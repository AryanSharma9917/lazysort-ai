import pytest
from fastapi import HTTPException

from app.main import analyze, health, index, ollama, scan, settings, upload_folder
from app.models import AnalyzeRequest, ScanRequest


class FakeUpload:
    def __init__(self, content: bytes):
        self.content = content

    async def read(self, _size: int) -> bytes:
        content, self.content = self.content, b""
        return content


@pytest.mark.asyncio
async def test_index_is_dashboard():
    response = await index()
    assert "LazySort never deletes" in response


@pytest.mark.asyncio
async def test_scan_validation_rejects_missing_folder():
    with pytest.raises(HTTPException) as exc:
        await scan(ScanRequest(folder="/definitely/not/a/real/folder"))
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_health(monkeypatch):
    async def fake_health():
        return {"status": "ready", "model": "gemma3:4b"}

    monkeypatch.setattr(ollama, "health", fake_health)
    assert (await health())["status"] == "ready"


@pytest.mark.asyncio
async def test_analyze_rejects_file_missing_from_fresh_scan(tmp_path):
    missing = tmp_path / "gone.txt"
    with pytest.raises(HTTPException) as exc:
        await analyze(AnalyzeRequest(folder=str(tmp_path), files=[str(missing)]))
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_folder_upload_preserves_safe_relative_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    uploaded = FakeUpload(b"hello")
    result = await upload_folder([uploaded], ["chosen-folder/notes/note.txt"])
    destination = __import__("pathlib").Path(result["folder"]) / "notes" / "note.txt"
    assert destination.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_folder_upload_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    uploaded = FakeUpload(b"nope")
    with pytest.raises(HTTPException) as exc:
        await upload_folder([uploaded], ["../note.txt"])
    assert exc.value.status_code == 400
