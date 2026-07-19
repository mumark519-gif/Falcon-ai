from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import app.services.chat_service as chat_service

from app.auth import get_current_user
from app.database import get_db
from app.models import Conversation, Chat


router = APIRouter()


class RenameChatRequest(BaseModel):
    chat_id: int
    title: str


class ChatRequest(BaseModel):
    chat_id: int
    message: str


class CreateChatRequest(BaseModel):
    title: str


@router.put("/rename-chat")
def rename_chat(
    request: RenameChatRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    chat = (
        db.query(Chat)
        .filter(
            Chat.id == request.chat_id,
            Chat.username == current_user,
        )
        .first()
    )

    if not chat:
        return {
            "error": "Chat not found"
        }

    chat.title = request.title

    db.commit()
    db.refresh(chat)

    return {
        "message": "Chat renamed successfully",
        "chat": chat,
    }


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.chat(
        request,
        current_user,
        db,
    )


@router.delete("/chat/{chat_id}")
def delete_chat(
    chat_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Delete all messages
    db.query(Conversation).filter(
        Conversation.chat_id == chat_id,
        Conversation.username == current_user,
    ).delete()

    # Delete the chat
    db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.username == current_user,
    ).delete()

    db.commit()

    return {
        "message": "Chat deleted successfully"
    }


@router.get("/search-chats")
def search_chats(
    q: str = Query(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    chats = (
        db.query(Chat)
        .filter(
            Chat.username == current_user,
            Chat.title.ilike(f"%{q}%"),
        )
        .order_by(Chat.created_at.desc())
        .all()
    )

    return chats


@router.post("/create_chat")
def create_chat(
    request: CreateChatRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    chat = Chat(
        username=current_user,
        title=request.title,
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "chat_id": chat.id,
        "title": chat.title,
    }


@router.get("/chats")
def get_chats(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    chats = (
        db.query(Chat)
        .filter(
            Chat.username == current_user,
        )
        .order_by(Chat.created_at.desc())
        .all()
    )

    return chats


@router.get("/chat/{chat_id}")
def get_chat_messages(
    chat_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    messages = (
        db.query(Conversation)
        .filter(
            Conversation.username == current_user,
            Conversation.chat_id == chat_id,
        )
        .order_by(Conversation.id)
        .all()
    )

    return messages