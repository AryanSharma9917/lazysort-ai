import json
from pathlib import Path

from app.models import Transaction


class HistoryStore:
    def __init__(self, directory: Path):
        self.directory = directory

    def save(self, transaction: Transaction) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"{transaction.session_id}.json"
        target.write_text(transaction.model_dump_json(indent=2), encoding="utf-8")

    def list(self) -> list[Transaction]:
        if not self.directory.exists():
            return []
        records = []
        for path in self.directory.glob("*.json"):
            try:
                records.append(Transaction.model_validate_json(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return sorted(records, key=lambda item: item.created_at, reverse=True)

    def get(self, session_id: str | None = None) -> Transaction | None:
        records = self.list()
        if session_id is None:
            return records[0] if records else None
        return next((item for item in records if item.session_id == session_id), None)

    def remove(self, session_id: str) -> None:
        path = self.directory / f"{session_id}.json"
        if path.exists():
            path.unlink()
