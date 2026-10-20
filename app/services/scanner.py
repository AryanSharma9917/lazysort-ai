import mimetypes
from pathlib import Path

from app.models import FileInfo
from app.services.safety import IGNORED_PARTS, validate_root


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}


def scan_folder(folder: str, recursive: bool = False) -> tuple[Path, list[FileInfo]]:
    root = validate_root(folder)
    iterator = root.rglob("*") if recursive else root.iterdir()
    files: list[FileInfo] = []
    for path in iterator:
        try:
            relative = path.relative_to(root)
            if any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            stat = path.stat()
        except (OSError, ValueError):
            continue
        extension = path.suffix.lower()
        files.append(FileInfo(
            path=str(path.resolve()), relative_path=str(relative), name=path.name,
            extension=extension, size=stat.st_size,
            modified_at=stat.st_mtime, mime_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            supported=extension in SUPPORTED_EXTENSIONS,
        ))
    return root, sorted(files, key=lambda item: item.relative_path.lower())
