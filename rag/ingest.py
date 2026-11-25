from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# -----------------------------
# PATHS
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"


# -----------------------------
# SETTINGS
# -----------------------------

COLLECTION_NAME = "business_knowledge"

# Lightweight embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Number of characters per chunk
CHUNK_SIZE = 800

# Small overlap helps preserve context between chunks
CHUNK_OVERLAP = 100


# -----------------------------
# LOAD DOCUMENTS
# -----------------------------

def load_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents


# -----------------------------
# CHUNK TEXT
# -----------------------------


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    # Keep each numbered product section separate.
    if (
        "TRACTOR TRAILER PRODUCT CATALOG" in text.upper()
        or "SALES POLICY" in text.upper()
    ):
        import re

        sections = re.split(
            r"(?m)(?=^\s*\d+\.\s+)",
            text
        )

        chunks = []

        for section in sections:
            section = section.strip()

            if not section:
                continue

            # Keep product sections intact when possible.
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Fall back to smaller chunks for long sections.
                start = 0

                while start < len(section):
                    end = min(start + chunk_size, len(section))
                    chunk = section[start:end].strip()

                    if chunk:
                        chunks.append(chunk)

                    if end >= len(section):
                        break

                    start = max(start + 1, end - overlap)

        return chunks

    # Existing boundary-aware chunking for other documents.
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            boundary = text.rfind("\n\n", start, end)

            if boundary == -1:
                boundary = text.rfind(". ", start, end)

            if boundary == -1:
                boundary = text.rfind("\n", start, end)

            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(start + 1, end - overlap)

    return chunks


# -----------------------------
# MAIN INGESTION
# -----------------------------

def ingest_documents():

    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    documents = load_documents()

    if not documents:
        print("No .txt documents found in knowledge folder.")
        return

    all_chunks = []
    all_metadata = []
    all_ids = []

    chunk_number = 0

    for document in documents:

        source = document["source"]
        text = document["text"]

        chunks = chunk_text(text)

        print(f"\nProcessing: {source}")
        print(f"Chunks created: {len(chunks)}")

        for index, chunk in enumerate(chunks):

            chunk_id = f"{source}_{index}"

            all_chunks.append(chunk)

            all_metadata.append({
                "source": source,
                "chunk_id": chunk_id
            })

            all_ids.append(chunk_id)

            chunk_number += 1

    print("\nCreating embeddings...")

    embeddings = model.encode(
        all_chunks,
        show_progress_bar=True
    ).tolist()

    print("Storing data in ChromaDB...")

    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadata
    )

    print("\n--------------------------------")
    print("RAG INGESTION COMPLETED")
    print("--------------------------------")
    print(f"Documents processed: {len(documents)}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"ChromaDB location: {CHROMA_DIR}")
    print(f"Collection: {COLLECTION_NAME}")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    ingest_documents()