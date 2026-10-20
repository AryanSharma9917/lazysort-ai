import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.models import CompletedOperation, ExecuteItem, Transaction
from app.services.history import HistoryStore
from app.services.safety import build_destination, conflict_free, validate_root, validate_source


def execute_plan(folder: str, items: list[ExecuteItem], store: HistoryStore) -> tuple[Transaction, dict]:
    root = validate_root(folder)
    transaction = Transaction(
        session_id=uuid4().hex, root=str(root), created_at=datetime.now(timezone.utc), operations=[]
    )
    stats = {"moved": 0, "renamed": 0, "folders_created": 0, "skipped": 0, "errors": [], "deleted": 0}
    for item in items:
        try:
            source = validate_source(root, item.source)
            destination = conflict_free(build_destination(root, item.category, item.subcategory, item.suggested_filename))
            if source == destination:
                stats["skipped"] += 1
                continue
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                stats["folders_created"] += 1
            shutil.move(str(source), str(destination))
            transaction.operations.append(CompletedOperation(
                source=str(source), destination=str(destination), timestamp=datetime.now(timezone.utc)
            ))
            stats["moved"] += 1
            if source.name != destination.name:
                stats["renamed"] += 1
        except (OSError, ValueError) as exc:
            stats["errors"].append({"source": item.source, "error": str(exc)})
    if transaction.operations:
        store.save(transaction)
    return transaction, stats


def undo_transaction(transaction: Transaction, store: HistoryStore) -> dict:
    root = validate_root(transaction.root)
    restored, errors = 0, []
    for operation in reversed(transaction.operations):
        try:
            current = validate_source(root, operation.destination)
            original = Path(operation.source)
            if original.exists():
                raise ValueError("original location is occupied")
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current), str(original))
            restored += 1
        except (OSError, ValueError) as exc:
            errors.append({"source": operation.destination, "error": str(exc)})
    if not errors:
        store.remove(transaction.session_id)
    return {"session_id": transaction.session_id, "restored": restored, "errors": errors, "deleted": 0}
