from docx import Document


def load_docx(filepath: str):

    document = Document(filepath)

    paragraphs = []

    for index, paragraph in enumerate(document.paragraphs, start=1):

        text = paragraph.text.strip()

        if text:

            paragraphs.append(
                {
                    "paragraph": index,
                    "text": text,
                }
            )

    core = document.core_properties

    return {
        "type": "docx",
        "paragraphs": paragraphs,
        "metadata": {
            "title": core.title,
            "author": core.author,
            "subject": core.subject,
            "keywords": core.keywords,
            "category": core.category,
        },
        "paragraph_count": len(paragraphs),
    }