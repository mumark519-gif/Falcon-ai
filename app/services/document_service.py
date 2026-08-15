from __future__ import annotations
import os

def load_document(filepath: str):
    extension = os.path.splitext(filepath)[1].lower()
    if extension == ".txt":
        from app.documents.txt_loader import load_txt
        return load_txt(filepath)
    if extension == ".pdf":
        from app.documents.pdf_loader import load_pdf
        return load_pdf(filepath)
    if extension == ".docx":
        from app.documents.docx_loader import load_docx
        return load_docx(filepath)
    raise ValueError(f"Unsupported file type: {extension or 'unknown'}")
