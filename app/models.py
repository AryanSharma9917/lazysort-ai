from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


Confidence = Literal["high", "medium", "low"]


class FileInfo(BaseModel):
    path: str
    relative_path: str
    name: str
    extension: str
    size: int
    modified_at: datetime
    mime_type: str
    supported: bool


class Classification(BaseModel):
    category: str = Field(min_length=1, max_length=60)
    subcategory: str = Field(min_length=1, max_length=60)
    suggested_filename: str = Field(min_length=1, max_length=180)
    reason: str = Field(min_length=1, max_length=300)
    confidence: Confidence

    @field_validator("category", "subcategory", "suggested_filename")
    @classmethod
    def safe_components(cls, value: str) -> str:
        from app.services.safety import sanitize_component

        sanitized = sanitize_component(value)
        if sanitized != value.strip():
            raise ValueError("unsafe path component")
        return sanitized


class ProposedOperation(BaseModel):
    id: str
    source: str
    destination: str
    category: str
    subcategory: str
    suggested_filename: str
    reason: str
    confidence: Confidence
    approved: bool = False
    needs_review: bool = False


class ScanRequest(BaseModel):
    folder: str
    recursive: bool = False


class AnalyzeRequest(BaseModel):
    folder: str
    files: list[str]


class ExecuteItem(BaseModel):
    source: str
    category: str
    subcategory: str
    suggested_filename: str

    @model_validator(mode="after")
    def validate_components(self):
        from app.services.safety import sanitize_component

        for value in (self.category, self.subcategory, self.suggested_filename):
            if sanitize_component(value) != value.strip():
                raise ValueError("unsafe destination component")
        return self


class ExecuteRequest(BaseModel):
    folder: str
    operations: list[ExecuteItem]


class UndoRequest(BaseModel):
    session_id: str | None = None


class CompletedOperation(BaseModel):
    source: str
    destination: str
    timestamp: datetime
    operation: Literal["move"] = "move"


class Transaction(BaseModel):
    session_id: str
    root: str
    created_at: datetime
    operations: list[CompletedOperation]
