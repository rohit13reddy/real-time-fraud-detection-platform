#!/bin/bash

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"

echo "Stopping Fraud Detection Platform..."

for name in live-producer live-consumer frontend dashboard-api ml-api; do
    pid_file="$RUN_DIR/$name.pid"

    if [ -f "$pid_file" ]; then
        pid="$(cat "$pid_file")"

        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $name..."
            kill "$pid" 2>/dev/null || true
        fi

        rm -f "$pid_file"
    fi
done

sleep 1
rm -f "$RUN_DIR/started"

echo "Application processes stopped."
echo "Kafka and PostgreSQL containers are still running."
echo "To stop those containers too, run: docker compose stop"
