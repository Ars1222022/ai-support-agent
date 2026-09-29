#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "Python 3.12 is required. Install Python 3.12, then run this script again." >&2
  exit 1
fi
PYTHON="$(command -v python3.12)"
mkdir -p .runtime/huggingface .runtime/chroma .runtime/phoenix
export HF_HOME="$ROOT/.runtime/huggingface"
export PHOENIX_WORKING_DIR="$ROOT/.runtime/phoenix"
export PIP_NO_CACHE_DIR=1

if [[ ! -x .venv/bin/python ]]; then "$PYTHON" -m venv .venv; fi
VENV_PY="$ROOT/.venv/bin/python"
VENV_VERSION="$($VENV_PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$VENV_VERSION" != "3.12" ]]; then echo "Existing .venv uses Python $VENV_VERSION; move/remove only this project's .venv and rerun." >&2; exit 1; fi
"$VENV_PY" -m pip install --upgrade pip
case "$(uname -s)" in
  Darwin) "$VENV_PY" -m pip install --no-cache-dir "torch==2.10.0" ;;
  Linux)  "$VENV_PY" -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.10.0+cpu" ;;
  *) echo "Unsupported platform. Use Windows PowerShell or macOS/Linux." >&2; exit 1 ;;
esac
"$VENV_PY" -m pip install --no-cache-dir -r requirements-local.txt
"$VENV_PY" -c "import streamlit, openai, langgraph, chromadb, sentence_transformers, phoenix.otel; import openinference.instrumentation.openai; print('All lesson dependencies imported successfully')"

if [[ ! -f .env ]]; then cp .env.example .env; fi
echo "Ready. Virtualenv and model/database data are stored inside: $ROOT"
echo "Add an API key to .env for LLM answers. Start the local app with: ./run-lesson7.sh"
