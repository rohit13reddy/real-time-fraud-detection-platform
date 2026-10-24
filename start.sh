#!/bin/bash

set -u

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

VENV="$ROOT_DIR/ml-service/.venv"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$RUN_DIR" "$LOG_DIR"

echo "========================================"
echo "  Real-Time Fraud Detection Platform"
echo "========================================"

# Avoid accidentally starting duplicate processes.
if [ -f "$RUN_DIR/started" ]; then
    echo "A previous session marker exists."
    echo "Run ./stop.sh first, then try again."
    exit 1
fi

# Start infrastructure.
echo ""
echo "[1/6] Starting Kafka and PostgreSQL..."
if ! docker compose up -d; then
    echo "Docker Compose failed. Check Docker Desktop."
    exit 1
fi

# Start one background process and save its PID and logs.
start_bg() {
    name="$1"
    shift

    echo "Starting $name..."
    "$@" > "$LOG_DIR/$name.log" 2>&1 &
    echo $! > "$RUN_DIR/$name.pid"
}

# Wait for an HTTP endpoint to become available.
wait_for_url() {
    name="$1"
    url="$2"

    for attempt in $(seq 1 30); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "$name is ready."
            return 0
        fi
        sleep 2
    done

    echo "ERROR: $name did not become ready."
    echo "Recent logs:"
    tail -n 30 "$LOG_DIR/$name.log" 2>/dev/null || true
    return 1
}

echo ""
echo "[2/6] Starting ML prediction API..."
start_bg ml-api "$VENV/bin/uvicorn" app:app \
    --app-dir "$ROOT_DIR/ml-service/src" \
    --host 127.0.0.1 --port 8000

if ! wait_for_url "ML API" "http://127.0.0.1:8000/health"; then
    exit 1
fi

echo ""
echo "[3/6] Starting Dashboard API..."
start_bg dashboard-api "$VENV/bin/uvicorn" dashboard_api:app \
    --app-dir "$ROOT_DIR/ml-service/src" \
    --host 127.0.0.1 --port 8001

if ! wait_for_url "Dashboard API" "http://127.0.0.1:8001/health"; then
    exit 1
fi

echo ""
echo "[4/6] Starting Kafka consumer..."
start_bg live-consumer "$VENV/bin/python" \
    "$ROOT_DIR/ml-service/src/live_consumer.py"

sleep 2

if ! kill -0 "$(cat "$RUN_DIR/live-consumer.pid")" 2>/dev/null; then
    echo "ERROR: Kafka consumer exited. Check logs/live-consumer.log"
    exit 1
fi

echo ""
echo "[5/6] Starting React dashboard..."
start_bg frontend bash -c 'cd "$1" && npm run dev -- --host 127.0.0.1' _ "$ROOT_DIR/dashboard"

if ! wait_for_url "React dashboard" "http://127.0.0.1:5173/"; then
    exit 1
fi

echo ""
echo "[6/6] Starting live transaction generator..."
start_bg live-producer "$VENV/bin/python" \
    "$ROOT_DIR/ml-service/src/live_producer.py"

sleep 2

if ! kill -0 "$(cat "$RUN_DIR/live-producer.pid")" 2>/dev/null; then
    echo "ERROR: Producer exited. Check logs/live-producer.log"
    exit 1
fi

touch "$RUN_DIR/started"

echo ""
echo "========================================"
echo "  Fraud Detection Platform is running!"
echo "========================================"
echo ""
echo "Dashboard:    http://localhost:5173/"
echo "ML API docs:  http://127.0.0.1:8000/docs"
echo "Dashboard API: http://127.0.0.1:8001/docs"
echo ""
echo "Logs:         $LOG_DIR/"
echo "Stop:         ./stop.sh"
echo ""
