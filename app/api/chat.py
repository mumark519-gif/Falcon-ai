from fastapi import APIRouter, Depends, Query
import app.services.chat_service as chat_service
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import Conversation, Chat, Memory
from app.ai_service import (
    ask_ai,
    extract_memory,
    generate_chat_title,
)

router = APIRouter()

class RenameChatRequest(BaseModel):
    chat_id: int
    title: str

@router.put("/rename-chat")
def rename_chat(
    request: RenameChatRequest,
    current_user: str = Depends(get_current_user)
):
    db = SessionLocal()

    chat = (
        db.query(Chat)
        .filter(
            Chat.id == request.chat_id,
            Chat.username == current_user
        )
        .first()
    )

    if not chat:
        db.close()
        return {"error": "Chat not found"}

    chat.title = request.title

    db.commit()
    db.refresh(chat)

    db.close()

    return {
        "message": "Chat renamed successfully",
        "chat": chat
    }

class ChatRequest(BaseModel):
    chat_id: int
    message: str
@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    return chat_service.chat(request, current_user)


@router.delete("/chat/{chat_id}")
def delete_chat(
    chat_id: int,
    current_user: str = Depends(get_current_user)
):
    db = SessionLocal()

    # Delete all messages in the chat
    db.query(Conversation).filter(
        Conversation.chat_id == chat_id,
        Conversation.username == current_user
    ).delete()

    # Delete the chat
    db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.username == current_user
    ).delete()

    db.commit()
    db.close()

    return {
        "message": "Chat deleted successfully"
    }

@router.get("/search-chats")
def search_chats(
    q: str = Query(...),
    current_user: str = Depends(get_current_user)
):
    db = SessionLocal()

    chats = (
        db.query(Chat)
        .filter(
            Chat.username == current_user,
            Chat.title.ilike(f"%{q}%")
        )
        .order_by(Chat.created_at.desc())
        .all()
    )

    db.close()

    return chats
class CreateChatRequest(BaseModel):
    title: str
@router.post("/create_chat")
def create_chat(
    request: CreateChatRequest,
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    chat = Chat(
        username=current_user,
        title=request.title
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    db.close()

    return {
        "chat_id": chat.id,
        "title": chat.title
    }

@router.get("/chats")
def get_chats(
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    chats = (
        db.query(Chat)
        .filter(Chat.username == current_user)
        .order_by(Chat.created_at.desc())
        .all()
    )

    db.close()

    return chats
@router.get("/chat/{chat_id}")
def get_chat_messages(
    chat_id: int,
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    messages = (
        db.query(Conversation)
        .filter(
            Conversation.username == current_user,
            Conversation.chat_id == chat_id
        )
        .order_by(Conversation.id)
        .all()
    )

    db.close()

    return messages