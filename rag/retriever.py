from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

ROOT = Path(__file__).resolve().parents[1]
PERSIST_DIR = ROOT / "vectorstore"
COLLECTION_NAME = "singapore_travel"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


def get_vectorstore() -> Chroma:
    if not PERSIST_DIR.exists():
        raise RuntimeError("Vector store not found. Run: python rag/ingest.py")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIR),
    )


def retrieve(query: str, k: int = 6) -> list[Document]:
    return get_vectorstore().similarity_search(query, k=k)


def format_retrieval(docs: list[Document]) -> str:
    if not docs:
        return "NO_KNOWLEDGE_FOUND"
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(
            f"[Source {i}]\n"
            f"Title: {doc.metadata.get('source_title', 'Unknown')}\n"
            f"URL: {doc.metadata.get('source_url', '')}\n"
            f"Content:\n{doc.page_content}"
        )
    return "\n\n".join(parts)
