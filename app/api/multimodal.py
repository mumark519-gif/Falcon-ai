from fastapi import APIRouter
from pydantic import BaseModel
from app.intelligence.multimodal import MultimodalController
router=APIRouter(prefix="/multimodal",tags=["multimodal"])
class MediaRequest(BaseModel): media_type:str
@router.post("/requirements")
def requirements(req:MediaRequest): return MultimodalController().requirements(req.media_type)
