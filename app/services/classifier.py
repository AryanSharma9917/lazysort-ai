import json
import re
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from app.models import Classification, FileInfo, ProposedOperation
from app.prompts.classify import build_prompt
from app.services.extractor import extract_text
from app.services.safety import build_destination


def parse_classification(raw: str, original_extension: str) -> Classification:
    cleaned = raw.strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    result = Classification.model_validate(json.loads(cleaned))
    if Path(result.suggested_filename).suffix.lower() != original_extension.lower():
        raise ValueError("model changed the file extension")
    return result


async def classify_file(root: Path, info: FileInfo, client, max_chars: int, max_bytes: int) -> ProposedOperation:
    content = extract_text(Path(info.path), max_chars, max_bytes) if info.supported else ""
    prompt = build_prompt(info, content)
    last_error: Exception | None = None
    for _ in range(2):
        try:
            result = parse_classification(await client.generate(prompt), info.extension)
            destination = build_destination(root, result.category, result.subcategory, result.suggested_filename)
            return ProposedOperation(
                id=uuid4().hex, source=info.path, destination=str(destination),
                **result.model_dump(), needs_review=result.confidence == "low",
            )
        except (ValueError, KeyError, json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            prompt += "\nYour prior response was invalid. Return one valid JSON object only."
    destination = build_destination(root, "Needs Review", "Unclassified", info.name)
    return ProposedOperation(
        id=uuid4().hex, source=info.path, destination=str(destination),
        category="Needs Review", subcategory="Unclassified", suggested_filename=info.name,
        reason=f"AI response could not be validated ({type(last_error).__name__}).",
        confidence="low", needs_review=True,
    )
