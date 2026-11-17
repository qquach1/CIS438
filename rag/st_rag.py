from simonbb.cis438.rag import MultiQueryRerankRetriever, build_rag

from dotenv import load_dotenv
load_dotenv( override=True ) # load environment variables from .env

from langchain_openai import ChatOpenAI

import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

from langchain_huggingface import HuggingFaceEmbeddings
embedding_model = HuggingFaceEmbeddings( model_name="BAAI/bge-large-en-v1.5", model_kwargs = {'device': device}, encode_kwargs = {'normalize_embeddings': False} )

import streamlit as st

import os
from pathlib import Path
import chromadb

store_path = Path.home() / 'chroma'

#%%

def get_knowledge_base():
    try:
        query_params = st.query_params
        if "kb" in query_params:
            return query_params["kb"]
    except:
        pass   

    return os.getenv("RAG_KNOWLEDGE_BASE")


def list_available_kbs():
    try:
        client = chromadb.PersistentClient(path=store_path)
        return [collection.name for collection in client.list_collections()]
    except:
        return []

from streamlit_javascript import st_javascript
url = st_javascript("await fetch('').then(r => window.parent.location.href)")

knowledge_base = get_knowledge_base()
debug = st.query_params.get("debug", "0") == "1" if hasattr(st, "query_params") else os.getenv("RAG_DEBUG", "0") == "1"

if knowledge_base is None:
    st.error("No knowledge base specified!")    
    st.markdown("\n**Available knowledge bases:**")
    for kb in list_available_kbs():
        st.markdown(f"- [`{kb}`]({url}?kb={kb})")
    st.markdown("### Usage:")
    st.markdown("Add `?kb=<knowledge_base>` to the URL, or set the `RAG_KNOWLEDGE_BASE` environment variable.")
    st.markdown("\n**Example URLs:**")
    st.text(f"- {url}?kb=your_kb_name")
    st.text(f"- {url}?kb=your_kb_name&debug=1")
    st.stop()

llm = ChatOpenAI( model='simonbb', max_tokens=4096, temperature=0.7, extra_body={"chat_template_kwargs": {"enable_thinking": False}},)

retriever = MultiQueryRerankRetriever( persist_directory=store_path, collection_name=knowledge_base, embeddings=embedding_model )
model = build_rag(retriever, llm)

st.title(knowledge_base.upper())
st.session_state.setdefault("messages", [])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input(f'Ask a question about {knowledge_base}'):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        response = model.invoke( query )
        answer = response["answer"]
        citations = response["sources"]
        st.markdown(answer)

        with st.expander("View Retrieved Source Snippets"):
            for i, citation in enumerate(citations, 1):
                source = citation.metadata.get('source', 'Unknown')
                page = citation.metadata.get('page', 'N/A')
                st.markdown(f"**Snippet {i}** | Source: {source} | Page: {page}")
                st.text_area(f"Content {i}", citation.page_content, height=150, label_visibility="collapsed")                
                st.divider()
    st.session_state.messages.append({"role": "assistant", "content": answer})