from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import Memory

router = APIRouter()


class MemoryRequest(BaseModel):
    key: str
    value: str


@router.post("/memory")
def save_memory(
    request: MemoryRequest,
    current_user: str = Depends(get_current_user)
):
    db = SessionLocal()

    memory = (
        db.query(Memory)
        .filter(
            Memory.username == current_user,
            Memory.key == request.key
        )
        .first()
    )

    if memory:
        memory.value = request.value
    else:
        memory = Memory(
            username=current_user,
            key=request.key,
            value=request.value
        )
        db.add(memory)

    db.commit()
    db.close()

    return {
        "message": "Memory saved successfully"
    }