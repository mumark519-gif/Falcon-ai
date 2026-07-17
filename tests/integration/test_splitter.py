from app.documents.text_splitter import split_text

text = (
    "Falcon AI is the future of enterprise artificial intelligence. "
    * 100
)

chunks = split_text(text)

print("Chunks:", len(chunks))

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i + 1}")
    print(chunk[:80])