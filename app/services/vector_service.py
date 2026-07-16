import chromadb
from sentence_transformers import SentenceTransformer
from app.documents.text_splitter import split_text

client = chromadb.PersistentClient(path="data/chroma")

collection = client.get_or_create_collection(
    name="falcon_documents"
)

model = SentenceTransformer("all-MiniLM-L6-v2")


def add_document(username: str, document_id: str, text: str):

    chunks = split_text(text)

    for i, chunk in enumerate(chunks):

        embedding = model.encode(chunk).tolist()

        collection.add(
            ids=[f"{document_id}_{i}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[
                {
                    "username": username,
                    "document": document_id,
                    "chunk": i
               }
            ]
        )

def search_documents(
    username: str,
    query: str,
    n_results=3
):

    embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={
        "username": username
        }
    )

    documents = results.get("documents", [[]])[0]

    distances = results.get("distances", [[]])[0]

    if not documents:
        return ""

    ranked = sorted(
        zip(documents, distances),
        key=lambda x: x[1]
   )

    unique_documents = []

    seen = set()

    for document, _ in ranked:

        if document not in seen:
            unique_documents.append(document)
            seen.add(document)

    return "\n\n".join(unique_documents)