from app.documents.txt_loader import load_txt
from app.documents.pdf_loader import load_pdf
from app.documents.docx_loader import load_docx


def load_document(filepath: str):

    if filepath.endswith(".txt"):
        return load_txt(filepath)

    elif filepath.endswith(".pdf"):
        return load_pdf(filepath)

    elif filepath.endswith(".docx"):
        return load_docx(filepath)

    else:
        raise Exception("Unsupported file type")