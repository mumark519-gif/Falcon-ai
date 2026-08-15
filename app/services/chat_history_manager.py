from app.models import Conversation


def load_chat_history(
    db,
    username: str,
    chat_id: int,
):

    return (
        db.query(Conversation)
        .filter(
            Conversation.username == username,
            Conversation.chat_id == chat_id,
        )
        .order_by(Conversation.id)
        .all()
    )