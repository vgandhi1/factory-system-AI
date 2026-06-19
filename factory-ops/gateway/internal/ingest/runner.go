// Package ingest wires NATS subscriptions to the ClickHouse sink: decode each
// message, buffer it, and flush on batch-size or a time interval.
package ingest

import (
	"context"
	"log/slog"
	"sync/atomic"
	"time"

	"github.com/nats-io/nats.go"

	"github.com/vinay/factory-ops/gateway/internal/model"
	"github.com/vinay/factory-ops/gateway/internal/sink"
)

type Runner struct {
	nc            *nats.Conn
	sink          *sink.ClickHouse
	subjects      []string
	flushInterval time.Duration
	log           *slog.Logger

	received atomic.Uint64
	dropped  atomic.Uint64
}

func New(nc *nats.Conn, s *sink.ClickHouse, subjects []string,
	flushInterval time.Duration, log *slog.Logger) *Runner {
	return &Runner{nc: nc, sink: s, subjects: subjects,
		flushInterval: flushInterval, log: log}
}

// Run subscribes and blocks until ctx is cancelled, then drains a final flush.
func (r *Runner) Run(ctx context.Context) error {
	flush := func() {
		fctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := r.sink.Flush(fctx); err != nil {
			r.log.Error("flush failed", "err", err)
		}
	}

	handler := func(m *nats.Msg) {
		d, err := model.Decode(m.Data)
		if err != nil {
			r.dropped.Add(1)
			r.log.Warn("decode failed", "subject", m.Subject, "err", err)
			return
		}
		r.received.Add(1)
		if r.sink.Add(d) {
			flush()
		}
	}

	subs := make([]*nats.Subscription, 0, len(r.subjects))
	for _, subj := range r.subjects {
		s, err := r.nc.Subscribe(subj, handler)
		if err != nil {
			return err
		}
		subs = append(subs, s)
		r.log.Info("subscribed", "subject", subj)
	}

	ticker := time.NewTicker(r.flushInterval)
	defer ticker.Stop()
	logTicker := time.NewTicker(5 * time.Second)
	defer logTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			for _, s := range subs {
				_ = s.Unsubscribe()
			}
			flush() // drain remaining buffered rows
			r.log.Info("shutdown", "received", r.received.Load(),
				"dropped", r.dropped.Load())
			return nil
		case <-ticker.C:
			flush()
		case <-logTicker.C:
			r.log.Info("ingest stats", "received", r.received.Load(),
				"dropped", r.dropped.Load())
		}
	}
}
