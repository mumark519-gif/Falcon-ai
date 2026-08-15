from app.models import Chat
from app.ai_service import generate_chat_title


def update_chat_title(
    db,
    username: str,
    chat_id: int,
    first_message: str,
):

    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.username == username,
        )
        .first()
    )

    if (
        chat
        and chat.title == "New Chat"
    ):

        chat.title = generate_chat_title(
            first_message
        )