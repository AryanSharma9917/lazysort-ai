# Architecture and trust boundaries

```text
Browser dashboard
      ↓ localhost HTTP
FastAPI request validation
      ↓
Scanner → bounded extractor → prompt builder
                              ↓
                    configured Ollama endpoint
                              ↓
                         Gemma 3 4B
                              ↓ JSON suggestion
Pydantic validation → safety layer → preview
                                      ↓ explicit approval
                               organizer → log → undo
```

## Boundaries

The selected folder and each source file are untrusted. The scanner rejects protected roots, skips dependency folders and symlinks, and resolves each source beneath the selected root again immediately before use.

Document text is also untrusted. Extraction is size- and character-bounded and its prompt wrapper explicitly identifies the content as data. Prompt defenses are not treated as authorization: Gemma can only return classification fields and has no filesystem tool.

Model output is untrusted. Pydantic checks its shape, confidence vocabulary, length, safe path components, and preserved extension. The application—not Gemma—builds the destination and proves it remains inside the root. Invalid output is retried once and then becomes a low-confidence “Needs Review” item.

Execution is a separate user-approved API request. Every source is revalidated, destinations use deterministic numeric suffixes rather than overwriting, and each successful move is logged immediately in the returned transaction. A later failure does not hide earlier successes.

History contains paths, timestamps, and operation types, never extracted document content. Undo works in reverse order and refuses to overwrite a newly occupied original path.

## Privacy

LazySort sends extracted snippets only to `OLLAMA_BASE_URL`. With the default localhost endpoint this is local inference. A user-supplied remote endpoint changes that privacy boundary. The app itself has no analytics or cloud storage.
