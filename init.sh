#!/bin/bash

set -e

# Start all services
echo "Starting containers..."
docker-compose up -d

REQUIRED_CONTAINERS=("kafka" "postgres" "flink-jobmanager" "flink-taskmanager" "data-generator")

# Max retry attempts
MAX_RETRIES=10
RETRY_INTERVAL=5

echo "Verifying container status..."
for (( i=1; i<=MAX_RETRIES; i++ )); do
    ALL_UP=true

    for CONTAINER in "${REQUIRED_CONTAINERS[@]}"; do
        STATUS=$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo "false")
        if [[ "$STATUS" != "true" ]]; then
            echo "$CONTAINER is not running yet."
            ALL_UP=false
        else
            echo "$CONTAINER is up."
        fi
    done

    if [[ "$ALL_UP" == true ]]; then
        echo "All required containers are running."
        break
    fi

    if [[ $i -lt $MAX_RETRIES ]]; then
        echo "Retrying in ${RETRY_INTERVAL}s... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    else
        echo "Containers not all running, re-running docker-compose..."
        docker-compose up -d
        i=1  # restart loop
    fi
done

# Submit Flink job
echo "Submitting Flink job..."
sleep 20
docker exec -it flink-jobmanager flink run -py /opt/flink/ad_metrics_job.py

echo "Flink job submitted."
