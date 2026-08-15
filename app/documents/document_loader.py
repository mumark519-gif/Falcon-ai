import os

from app.documents.txt_loader import load_txt
from app.documents.pdf_loader import load_pdf
from app.documents.docx_loader import load_docx


SUPPORTED_TYPES = {
    ".txt": load_txt,
    ".pdf": load_pdf,
    ".docx": load_docx,
}


def load_document(filepath: str):

    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    extension = os.path.splitext(filepath)[1].lower()

    loader = SUPPORTED_TYPES.get(extension)

    if loader is None:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    result = loader(filepath)

    return {
        "filename": os.path.basename(filepath),
        "filepath": filepath,
        "extension": extension,
        "content": result,
    }