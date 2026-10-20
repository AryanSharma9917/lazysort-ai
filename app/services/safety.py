import os
import re
from pathlib import Path


IGNORED_PARTS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
PROTECTED_POSIX = {
    Path("/"), Path("/bin"), Path("/boot"), Path("/dev"), Path("/etc"),
    Path("/lib"), Path("/lib64"), Path("/proc"), Path("/root"), Path("/run"),
    Path("/sbin"), Path("/sys"), Path("/usr"), Path("/var"), Path("/System"),
    Path("/Applications"), Path("/Library"),
}


def sanitize_component(value: str) -> str:
    value = value.strip()
    if not value or value in {".", ".."} or Path(value).is_absolute():
        raise ValueError("invalid path component")
    if any(char in value for char in ("/", "\\", "\0")) or re.search(r"[\x00-\x1f]", value):
        raise ValueError("path separators and control characters are forbidden")
    if value.rstrip(". ").upper().split(".")[0] in WINDOWS_RESERVED:
        raise ValueError("reserved filename")
    if value.endswith((".", " ")):
        raise ValueError("unsafe trailing character")
    return value


def validate_root(folder: str | Path) -> Path:
    raw = Path(folder).expanduser()
    if raw.is_symlink():
        raise ValueError("selected folder cannot be a symlink")
    root = raw.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("selected path is not a directory")
    if root in PROTECTED_POSIX:
        raise ValueError("protected system directory")
    anchor = Path(root.anchor)
    if root == anchor:
        raise ValueError("filesystem roots are protected")
    lowered = {part.lower() for part in root.parts}
    if {"windows", "program files", "program files (x86)"} & lowered:
        raise ValueError("protected system directory")
    return root


def ensure_within(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(resolved_root):
        raise ValueError("path escapes selected folder")
    return resolved


def validate_source(root: Path, source: str | Path) -> Path:
    path = ensure_within(root, Path(source))
    if path.is_symlink() or not path.is_file():
        raise ValueError("source must be a regular non-symlink file")
    return path


def build_destination(root: Path, category: str, subcategory: str, filename: str) -> Path:
    parts = [sanitize_component(x) for x in (category, subcategory, filename)]
    return ensure_within(root, root.joinpath(*parts))


def conflict_free(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
