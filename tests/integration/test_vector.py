from app.services.vector_service import (
    add_document,
    search_documents,
)


add_document(
    "test_user",
    "1",
    "Falcon AI is being built by Muhammad."
)
results = search_documents(
    "test_user",
    "Who is building Falcon AI?"
)

print(results)