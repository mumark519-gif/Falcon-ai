import os

from app.documents.txt_loader import load_txt
from app.documents.pdf_loader import load_pdf
from app.documents.docx_loader import load_docx


def load_document(filepath: str):

    extension = os.path.splitext(filepath)[1].lower()

    if extension == ".txt":
        return load_txt(filepath)

    elif extension == ".pdf":
        return load_pdf(filepath)

    elif extension == ".docx":
        return load_docx(filepath)

    else:
        raise Exception(f"Unsupported file type: {extension}")