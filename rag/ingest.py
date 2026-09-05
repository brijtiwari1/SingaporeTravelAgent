from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "singapore"
PERSIST_DIR = ROOT / "vectorstore"
COLLECTION_NAME = "singapore_travel"

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


def load_markdown_documents() -> list[Document]:
    docs: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        metadata = {
            "source_title": lines[0].lstrip("# ").strip() if lines else path.stem,
            "source_url": next(
                (line.split(":", 1)[1].strip() for line in lines if line.startswith("Source URL:")),
                "",
            ),
            "file": path.name,
        }
        body = "\n".join(
            line for line in lines if not line.startswith("Source URL:")
        )
        docs.append(Document(page_content=body, metadata=metadata))
    return docs


def build_vectorstore() -> Chroma:
    source_docs = load_markdown_documents()
    if not source_docs:
        raise RuntimeError(f"No Markdown knowledge-base files found in {DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(source_docs)

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )

    # Rebuild the local collection each time so removed/edited source content
    # cannot remain as stale vectors.
    db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    existing = db.get()
    if existing.get("ids"):
        db.delete(ids=existing["ids"])
    db.add_documents(chunks)
    return db


if __name__ == "__main__":
    db = build_vectorstore()
    print(f"Knowledge base created: {db._collection.count()} chunks")
