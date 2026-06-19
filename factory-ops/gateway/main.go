// Command gateway is the FactoryOps ingestion service: it subscribes to the
// Digital Twin's NATS event stream and batch-writes it into ClickHouse.
package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nats-io/nats.go"

	"github.com/vinay/factory-ops/gateway/internal/config"
	"github.com/vinay/factory-ops/gateway/internal/ingest"
	"github.com/vinay/factory-ops/gateway/internal/sink"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg := config.Load()

	ctx, stop := signal.NotifyContext(context.Background(),
		syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// ClickHouse (retry: it may still be starting in docker-compose).
	ch, err := openSinkWithRetry(ctx, cfg, log)
	if err != nil {
		log.Error("clickhouse connect failed", "err", err)
		os.Exit(1)
	}
	defer ch.Close()
	log.Info("clickhouse ready", "addr", cfg.CHAddr)

	nc, err := nats.Connect(cfg.NATSURL,
		nats.RetryOnFailedConnect(true),
		nats.MaxReconnects(-1),
		nats.ReconnectWait(time.Second),
	)
	if err != nil {
		log.Error("nats connect failed", "err", err)
		os.Exit(1)
	}
	defer nc.Drain()
	log.Info("nats connected", "url", cfg.NATSURL)

	r := ingest.New(nc, ch, cfg.NATSSubjects, cfg.FlushInterval, log)
	if err := r.Run(ctx); err != nil {
		log.Error("runner error", "err", err)
		os.Exit(1)
	}
}

func openSinkWithRetry(ctx context.Context, cfg config.Config, log *slog.Logger) (*sink.ClickHouse, error) {
	var lastErr error
	for i := 0; i < 30; i++ {
		ch, err := sink.Open(ctx, cfg.CHAddr, cfg.CHDatabase, cfg.CHUser,
			cfg.CHPassword, cfg.BatchSize)
		if err == nil {
			return ch, nil
		}
		lastErr = err
		log.Warn("waiting for clickhouse", "attempt", i+1, "err", err)
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return nil, lastErr
}
