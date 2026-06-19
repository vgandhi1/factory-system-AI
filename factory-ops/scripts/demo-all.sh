#!/usr/bin/env bash
#
# demo-all.sh — bring up the full Factory Systems AI portfolio in one command.
#
# Starts both Docker Compose stacks (they are now port-safe and can run together):
#   * FactoryOps  : Digital Twin -> NATS -> Go gateway -> ClickHouse -> FastAPI -> Next.js
#   * VisionGuard : inference-server (YOLOv8 + EigenCAM) -> webui, Postgres, MinIO
#
# Port map (no collisions):
#   FactoryOps  frontend 3000 · API 8010 · ClickHouse 8123/9000 · NATS 4222 · Postgres 5432
#   VisionGuard webui    3001 · API 8001 · MinIO 9100/9101 · Postgres 5433
#
# Usage:
#   scripts/demo-all.sh up        # build + start both stacks (default)
#   scripts/demo-all.sh down      # stop both stacks
#   scripts/demo-all.sh seed-vg   # populate VisionGuard MinIO with Twin defect images
#
set -euo pipefail

# Script lives in factory-ops/scripts/; the three repos are siblings under ROOT.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPS="$ROOT/factory-ops"
VG="$ROOT/visionguard"

# Resolve the compose command (plugin `docker compose` or legacy `docker-compose`).
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "ERROR: Docker Compose not found. Install Docker Desktop or the compose plugin." >&2
  exit 1
fi

cmd="${1:-up}"

case "$cmd" in
  up)
    echo ">> Starting FactoryOps (Twin + gateway + ClickHouse + API + UI)…"
    ( cd "$OPS" && $DC up -d --build )

    echo ">> Starting VisionGuard (inference + webui + Postgres + MinIO)…"
    ( cd "$VG" && $DC up -d --build )

    cat <<'EOF'

================ Factory Systems AI — running ================
FactoryOps
  Dashboard   http://localhost:3000
  API docs    http://localhost:8010/docs
VisionGuard
  Web UI      http://localhost:3001
  API docs    http://localhost:8001/docs
  MinIO       http://localhost:9101   (minioadmin / minioadmin)

Demo path:
  1. Open the FactoryOps dashboard — OEE / downtime / bottleneck from Twin data.
  2. Ask the Copilot (chat page): "Why is line-1 OEE low?"  (set ANTHROPIC_API_KEY
     for the real Claude answer; otherwise the deterministic fallback responds).
  3. Seed VisionGuard images:  scripts/demo-all.sh seed-vg
  4. Open the VisionGuard Web UI, run a detection, correct a label.
  5. (Optional) retrain:  cd visionguard && docker compose --profile retrain up retrainer

Stop everything:  scripts/demo-all.sh down
=============================================================
EOF
    ;;

  down)
    echo ">> Stopping VisionGuard…"
    ( cd "$VG" && $DC down )
    echo ">> Stopping FactoryOps…"
    ( cd "$OPS" && $DC down )
    ;;

  seed-vg)
    # Populate VisionGuard's MinIO (host port 9100) with the Twin's labeled defect
    # images so the inference server has real data to score. Requires the Twin's
    # Python deps; run inside its venv if present.
    echo ">> Generating Twin defect images into VisionGuard MinIO (localhost:9100)…"
    ( cd "$ROOT/factory-digital-twin" && \
      python synthetic-images/defect_generator.py \
        --minio localhost:9100 --minio-access minioadmin --minio-secret minioadmin )
    echo ">> Done. Refs are minio://defects/<part_id>.png — score via POST /detect/ref."
    ;;

  *)
    echo "Usage: $0 {up|down|seed-vg}" >&2
    exit 1
    ;;
esac
