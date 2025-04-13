#!/bin/bash
set -e

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL..."
while ! (echo > /dev/tcp/postgres/5432) >/dev/null 2>&1; do
  echo "PostgreSQL not ready yet. Waiting..."
  sleep 1
done

echo "PostgreSQL is up - setting up Superset..."

# Setup Superset
superset db upgrade

superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@superset.com \
  --password admin || true  # Don't fail if user exists

superset init

# Start Superset
superset run -h 0.0.0.0 -p 8088
