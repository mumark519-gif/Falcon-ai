from app.services.vector_service import search_documents

context = search_documents(
    "Who is building Falcon AI?"
)

print(context)