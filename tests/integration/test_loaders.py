from app.documents.txt_loader import load_txt

def test_txt_loader(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("Falcon AI loader test.", encoding="utf-8")
    result = load_txt(str(path))
    assert result["content"] == "Falcon AI loader test."
    assert result["type"] == "txt"
