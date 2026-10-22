import streamlit as st
import json
import subprocess
from pathlib import Path
 
# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------
 
st.set_page_config(
    page_title="Feenixdv Kubernetes Copilot",
    page_icon="🚀",
    layout="wide"
)
 
st.title("🚀 Feenixdv Kubernetes Copilot")
st.caption("Answers are grounded only in the local Kubernetes knowledge base.")
 
# --------------------------------------------------
# LOAD KNOWLEDGE BASE
# --------------------------------------------------
 
docs_folder = Path(__file__).parent.parent / "docs"
 
knowledge = []
markdown_files_loaded = 0
markdown_files_empty = []
 
# Load Markdown files from topic subfolders
for markdown_file in docs_folder.rglob("*.md"):
 
    try:
        content = markdown_file.read_text(encoding="utf-8").strip()
 
        if not content:
            markdown_files_empty.append(markdown_file.relative_to(docs_folder).as_posix())
            continue
 
        knowledge.append(
            {
                "source": markdown_file.relative_to(docs_folder).as_posix(),
                "content": content
            }
        )
        markdown_files_loaded += 1
 
    except OSError as e:
        st.warning(f"Could not read {markdown_file.name}: {e}")
 
st.caption(f"Loaded {markdown_files_loaded} non-empty Markdown documents from {docs_folder}.")
if markdown_files_empty:
    st.caption(f"Empty Markdown documents skipped: {', '.join(markdown_files_empty)}")
 
# Load JSONL
jsonl_file = docs_folder / "k8s_qa.jsonl"
 
if jsonl_file.exists():
 
    with open(jsonl_file, "r", encoding="utf-8") as f:
 
        for line in f:
 
            line = line.strip()
 
            if not line:
                continue
 
            try:
 
                item = json.loads(line)
 
                knowledge.append(
                    {
                        "source": "k8s_qa.jsonl",
                        "content":
                        f"""
Question:
{item.get("question","")}
 
Answer:
{item.get("answer","")}
"""
                    }
                )
 
            except Exception:
                continue
 
# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------
 
question = st.text_input(
    "Ask a question"
)
 
# --------------------------------------------------
# PROCESS QUESTION
# --------------------------------------------------
 
if question:
 
    matches = []
 
    for item in knowledge:
 
        score = 0
 
        content = item["content"].lower()
 
        for word in question.lower().split():
 
            word = word.strip()
 
            if len(word) < 3:
                continue
 
            if word in content:
                score += 1
 
        if score > 0:
 
            matches.append(
                (
                    score,
                    item["source"],
                    item["content"]
                )
            )
 
    matches.sort(
        key=lambda x: x[0],
        reverse=True
    )
 
    selected_matches = matches[:3]
    if not any(source.endswith(".md") for _, source, _ in selected_matches):
        best_markdown_match = next(
            (match for match in matches if match[1].endswith(".md")),
            None
        )
        if best_markdown_match:
            selected_matches = selected_matches[:2] + [best_markdown_match]
 
    if selected_matches:
        st.caption(
            "Context sources: "
            + ", ".join(source for _, source, _ in selected_matches)
        )
    else:
        st.warning(
            "No matching information was found in the local knowledge base. "
            "Add relevant documentation under docs/ and try again."
        )
        st.stop()

    context = "\n\n".join(
        f"Source: {source}\n{content}"
        for _, source, content in selected_matches
    )
 
    prompt = f"""
You are Feenixdv Kubernetes Copilot, a retrieval-augmented assistant.
Answer using only the supplied local context. Do not add facts from general
knowledge or other sources. If the context does not contain enough information
to answer the question, say that the local knowledge base does not contain the
requested information. Cite the source file names used in the answer.
 
Context:
{context}
 
User Question:
{question}
 
Provide a clear and accurate answer.
"""
 
    with st.spinner("Thinking..."):
 
        try:
 
            result = subprocess.run(
                [
                    "docker",
                    "model",
                    "run",
                    "smollm2",
                    prompt
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
 
            llm_answer = result.stdout.strip()
 
            st.subheader("🤖 Feenixdv Kubernetes Copilot")
 
            st.success(llm_answer)
 
        except Exception as e:
 
            st.error(
                f"Model Error: {str(e)}"
            )