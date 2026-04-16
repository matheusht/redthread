#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install uv first: https://docs.astral.sh/uv/"
  exit 1
fi

PYTHON_BIN=".venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3.13 || command -v python3 || command -v python)"
fi

echo "[redthread] installing editable global command with $PYTHON_BIN"
uv tool install -e . --force --python "$PYTHON_BIN"

echo "[redthread] command path: $(command -v redthread || echo 'not on PATH yet')"

echo "[redthread] bootstrapping local workspace"
redthread init || true

echo "[redthread] running doctor"
redthread doctor || true

echo "[redthread] done"
