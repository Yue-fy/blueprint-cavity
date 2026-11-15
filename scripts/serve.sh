#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec nice -n 15 .venv/bin/python -m uvicorn blueprint_gym.server:app --host 127.0.0.1 --port "${PORT:-8430}" --workers 1
