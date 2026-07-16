from fastapi import APIRouter, UploadFile, File, Depends
from app.auth import get_current_user
from app.services.document_service import load_document
from app.services.vector_service import add_document
import shutil
import os
router = APIRouter()

UPLOAD_FOLDER = "data/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):

    filename = f"{current_user}_{file.filename}"

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = load_document(filepath)

    add_document(
        username=current_user,
        document_id=filename,
        text=text
    )

    return {
    "message": "File uploaded and indexed successfully",
    "filename": filename,
    "characters": len(text)
}