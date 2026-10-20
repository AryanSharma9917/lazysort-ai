# LazySort AI

> Drop the mess. Let AI sort it out.

LazySort is a local-first file organizer that uses **Gemma 3 through Ollama** to understand messy files, propose meaningful folders and names, and let you approve every change. It is a submission project for the [Hacktoberfest 2026 Week 3: Slow and Steady challenge](https://dev.to/challenges/hacktoberfest-week3-2026-10-19).

Instead of opening, identifying, renaming, and sorting files one by one, select a folder and review the organization plan Gemma prepares. LazySort never deletes files.

## Why open-source AI?

File names and document contents can be personal. When `OLLAMA_BASE_URL` points to localhost, inference happens on your machine: there is no mandatory proprietary AI API, no analytics, and no permanent storage of extracted content. You can also swap the configured Ollama model. If you configure a remote Ollama endpoint, extracted information is sent to that server—local inference is not an absolute privacy guarantee.

## Features

- Semantic classification and descriptive renaming with Gemma 3 4B
- Bounded extraction from TXT, Markdown, PDF, DOCX, CSV, and JSON
- Strict structured output, Pydantic validation, and one retry for malformed model output
- Preview-first workflow with per-file or approve-all selection
- Explainable suggestions and high/medium/low confidence
- Protected-directory, traversal, reserved-name, and symlink defenses
- Conflict-safe moves: existing files are never overwritten
- Transaction log and undo for completed operations
- Accurate partial-failure reporting and zero deletion
- Responsive, accessible dashboard and local model status
- Fictional demo-file generator and mocked test suite

## Safety architecture

```text
Scan → bounded extraction → Gemma → validate → preview → approval → move → transaction log
```

The model never receives a filesystem tool and never constructs an executable path. It suggests three path components; the application sanitizes them, preserves the extension, verifies containment inside the chosen root, and acts only on explicitly submitted operations. No delete endpoint exists.

See [the architecture notes](docs/architecture.md) for trust boundaries and limitations.

## Install

Requirements: Python 3.11+, [Ollama](https://ollama.com/), and enough memory to run Gemma 3 4B.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ollama pull gemma3:4b
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The server should remain local: LazySort is not designed as a remotely exposed multi-user service.

### Use it

1. Select **Choose folder** and pick a folder. LazySort uploads a working copy so the original is untouched. Alternatively, paste an absolute local path to organize that folder directly.
2. Select **Scan folder** and wait while Gemma analyzes the files.
3. Review the proposed folders, filenames, explanations, and confidence levels.
4. Edit any proposal, check the operations you accept, or select **Approve all**.
5. Select **Organize approved**. LazySort reports the completed moves and always reports zero deletions.
6. Select **Undo last run** if you want to restore the files.

For a safe first run, choose the tracked `demo/upload-this-folder` sample. It contains fictional files only. You can also generate a fresh messy workspace with `python demo/create_demo_files.py`.

Configuration:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `gemma3:4b` | Open-weight model |
| `MAX_FILE_BYTES` | `10485760` | Largest file considered for extraction |
| `MAX_EXTRACTED_CHARS` | `12000` | Maximum content sent per file |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Model request timeout |
| `HISTORY_DIR` | `~/.lazysort/history` | Filesystem-operation metadata only |

## Safe demo

```bash
python demo/create_demo_files.py
```

This creates ignored `demo_workspace/` files containing only fictional data. Follow [the demo guide](docs/demo-guide.md).

## Test

```bash
pytest -q
```

Tests use temporary folders and mock model output; Ollama and Gemma are not needed. CI runs the same suite.

## API

- `GET /api/health` — Ollama/model state
- `POST /api/scan` — validate and scan a folder
- `POST /api/upload` — create a safe staged working copy from a browser folder upload
- `POST /api/analyze` — extract and classify selected scanned files
- `POST /api/execute` — move only submitted operations
- `POST /api/undo` — undo a session (latest by default)
- `GET /api/history` — transaction metadata

Interactive OpenAPI documentation is available at `/docs` while the app runs.

## Limitations and security

- The browser cannot open a native directory chooser for arbitrary server paths; enter the local path.
- PDF extraction is text-only; scanned images need OCR. Images/audio use filename and metadata only.
- Model suggestions can be wrong. Review is a required part of the design, especially for low-confidence results.
- Undo will not overwrite a file that appeared at the original location after organization.
- Authentication is intentionally absent because this is a localhost tool. Do not expose it publicly.
- File content can contain prompt injection. The prompt marks it as untrusted data, while deterministic application code enforces all filesystem policy.

## Screenshots

Add real screenshots after running the completed demo. No mock screenshots are presented as product output.

## Roadmap

- Editable category and filename controls in the review UI
- Optional local OCR and image understanding
- Streaming batch progress and cancellation
- Cross-platform packaged desktop release

Contributions are welcome. Please open an issue before large changes and include tests for filesystem behavior. Licensed under the [MIT License](LICENSE).
