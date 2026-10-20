from app.models import ExecuteItem
from app.services.history import HistoryStore
from app.services.organizer import execute_plan, undo_transaction


def item(source, name="clear-note.txt"):
    return ExecuteItem(source=str(source), category="Documents", subcategory="Notes", suggested_filename=name)


def test_execute_and_undo(tmp_path):
    source = tmp_path / "messy.txt"; source.write_text("hello")
    store = HistoryStore(tmp_path / ".history")
    transaction, stats = execute_plan(str(tmp_path), [item(source)], store)
    destination = tmp_path / "Documents" / "Notes" / "clear-note.txt"
    assert destination.exists() and stats["moved"] == 1 and stats["deleted"] == 0
    result = undo_transaction(transaction, store)
    assert source.exists() and result["restored"] == 1


def test_partial_failure_records_success(tmp_path):
    source = tmp_path / "good.txt"; source.write_text("ok")
    missing = tmp_path / "missing.txt"
    transaction, stats = execute_plan(str(tmp_path), [item(source), item(missing)], HistoryStore(tmp_path / ".history"))
    assert len(transaction.operations) == 1
    assert len(stats["errors"]) == 1
