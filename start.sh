#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
  for pid in $(jobs -p); do
    kill "$pid" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT INT TERM

echo "Starting MLB Show Dashboard..."

echo "Launching backend..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &

sleep 2

echo "Launching frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &

echo "Backend running at http://127.0.0.1:8000"
echo "Dashboard running at http://localhost:3000/dashboard"

echo "Press Ctrl+C to stop both services."
wait
