from app.services.extractor import extract_text
from app.services.scanner import scan_folder


def test_scan_ignores_dependencies_and_symlinks(tmp_path):
    (tmp_path / "hello.txt").write_text("hello")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "dep.txt").write_text("ignored")
    (tmp_path / "link.txt").symlink_to(tmp_path / "hello.txt")
    _, files = scan_folder(str(tmp_path), recursive=True)
    assert [item.name for item in files] == ["hello.txt"]


def test_supported_and_unsupported(tmp_path):
    (tmp_path / "one.md").write_text("# one")
    (tmp_path / "two.png").write_bytes(b"png")
    _, files = scan_folder(str(tmp_path))
    assert {item.name: item.supported for item in files} == {"one.md": True, "two.png": False}


def test_extraction_is_bounded(tmp_path):
    path = tmp_path / "long.txt"
    path.write_text("x" * 100)
    assert extract_text(path, max_chars=12, max_file_bytes=1000) == "x" * 12


def test_large_file_is_not_loaded(tmp_path):
    path = tmp_path / "large.txt"
    path.write_text("x" * 20)
    assert "exceeds" in extract_text(path, max_chars=100, max_file_bytes=10)
