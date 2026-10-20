import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models import AnalyzeRequest, ExecuteRequest, ScanRequest, UndoRequest
from app.services.classifier import classify_file
from app.services.history import HistoryStore
from app.services.ollama import OllamaClient
from app.services.organizer import execute_plan, undo_transaction
from app.services.safety import sanitize_component, validate_root, validate_source
from app.services.scanner import scan_folder


BASE = Path(__file__).parent
settings = get_settings()
history = HistoryStore(settings.history_dir)
ollama = OllamaClient(settings.ollama_base_url, settings.ollama_model, settings.request_timeout_seconds)
app = FastAPI(title="LazySort AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (BASE / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
async def health():
    return await ollama.health()


@app.post("/api/upload")
async def upload_folder(files: list[UploadFile] = File(...), relative_paths: list[str] = Form(...)):
    if not files or len(files) != len(relative_paths):
        raise HTTPException(400, "Each uploaded file must have one relative path")
    session = settings.upload_dir / uuid4().hex
    total = 0
    saved = 0
    try:
        session.mkdir(parents=True, exist_ok=False)
        validated_paths = []
        for relative in relative_paths:
            raw_parts = Path(relative.replace("\\", "/")).parts
            if not raw_parts or len(raw_parts) > 32:
                raise ValueError("invalid uploaded path")
            validated_paths.append(tuple(sanitize_component(part) for part in raw_parts))
        for uploaded, parts in zip(files, validated_paths, strict=True):
            destination = session.joinpath(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                while chunk := await uploaded.read(1024 * 1024):
                    total += len(chunk)
                    if total > settings.max_upload_bytes:
                        raise ValueError("folder exceeds upload size limit")
                    output.write(chunk)
            saved += 1
    except (OSError, ValueError) as exc:
        shutil.rmtree(session, ignore_errors=True)
        raise HTTPException(400, str(exc)) from exc
    top = validated_paths[0][0]
    root = session / top if all(parts[0] == top for parts in validated_paths) else session
    return {"folder": str(root.resolve()), "files_uploaded": saved, "bytes_uploaded": total}


@app.post("/api/scan")
async def scan(request: ScanRequest):
    try:
        root, files = scan_folder(request.folder, request.recursive)
        return {"root": str(root), "files": [item.model_dump() for item in files], "count": len(files)}
    except (OSError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        root = validate_root(request.folder)
        _, scanned = scan_folder(str(root), recursive=True)
        by_path = {item.path: item for item in scanned}
        selected = []
        for value in request.files:
            source = str(validate_source(root, value))
            if source not in by_path:
                raise ValueError("file was not found in a fresh scan")
            selected.append(by_path[source])
    except (OSError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    results = []
    for item in selected:
        try:
            # Revalidate immediately before extraction: another local client may
            # have moved the file since the fresh scan above.
            validate_source(root, item.path)
            results.append(await classify_file(
                root, item, ollama, settings.max_extracted_chars, settings.max_file_bytes
            ))
        except (OSError, ValueError) as exc:
            raise HTTPException(409, f"File changed during analysis: {item.name}") from exc
    return {"operations": [item.model_dump() for item in results]}


@app.post("/api/execute")
async def execute(request: ExecuteRequest):
    try:
        transaction, stats = execute_plan(request.folder, request.operations, history)
        return {"session_id": transaction.session_id, "operations": len(transaction.operations), "stats": stats}
    except (OSError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/undo")
async def undo(request: UndoRequest):
    transaction = history.get(request.session_id)
    if transaction is None:
        raise HTTPException(404, "No organization session found")
    try:
        return undo_transaction(transaction, history)
    except (OSError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/history")
async def get_history():
    return {"sessions": [item.model_dump() for item in history.list()]}
