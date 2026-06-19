#!/usr/bin/env bash
set -e

echo "[cleanup] Starting cleanup..."

if [ -d "/root/task" ]; then
  echo "[cleanup] Changing to /root/task"
  cd /root/task
fi

echo "[cleanup] Stopping Docker Compose services (with volumes and orphans)..."
docker compose down --remove-orphans --volumes || true

echo "[cleanup] Removing project-specific named volume(s)..."
docker volume rm delivery-tracking-ack-dlq-fix_rabbitmq-data || true
docker volume rm task_rabbitmq-data || true

echo "[cleanup] Pruning unused Docker resources..."
docker system prune -a --volumes -f || true

echo "[cleanup] Removing task directory /root/task..."
rm -rf /root/task || true

echo "Cleanup completed successfully!"
