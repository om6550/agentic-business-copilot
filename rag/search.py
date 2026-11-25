from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# -----------------------------
# PATHS
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"


# -----------------------------
# SETTINGS
# -----------------------------

COLLECTION_NAME = "business_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# -----------------------------
# LAZY LOAD MODEL + DATABASE
# -----------------------------

@lru_cache(maxsize=1)
def get_search_resources():
    """Load the embedding model and database only when needed."""

    print("Loading embedding model for the first RAG search...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print("RAG resources are ready.")

    return model, collection


# -----------------------------
# FILTER RELEVANT RESULTS
# -----------------------------

def filter_relevant_results(
    documents,
    metadatas,
    distances,
    max_distance=1.0
):
    """
    Keep only results whose distance is within
    the allowed relevance threshold.

    Lower distance generally means a closer
    semantic match.
    """

    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        if distance <= max_distance:

            filtered_documents.append(document)
            filtered_metadatas.append(metadata)
            filtered_distances.append(distance)

    return (
        filtered_documents,
        filtered_metadatas,
        filtered_distances
    )


# -----------------------------
# SEARCH FUNCTION
# -----------------------------

def search_knowledge(
    query,
    top_k=3,
    source=None,
    max_distance=None
):
    """
    Search business documents using semantic similarity.

    Parameters:
        query: User's question.
        top_k: Number of results to retrieve.
        source: Optional document source restriction.
        max_distance: Optional relevance threshold.

    When max_distance=None, return the nearest results
    without distance filtering.

    This is useful for source-restricted multilingual
    searches where the document source is already known.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if max_distance is not None and max_distance < 0:
        raise ValueError("max_distance cannot be negative.")

    model, collection = get_search_resources()

    # Create query embedding.
    query_embedding = model.encode(
        [query]
    ).tolist()

    # Prepare ChromaDB search options.
    query_options = {
        "query_embeddings": query_embedding,
        "n_results": top_k,
    }

    # Restrict retrieval to a particular source when requested.
    if source is not None:

        query_options["where"] = {
            "source": source
        }

    # Perform semantic search.
    results = collection.query(
        **query_options
    )

    # Extract retrieved results safely.
    documents = (
        results.get("documents") or [[]]
    )[0]

    metadatas = (
        results.get("metadatas") or [[]]
    )[0]

    distances = (
        results.get("distances") or [[]]
    )[0]

    # No documents found.
    if not documents:
        return [], [], []

    # Apply relevance filtering only when a threshold
    # has explicitly been provided.
    if max_distance is not None:

        (
            documents,
            metadatas,
            distances
        ) = filter_relevant_results(
            documents,
            metadatas,
            distances,
            max_distance=max_distance
        )

    return (
        documents,
        metadatas,
        distances
    )


# -----------------------------
# TEST SEARCH
# -----------------------------

if __name__ == "__main__":

    query = input(
        "\nEnter your business question: "
    ).strip()

    if not query:

        print("Please enter a question.")

    else:

        try:

            documents, metadatas, distances = search_knowledge(
                query,
                top_k=5
            )

            print("\n" + "=" * 60)
            print("RAG SEARCH RESULTS")
            print("=" * 60)

            if not documents:

                print("No documents were found.")

            for i, (document, metadata, distance) in enumerate(
                zip(documents, metadatas, distances),
                start=1
            ):

                print(f"\nRESULT {i}")
                print("-" * 60)

                print("Source:", metadata.get("source"))
                print("Chunk:", metadata.get("chunk_id"))
                print("Distance:", round(distance, 4))

                print("\nContent:")
                print(document)

        except Exception as error:

            print("\nSearch error:")
            print(type(error).__name__, error)