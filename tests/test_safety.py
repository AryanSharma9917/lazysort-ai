from pathlib import Path

import pytest

from app.services.safety import build_destination, conflict_free, sanitize_component, validate_root


@pytest.mark.parametrize("value", ["..", "a/b", "a\\b", "/etc", "CON", "bad\0name"])
def test_rejects_unsafe_components(value):
    with pytest.raises(ValueError):
        sanitize_component(value)


def test_build_destination_stays_inside_root(tmp_path):
    result = build_destination(tmp_path, "Finance", "Invoices", "invoice.pdf")
    assert result == tmp_path / "Finance" / "Invoices" / "invoice.pdf"


def test_conflict_suffix_is_deterministic(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("one")
    (tmp_path / "note-2.txt").write_text("two")
    assert conflict_free(target).name == "note-3.txt"


def test_symlink_root_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        validate_root(link)
