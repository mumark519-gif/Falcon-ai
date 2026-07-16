def load_txt(filepath: str):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()