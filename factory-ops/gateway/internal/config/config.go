// Package config loads gateway settings from the environment.
package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	NATSURL       string        // e.g. nats://localhost:4222
	NATSSubjects  []string      // subjects to subscribe
	CHAddr        string        // ClickHouse host:port (native protocol)
	CHDatabase    string        // ClickHouse database
	CHUser        string        // ClickHouse user
	CHPassword    string        // ClickHouse password
	BatchSize     int           // flush when buffer reaches this many rows
	FlushInterval time.Duration // flush at least this often
}

func Load() Config {
	return Config{
		NATSURL: env("NATS_URL", "nats://localhost:4222"),
		NATSSubjects: []string{
			"factory.production",
			"factory.downtime",
			"factory.quality",
		},
		CHAddr:        env("CLICKHOUSE_ADDR", "localhost:9000"),
		CHDatabase:    env("CLICKHOUSE_DB", "factory"),
		CHUser:        env("CLICKHOUSE_USER", "default"),
		CHPassword:    env("CLICKHOUSE_PASSWORD", ""),
		BatchSize:     envInt("GATEWAY_BATCH_SIZE", 500),
		FlushInterval: time.Duration(envInt("GATEWAY_FLUSH_MS", 1000)) * time.Millisecond,
	}
}

func env(k, def string) string {
	if v, ok := os.LookupEnv(k); ok && v != "" {
		return v
	}
	return def
}

func envInt(k string, def int) int {
	if v, ok := os.LookupEnv(k); ok {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}
