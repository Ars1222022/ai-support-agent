#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PYTHON="$ROOT/.venv/bin/python"
on_error() {
  status=$?
  echo "FAIL: lokal verifiering avbröts (felkod $status)." >&2
  if [[ -f .runtime/phoenix.log ]]; then
    echo "=== Senaste Phoenix-loggar ===" >&2
    tail -n 60 .runtime/phoenix.log >&2
  fi
  echo "Kontrollera även terminalen där ./run-lesson7.sh körs (Streamlit-loggar)." >&2
  exit "$status"
}
trap on_error ERR
if [[ ! -x "$PYTHON" ]]; then echo "Run ./setup-lesson7.sh first." >&2; exit 1; fi
"$PYTHON" smoke_test.py
for url in http://localhost:8501/_stcore/health http://localhost:6006; do
  curl --fail --silent --show-error --max-time 5 "$url" >/dev/null
  echo "PASS: $url"
done
echo "Local imports, RAG, Chroma, LangGraph, evals, app and Phoenix verified."
