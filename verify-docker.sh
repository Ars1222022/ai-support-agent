#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
failed=0

echo "=== Compose configuration ==="
docker compose config --quiet || failed=1
echo "=== Service status ==="
docker compose ps || failed=1
echo "=== Imports inside app container ==="
docker compose exec -T lesson7 python -c "import streamlit, openai, langgraph, chromadb, sentence_transformers, phoenix.otel; import openinference.instrumentation.openai; print('PASS: Python dependencies')" || failed=1
if [[ "$failed" -eq 0 ]]; then
  echo "=== RAG, Chroma, LangGraph and offline eval ==="
  docker compose exec -T lesson7 python smoke_test.py || failed=1
fi
echo "=== Service HTTP checks ==="
for url in http://localhost:8501/_stcore/health http://localhost:8000/api/v2/heartbeat http://localhost:6006; do
  if curl --fail --silent --show-error --max-time 5 "$url" >/dev/null; then echo "PASS: $url"; else echo "FAIL: $url"; failed=1; fi
done

if [[ "$failed" -ne 0 ]]; then
  echo "=== Recent logs ==="
  docker compose logs --tail 40 lesson7 chroma phoenix || true
  exit 1
fi
echo "All local container checks passed. LLM answers require a valid API key."
