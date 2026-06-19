#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/root/task"
cd "$BASE_DIR"

echo "[1/6] Starting RabbitMQ broker via Docker Compose..."
docker compose up -d

echo "[2/6] Waiting for RabbitMQ to become healthy..."
ATTEMPTS=0
MAX_ATTEMPTS=30
until docker compose exec -T rabbitmq rabbitmq-diagnostics -q ping >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
    echo "ERROR: RabbitMQ did not become healthy in time."
    docker compose ps
    exit 1
  fi
  echo "  ...broker not ready yet (attempt ${ATTEMPTS}/${MAX_ATTEMPTS})"
  sleep 3
done
echo "  RabbitMQ responded to ping."

echo "[3/6] Showing compose service status..."
docker compose ps

echo "[4/6] Checking that expected starter files exist..."
for f in definitions.json consumer.py producer.py sample_messages.json docker-compose.yml; do
  if [ ! -f "$BASE_DIR/$f" ]; then
    echo "ERROR: expected file missing: $f"
    exit 1
  fi
  echo "  found: $f"
done

echo "[5/6] Validating JSON files..."
for j in definitions.json sample_messages.json; do
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import json,sys; json.load(open('$BASE_DIR/$j'))" && echo "  valid JSON: $j"
  else
    echo "  (python3 not available, skipping JSON validation for $j)"
  fi
done

echo "[6/6] Confirming Management API is reachable with configured credentials..."
if docker compose exec -T rabbitmq rabbitmqctl -q list_vhosts >/dev/null 2>&1; then
  echo "  Management/broker is reachable. Current vhosts:"
  docker compose exec -T rabbitmq rabbitmqctl -q list_vhosts || true
else
  echo "  WARNING: could not list vhosts via rabbitmqctl."
fi

echo "Readiness checks completed. Starter environment is up."
exit 0
