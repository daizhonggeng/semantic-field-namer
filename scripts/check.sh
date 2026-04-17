#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m compileall backend/app backend/tests
(cd backend && python -m pytest -q)
(cd frontend && npm run build)
