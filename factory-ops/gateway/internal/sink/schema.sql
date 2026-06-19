-- FactoryOps analytics schema. Mirrors the Digital Twin event contract.
-- One table per event family; event_type distinguishes started/completed etc.
-- MergeTree ordered by (line_id, ts) for fast per-line time-range scans (OEE).
-- __DB__ is substituted with the configured database name (CLICKHOUSE_DB) by the
-- gateway at startup; defaults to "factory".

CREATE DATABASE IF NOT EXISTS __DB__;

CREATE TABLE IF NOT EXISTS __DB__.production
(
    ts                   DateTime64(3, 'UTC'),
    event_id             String,
    event_type           LowCardinality(String),
    line_id              LowCardinality(String),
    station_id           LowCardinality(String),
    order_id             String,
    product_sku          LowCardinality(String) DEFAULT '',
    target_qty           UInt32  DEFAULT 0,
    good_qty             UInt32  DEFAULT 0,
    scrap_qty            UInt32  DEFAULT 0,
    ideal_cycle_time_s   Float64 DEFAULT 0,
    actual_cycle_time_s  Float64 DEFAULT 0
)
ENGINE = MergeTree
ORDER BY (line_id, ts);

CREATE TABLE IF NOT EXISTS __DB__.downtime
(
    ts           DateTime64(3, 'UTC'),
    event_id     String,
    event_type   LowCardinality(String),
    line_id      LowCardinality(String),
    station_id   LowCardinality(String),
    downtime_id  String,
    category     LowCardinality(String) DEFAULT '',
    planned      UInt8   DEFAULT 0,
    reason       String  DEFAULT '',
    duration_s   Float64 DEFAULT 0
)
ENGINE = MergeTree
ORDER BY (line_id, ts);

CREATE TABLE IF NOT EXISTS __DB__.quality
(
    ts               DateTime64(3, 'UTC'),
    event_id         String,
    line_id          LowCardinality(String),
    station_id       LowCardinality(String),
    part_id          String,
    result           LowCardinality(String),
    defect_type      LowCardinality(String) DEFAULT 'none',
    confidence       Float64 DEFAULT 1,
    image_ref        String  DEFAULT '',
    equipment_state  LowCardinality(String) DEFAULT 'nominal'
)
ENGINE = MergeTree
ORDER BY (line_id, ts);

-- Convenience view: per-line OEE over all loaded data. The API layer will
-- parameterize the time window; this proves the schema supports the calc and
-- should match the Twin's ground-truth oee_calculator within tolerance.
CREATE VIEW IF NOT EXISTS __DB__.oee AS
WITH
    prod AS (
        SELECT line_id,
               sum(good_qty)  AS good,
               sum(good_qty + scrap_qty) AS total,
               avg(ideal_cycle_time_s)   AS ideal_cycle
        FROM __DB__.production
        WHERE event_type = 'production_completed'
        GROUP BY line_id
    ),
    down AS (
        SELECT line_id, sum(duration_s) AS downtime_s
        FROM __DB__.downtime
        WHERE event_type = 'downtime_ended'
        GROUP BY line_id
    ),
    -- planned production time = span between first and last event per line
    span AS (
        SELECT line_id,
               dateDiff('second', min(ts), max(ts)) AS planned_s
        FROM __DB__.production
        GROUP BY line_id
    )
SELECT
    p.line_id AS line_id,
    least(1.0, (s.planned_s - ifNull(d.downtime_s, 0)) / s.planned_s) AS availability,
    least(1.0, (p.ideal_cycle * p.total) /
          nullIf(s.planned_s - ifNull(d.downtime_s, 0), 0))           AS performance,
    p.good / nullIf(p.total, 0)                                        AS quality,
    availability * performance * quality                              AS oee
FROM prod p
LEFT JOIN down d ON p.line_id = d.line_id
LEFT JOIN span s ON p.line_id = s.line_id
ORDER BY line_id;
