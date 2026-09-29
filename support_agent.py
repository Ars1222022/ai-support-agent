"""RAG, model access, graph routing and classroom evaluations."""
from __future__ import annotations

import os
import json
from urllib.request import Request, urlopen
from pathlib import Path
from typing import TypedDict

import chromadb
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DOCS_PATH = ROOT / "data" / "support_docs.txt"
DB_PATH = ROOT / ".runtime" / "chroma"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None
try:
    _tracer_provider = register(project_name="lesson7-ai-support-agent", endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006") + "/v1/traces", protocol="http/protobuf")
    OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
except Exception:
    # The learning app still works when a student temporarily disables Phoenix.
    pass


def load_documents() -> list[str]:
    text = DOCS_PATH.read_text(encoding="utf-8")
    chunks = []
    for part in text.split("\n\n"):
        body = "\n".join(line for line in part.splitlines() if not line.lstrip().startswith("#")).strip()
        if body:
            chunks.append(body)
    return chunks


def _embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _collection():
    chroma_host = os.getenv("CHROMA_HOST")
    if chroma_host:
        client = chromadb.HttpClient(host=chroma_host, port=int(os.getenv("CHROMA_PORT", "8000")))
    else:
        DB_PATH.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(DB_PATH), settings=chromadb.Settings(anonymized_telemetry=False))
    return client, client.get_or_create_collection("support_docs", metadata={"hnsw:space": "cosine"})


def index_documents() -> int:
    chunks = load_documents()
    model = _embedding_model()
    client, _ = _collection()
    try:
        client.delete_collection("support_docs")
    except Exception:
        pass
    collection = client.get_or_create_collection("support_docs", metadata={"hnsw:space": "cosine"})
    collection.add(ids=[f"chunk_{i}" for i in range(len(chunks))], documents=chunks, embeddings=model.encode(chunks).tolist())
    return len(chunks)


def retrieve(query: str, n_results: int = 3) -> list[str]:
    client, collection = _collection()
    if collection.count() == 0:
        index_documents()
        _, collection = _collection()
    result = collection.query(query_embeddings=_embedding_model().encode([query]).tolist(), n_results=min(n_results, collection.count()))
    return result["documents"][0] if result.get("documents") else []


def _client(provider: str):
    key_name, base, model = {
        "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1", os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")),
        "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
    }[provider]
    key = os.getenv(key_name)
    if not key:
        raise RuntimeError(f"API-nyckel saknas. Lägg {key_name}=... i .env och starta om appen.")
    return OpenAI(api_key=key, base_url=base), model


def _generate(question: str, context: str, provider: str) -> str:
    client, model = _client(provider)
    response = client.chat.completions.create(model=model, temperature=0.3, messages=[
        {"role": "system", "content": "Du är en svensk supportagent. Svara kort och använd bara fakta från kontexten. Om svaret saknas, säg det tydligt.\n\n" + context},
        {"role": "user", "content": question},
    ])
    return response.choices[0].message.content or "Jag kunde inte skapa ett svar."


def answer(question: str, provider: str = "groq") -> dict:
    sources = retrieve(question)
    context = "\n\n".join(sources)
    try:
        response = _generate(question, context, provider)
    except Exception as exc:
        response = f"**Kunde inte nå språkmodellen:** {exc}\n\nHämtad information:\n\n{context}"
    return {"answer": response, "sources": sources}


class SupportState(TypedDict, total=False):
    query: str
    category: str
    needs_rag: bool
    context: str
    response: str
    research: str
    draft: str
    final: str


def build_simple_graph():
    """Three deterministic routes for the first LangGraph exercise."""
    def classify(state):
        q = state["query"].casefold()
        category = "retur" if any(w in q for w in ("retur", "byte", "ångerr")) else "frakt" if any(w in q for w in ("frakt", "leverans")) else "allmän"
        return {"category": category}
    def route(state): return state["category"]
    graph = StateGraph(SupportState)
    graph.add_node("classify", classify)
    graph.add_node("retur", lambda s: {"response": f"Returfråga: {s['query']}"})
    graph.add_node("frakt", lambda s: {"response": f"Fraktfråga: {s['query']}"})
    graph.add_node("allmän", lambda s: {"response": f"Allmän fråga: {s['query']}"})
    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route, {"retur": "retur", "frakt": "frakt", "allmän": "allmän"})
    for node in ("retur", "frakt", "allmän"): graph.add_edge(node, END)
    return graph.compile()


def build_graph(provider: str = "groq"):
    def classify(state):
        q = state["query"].casefold()
        category = "retur" if any(w in q for w in ("retur", "byte", "ångerr")) else "frakt" if any(w in q for w in ("frakt", "leverans")) else "allmän"
        return {"category": category, "needs_rag": not any(w in q for w in ("hej", "tack"))}
    def use_rag(state): return {"context": "\n\n".join(retrieve(state["query"], 2))}
    def respond(state): return {"response": _generate(state["query"], state.get("context", ""), provider)}
    def direct(state): return {"response": "Hej! Hur kan jag hjälpa dig?" if "hej" in state["query"].casefold() else "Tack själv!"}
    graph = StateGraph(SupportState)
    for name, fn in [("classify", classify), ("use_rag", use_rag), ("respond", respond), ("direct", direct)]: graph.add_node(name, fn)
    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", lambda s: "use_rag" if s["needs_rag"] else "direct", {"use_rag": "use_rag", "direct": "direct"})
    graph.add_edge("use_rag", "respond"); graph.add_edge("respond", END); graph.add_edge("direct", END)
    return graph.compile()


def run_role_pipeline(question: str, provider: str = "groq") -> str:
    """A small, genuinely executable researcher → writer → reviewer graph."""
    def researcher(state):
        return {"research": "\n\n".join(retrieve(state["query"], 2))}
    def writer(state):
        return {"draft": _generate(state["query"], state["research"], provider)}
    def reviewer(state):
        return {"final": _generate("Granska och förbättra detta utkast utan att lägga till fakta: " + state["draft"], state["research"], provider)}
    graph = StateGraph(SupportState)
    graph.add_node("researcher", researcher); graph.add_node("writer", writer); graph.add_node("reviewer", reviewer)
    graph.set_entry_point("researcher"); graph.add_edge("researcher", "writer"); graph.add_edge("writer", "reviewer"); graph.add_edge("reviewer", END)
    return graph.compile().invoke({"query": question})


def ask_ollama(prompt: str, model: str | None = None) -> str:
    """Optional local-model demo; Ollama is not needed by the main workshop."""
    url = os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/generate"
    body = json.dumps({"model": model or os.getenv("OLLAMA_MODEL", "qwen3:4b"), "prompt": prompt, "stream": False}).encode()
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode())["response"]


def evaluate() -> list[dict[str, str]]:
    cases = [("Hur lång är returrätten?", ["30", "dagar"], "retur"), ("Vad kostar expressfrakt?", ["198"], "expressfrakt"), ("Hur lång är garantin?", ["2", "år"], "garanti"), ("Vad kostar standardfrakt?", ["49"], "standardfrakt")]
    rows = []
    for question, expected, context_word in cases:
        docs = retrieve(question, 2)
        ctx = " ".join(docs).casefold()
        supported = context_word in ctx
        relevant = all(word.casefold() in ctx for word in expected)
        rows.append({"Fråga": question, "Kontextstöd": "OK" if supported else "SAKNAS", "Förväntad fakta": "OK" if relevant else "SAKNAS", "Resultat": "PASS" if supported and relevant else "FAIL"})
    return rows
