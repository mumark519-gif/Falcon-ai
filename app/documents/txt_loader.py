def load_txt(filepath: str):

    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as file:

        text = file.read()

    return {
        "type": "txt",
        "content": text,
        "metadata": {},
    }