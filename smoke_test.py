"""Offline check of document loading, embeddings, Chroma, evals and LangGraph."""
from support_agent import build_simple_graph, evaluate, index_documents, load_documents, retrieve

documents = load_documents()
assert len(documents) == 7, f"Expected 7 source sections, got {len(documents)}"
print("PASS: loaded 7 support document sections")

count = index_documents()
assert count == 7, f"Expected to index 7 sections, got {count}"
print("PASS: indexed documents")

sources = retrieve("Vad kostar expressfrakt?", n_results=2)
assert sources and any("expressfrakt" in source.casefold() and "198" in source for source in sources), "Relevant shipping source not retrieved"
print("PASS: Swedish RAG retrieval found the shipping price")

graph_result = build_simple_graph().invoke({"query": "Vad kostar expressfrakt?"})
assert graph_result["category"] == "frakt", f"Unexpected graph route: {graph_result['category']}"
print("PASS: LangGraph routed the question to frakt")

rows = evaluate()
failed = [row["Fråga"] for row in rows if row["Resultat"] != "PASS"]
assert not failed, f"Offline eval failures: {failed}"
print(f"PASS: offline evaluations ({len(rows)}/{len(rows)})")
