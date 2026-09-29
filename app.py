"""Beginner-friendly Swedish support agent, powered by RAG and LangGraph."""
from __future__ import annotations

import streamlit as st

from support_agent import answer, ask_ollama, build_graph, build_simple_graph, evaluate, index_documents, load_documents

st.set_page_config(page_title="AI Support Agent · Lektion 7", page_icon="💬", layout="wide")
st.title("AI Support Agent")
st.caption("Lektion 7 · RAG · LangGraph · Evals · Phoenix")

with st.sidebar:
    st.header("Kom igång")
    st.markdown("1. Välj Groq eller OpenAI i **Inställningar**.\n2. Lägg API-nyckeln i `.env`.\n3. Fråga agenten eller kör en kursövning.")
    provider = st.selectbox("AI-leverantör", ["groq", "openai"], format_func=lambda x: "Groq" if x == "groq" else "OpenAI")
    if st.button("Bygg om kunskapsbas", use_container_width=True):
        with st.spinner("Läser in svenska dokument och bygger index …"):
            count = index_documents()
        st.success(f"Klart! {count} textavsnitt indexerades.")
    st.caption("Första indexeringen hämtar en flerspråkig embedding-modell.")

chat_tab, lessons_tab, about_tab = st.tabs(["💬 Chatta", "🧭 Kurssteg", "ℹ️ Om projektet"])
with chat_tab:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Visa källor"):
                    st.write("\n\n".join(msg["sources"]))
    prompt = st.chat_input("Fråga om retur, frakt, garanti …")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Agenten söker i kunskapsbasen …"):
                result = answer(prompt, provider)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Visa källor"):
                    st.write("\n\n".join(result["sources"]))
        st.session_state.messages.append({"role": "assistant", **result})

with lessons_tab:
    st.subheader("Lär dig genom att prova")
    lesson = st.selectbox("Välj kurssteg", ["1 · RAG och retrieval", "2 · RAG-agent", "3 · Enkel LangGraph", "4 · LangGraph med RAG", "5 · Rollbaserad pipeline", "6–7 · Evals", "8 · Phoenix tracing", "9 · Ollama (bonus)"])
    if lesson.startswith("1"):
        st.write("Dokument delas upp i avsnitt, görs om till embeddings och sparas i Chroma. Prova en fråga i chatten och öppna källorna.")
        if st.button("Visa dokumentavsnitt"):
            for i, chunk in enumerate(load_documents(), 1):
                st.markdown(f"**Avsnitt {i}**\n\n{chunk}")
    elif lesson.startswith("2"):
        st.write("RAG hämtar relevanta textavsnitt. LLM formulerar sedan ett svar med enbart den hämtade kontexten.")
    elif lesson.startswith("3"):
        st.write("LangGraph dirigerar frågan till en retur-, frakt- eller allmän nod. Kör en fråga för att se flödet.")
        q = st.text_input("Testfråga", "Hur returnerar jag en vara?", key="graphq")
        if st.button("Kör graf"):
            st.json(build_simple_graph().invoke({"query": q}))
    elif lesson.startswith("4"):
        st.write("Grafen väljer en direkt hälsning eller hämtar kunskap med RAG innan svaret skapas.")
        q = st.text_input("Fråga grafen", "Vad kostar expressfrakt?", key="rag_graph_q")
        if st.button("Kör LangGraph med RAG"):
            with st.spinner("Grafen arbetar …"):
                result = build_graph(provider).invoke({"query": q})
            st.write(result["response"])
            st.caption(f"Kategori: {result['category']} · RAG: {'ja' if result['needs_rag'] else 'nej'}")
    elif lesson.startswith("5"):
        st.write("Researcher hämtar fakta → Writer skriver ett utkast → Reviewer granskar svaret. Det är en pedagogisk sekventiell pipeline.")
        from support_agent import run_role_pipeline
        q = st.text_input("Fråga till pipeline", "Hur returnerar jag en vara?", key="pipeline_q")
        if st.button("Kör researcher → writer → reviewer"):
            with st.spinner("Tre roller arbetar i följd …"):
                try:
                    result = run_role_pipeline(q, provider)
                    st.success(result["final"])
                    with st.expander("Visa mellanresultat"):
                        st.write("**Research:**", result["research"])
                        st.write("**Utkast:**", result["draft"])
                except Exception as exc:
                    st.error(str(exc))
    elif lesson.startswith("6"):
        st.write("Evals testar om svaret är relevant och om den hämtade kontexten stöder det.")
        if st.button("Kör offline-evals"):
            rows = evaluate()
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.success(f"{sum(r['Resultat'] == 'PASS' for r in rows)}/{len(rows)} godkända")
    elif lesson.startswith("8"):
        st.write("Phoenix tar emot traces på port 6006. Öppna Phoenix-knappen när containern startats.")
        st.link_button("Öppna Phoenix", "http://localhost:6006")
    else:
        st.write("Frivillig lokal modell. Den kräver extra disk/RAM och startas inte med standarduppsättningen.")
        st.code("docker compose --profile ollama up -d ollama\ndocker compose exec ollama ollama pull qwen3:4b")
        q = st.text_input("Fråga Ollama", "Förklara vad en AI-agent är på en mening.", key="ollama_q")
        if st.button("Fråga lokal modell"):
            with st.spinner("Ollama svarar …"):
                try: st.write(ask_ollama(q))
                except Exception as exc: st.error(f"Ollama är inte tillgänglig. Starta bonusprofilen först. Detalj: {exc}")

with about_tab:
    st.markdown("""
**Teknik:** Python 3.12 · Streamlit · ChromaDB · Sentence Transformers · LangGraph · OpenAI/Groq · Arize Phoenix.

All applikationsberoenden körs i Docker. Studenter behöver Docker Desktop (Windows/macOS) eller Docker Engine + Compose (Linux); VS Code är valfritt.

**Demo-data:** supportreglerna i `data/support_docs.txt` är exempel och kan redigeras.
""")
