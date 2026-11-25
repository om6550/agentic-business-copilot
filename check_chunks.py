import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="business_knowledge")

results = collection.get(
    where={"source": "sales_policy.txt"},
    include=["documents", "metadatas"]
)

print("\n--- SALES POLICY CHUNKS ---")

for document, metadata in zip(
    results["documents"],
    results["metadatas"]
):
    print("\nCHUNK:", metadata.get("chunk_id"))
    print("-" * 40)
    print(document)