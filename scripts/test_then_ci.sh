#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: scripts/test_then_ci.sh <pytest args>"
  echo "example: scripts/test_then_ci.sh tests/test_evaluation_truth.py -q"
  exit 1
fi

echo "==> Running focused pytest command"
PYTHONPATH=src REDTHREAD_DRY_RUN=true .venv/bin/pytest "$@"

echo "==> Focused pytest passed. Running local PR CI mirror"
make ci-pr
