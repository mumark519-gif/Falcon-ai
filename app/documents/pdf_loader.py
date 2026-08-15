from pypdf import PdfReader


def load_pdf(filepath: str):

    reader = PdfReader(filepath)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    metadata = reader.metadata or {}

    return {
        "type": "pdf",
        "pages": pages,
        "metadata": {
            "title": metadata.get("/Title"),
            "author": metadata.get("/Author"),
            "subject": metadata.get("/Subject"),
            "creator": metadata.get("/Creator"),
            "producer": metadata.get("/Producer"),
        },
        "page_count": len(pages),
    }