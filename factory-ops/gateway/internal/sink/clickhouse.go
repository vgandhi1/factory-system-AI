// Package sink persists decoded events to ClickHouse. It buffers rows per table
// and flushes on size or interval, using clickhouse-go batch inserts.
package sink

import (
	"context"
	_ "embed"
	"fmt"
	"strings"
	"sync"

	"github.com/ClickHouse/clickhouse-go/v2"
	"github.com/ClickHouse/clickhouse-go/v2/lib/driver"

	"github.com/vinay/factory-ops/gateway/internal/model"
)

//go:embed schema.sql
var schemaSQL string

// dbToken is the placeholder in schema.sql replaced with the configured database
// name at startup, so CLICKHOUSE_DB actually drives where tables live.
const dbToken = "__DB__"

type ClickHouse struct {
	conn      driver.Conn
	db        string
	batchSize int

	mu   sync.Mutex
	prod []model.ProductionRow
	down []model.DowntimeRow
	qual []model.QualityRow
}

func Open(ctx context.Context, addr, db, user, pass string, batchSize int) (*ClickHouse, error) {
	// Bootstrap on the always-present "default" database: the embedded schema
	// runs CREATE DATABASE IF NOT EXISTS for the configured db, so we can't make
	// it the session default before it exists. All DDL/inserts are fully
	// qualified with db, so the session default is irrelevant after bootstrap.
	conn, err := clickhouse.Open(&clickhouse.Options{
		Addr: []string{addr},
		Auth: clickhouse.Auth{Database: "default", Username: user, Password: pass},
	})
	if err != nil {
		return nil, err
	}
	if err := conn.Ping(ctx); err != nil {
		return nil, fmt.Errorf("clickhouse ping: %w", err)
	}
	ch := &ClickHouse{conn: conn, db: db, batchSize: batchSize}
	if err := ch.ensureSchema(ctx); err != nil {
		return nil, err
	}
	return ch, nil
}

// ensureSchema applies the embedded DDL statement-by-statement (idempotent).
// Comment lines are stripped first so a ';' inside a '--' comment can't be
// mistaken for a statement terminator. The db placeholder is substituted last.
func (c *ClickHouse) ensureSchema(ctx context.Context) error {
	var code strings.Builder
	for _, line := range strings.Split(schemaSQL, "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), "--") {
			continue
		}
		code.WriteString(line)
		code.WriteByte('\n')
	}
	ddl := strings.ReplaceAll(code.String(), dbToken, c.db)
	for _, stmt := range strings.Split(ddl, ";") {
		s := strings.TrimSpace(stmt)
		if s == "" {
			continue
		}
		if err := c.conn.Exec(ctx, s); err != nil {
			return fmt.Errorf("schema stmt failed: %w\n%s", err, s)
		}
	}
	return nil
}

// Add buffers a decoded row. Returns true if the buffer reached batchSize and
// the caller should Flush.
func (c *ClickHouse) Add(d model.Decoded) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	switch {
	case d.Production != nil:
		c.prod = append(c.prod, *d.Production)
	case d.Downtime != nil:
		c.down = append(c.down, *d.Downtime)
	case d.Quality != nil:
		c.qual = append(c.qual, *d.Quality)
	}
	return len(c.prod)+len(c.down)+len(c.qual) >= c.batchSize
}

// Flush sends all buffered rows. Safe to call on an empty buffer.
func (c *ClickHouse) Flush(ctx context.Context) error {
	c.mu.Lock()
	prod, down, qual := c.prod, c.down, c.qual
	c.prod, c.down, c.qual = nil, nil, nil
	c.mu.Unlock()

	if err := c.flushProduction(ctx, prod); err != nil {
		return err
	}
	if err := c.flushDowntime(ctx, down); err != nil {
		return err
	}
	return c.flushQuality(ctx, qual)
}

func (c *ClickHouse) flushProduction(ctx context.Context, rows []model.ProductionRow) error {
	if len(rows) == 0 {
		return nil
	}
	b, err := c.conn.PrepareBatch(ctx, fmt.Sprintf(`INSERT INTO %s.production
		(ts, event_id, event_type, line_id, station_id, order_id, product_sku,
		 target_qty, good_qty, scrap_qty, ideal_cycle_time_s, actual_cycle_time_s)`, c.db))
	if err != nil {
		return err
	}
	for _, r := range rows {
		if err := b.Append(r.TS, r.EventID, r.EventType, r.LineID, r.StationID,
			r.OrderID, r.ProductSKU, r.TargetQty, r.GoodQty, r.ScrapQty,
			r.IdealCycleTimeS, r.ActualCycleTimeS); err != nil {
			return err
		}
	}
	return b.Send()
}

func (c *ClickHouse) flushDowntime(ctx context.Context, rows []model.DowntimeRow) error {
	if len(rows) == 0 {
		return nil
	}
	b, err := c.conn.PrepareBatch(ctx, fmt.Sprintf(`INSERT INTO %s.downtime
		(ts, event_id, event_type, line_id, station_id, downtime_id, category,
		 planned, reason, duration_s)`, c.db))
	if err != nil {
		return err
	}
	for _, r := range rows {
		if err := b.Append(r.TS, r.EventID, r.EventType, r.LineID, r.StationID,
			r.DowntimeID, r.Category, r.Planned, r.Reason, r.DurationS); err != nil {
			return err
		}
	}
	return b.Send()
}

func (c *ClickHouse) flushQuality(ctx context.Context, rows []model.QualityRow) error {
	if len(rows) == 0 {
		return nil
	}
	b, err := c.conn.PrepareBatch(ctx, fmt.Sprintf(`INSERT INTO %s.quality
		(ts, event_id, line_id, station_id, part_id, result, defect_type,
		 confidence, image_ref, equipment_state)`, c.db))
	if err != nil {
		return err
	}
	for _, r := range rows {
		if err := b.Append(r.TS, r.EventID, r.LineID, r.StationID, r.PartID,
			r.Result, r.DefectType, r.Confidence, r.ImageRef,
			r.EquipmentState); err != nil {
			return err
		}
	}
	return b.Send()
}

func (c *ClickHouse) Close() error { return c.conn.Close() }
