import re


def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
):

    if not text:
        return []

    text = re.sub(r"\n{3,}", "\n\n", text)

    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current_chunk) + len(paragraph) < chunk_size:

            if current_chunk:

                current_chunk += "\n\n"

            current_chunk += paragraph

        else:

            if current_chunk:

                chunks.append(current_chunk)

            if overlap > 0 and chunks:

                previous = chunks[-1][-overlap:]

                current_chunk = previous + "\n\n" + paragraph

            else:

                current_chunk = paragraph

    if current_chunk:

        chunks.append(current_chunk)

    return chunks