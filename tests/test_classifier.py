import pytest

from app.models import FileInfo
from app.services.classifier import classify_file, parse_classification


VALID = '{"category":"Finance","subcategory":"Invoices","suggested_filename":"october-invoice.pdf","reason":"Contains billing data.","confidence":"high"}'


def test_parse_valid_json_and_preserve_extension():
    result = parse_classification(VALID, ".pdf")
    assert result.category == "Finance"


def test_changed_extension_is_rejected():
    with pytest.raises(ValueError):
        parse_classification(VALID, ".txt")


class FakeClient:
    def __init__(self, replies): self.replies = iter(replies); self.calls = 0
    async def generate(self, prompt): self.calls += 1; return next(self.replies)


@pytest.mark.asyncio
async def test_malformed_output_retries_once(tmp_path):
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"")
    stat = source.stat()
    info = FileInfo(path=str(source), relative_path=source.name, name=source.name, extension=".pdf", size=0, modified_at=stat.st_mtime, mime_type="application/pdf", supported=True)
    client = FakeClient(["not json", VALID])
    result = await classify_file(tmp_path, info, client, 100, 100)
    assert client.calls == 2
    assert result.confidence == "high"


@pytest.mark.asyncio
async def test_two_invalid_replies_need_review(tmp_path):
    source = tmp_path / "note.txt"; source.write_text("hello")
    stat = source.stat()
    info = FileInfo(path=str(source), relative_path=source.name, name=source.name, extension=".txt", size=5, modified_at=stat.st_mtime, mime_type="text/plain", supported=True)
    result = await classify_file(tmp_path, info, FakeClient(["bad", "also bad"]), 100, 100)
    assert result.needs_review and result.category == "Needs Review"
