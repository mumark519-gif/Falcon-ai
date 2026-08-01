from app.models import Conversation


def save_message(
    db,
    username: str,
    chat_id: int,
    role: str,
    message: str,
):

    db.add(
        Conversation(
            username=username,
            chat_id=chat_id,
            role=role,
            message=message,
        )
    )

    db.commit()