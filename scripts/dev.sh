#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose up -d
(cd backend && python -m uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
