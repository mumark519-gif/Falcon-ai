from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    from sqlalchemy import DateTime
from datetime import datetime


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, index=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))

    role = Column(String)

    message = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)




class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, index=True)

    title = Column(String, default="New Chat")

    created_at = Column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, index=True)

    key = Column(String)

    value = Column(String)