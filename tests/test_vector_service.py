from app.services.vector_service import (
    add_document,
    search_documents,
)


def test_document_search():

    username = "pytest_vector_user"

    document_id = "pytest_document"

    text = """
    Falcon AI is an artificial intelligence assistant.

    Falcon AI helps businesses analyze problems,
    improve operations, and make better decisions.

    Falcon AI can also remember important information
    about users and search uploaded documents.
    """

    # Add document to ChromaDB
    add_document(
        username,
        document_id,
        text,
    )

    # Search the document
    result = search_documents(
        username,
        "What is Falcon AI?",
    )

    # Verify that relevant knowledge was found
    assert result != ""

    assert (
        "artificial intelligence"
        in result.lower()
        or "assistant"
        in result.lower()
    )

def test_document_isolation():

    user_a = "pytest_user_a"
    user_b = "pytest_user_b"

    add_document(
        user_a,
        "user_a_document",
        """
        User A owns a secret company called Falcon Technologies.
        """
    )

    add_document(
        user_b,
        "user_b_document",
        """
        User B owns a company that sells watches.
        """
    )

    # User A searches for their own information
    result_a = search_documents(
        user_a,
        "What company does the user own?"
    )

    # User B searches their own documents
    result_b = search_documents(
        user_b,
        "What company does the user own?"
    )

    assert "Falcon Technologies" in result_a
    assert "Falcon Technologies" not in result_b