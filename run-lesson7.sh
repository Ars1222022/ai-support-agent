#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
VENV_PY="$ROOT/.venv/bin/python"
PHOENIX="$ROOT/.venv/bin/phoenix"
if [[ ! -x "$VENV_PY" || ! -x "$PHOENIX" ]]; then
  echo "Local environment missing. Run ./setup-lesson7.sh first." >&2
  exit 1
fi
mkdir -p .runtime/huggingface .runtime/phoenix
export HF_HOME="$ROOT/.runtime/huggingface"
export PHOENIX_WORKING_DIR="$ROOT/.runtime/phoenix"
export PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"
"$PHOENIX" serve --host 127.0.0.1 --port 6006 >.runtime/phoenix.log 2>&1 &
PHOENIX_PID=$!
cleanup() { kill "$PHOENIX_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

ready=0
for ((i = 0; i < 30; i++)); do
  if ! kill -0 "$PHOENIX_PID" 2>/dev/null; then
    echo "Phoenix stopped. See .runtime/phoenix.log" >&2
    exit 1
  fi
  if "$VENV_PY" -c "import urllib.request; urllib.request.urlopen('http://localhost:6006', timeout=2)" >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
if [[ "$ready" -ne 1 ]]; then echo "Phoenix did not start on port 6006. See .runtime/phoenix.log" >&2; exit 1; fi
echo "Phoenix: http://localhost:6006 | App: http://localhost:8501"
"$VENV_PY" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
