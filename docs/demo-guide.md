# Demo guide

1. Run `python demo/create_demo_files.py` and show the messy `demo_workspace/` folder.
2. Run `ollama serve`, then `ollama pull gemma3:4b` if needed.
3. Start LazySort with `uvicorn app.main:app --reload`.
4. Open `http://127.0.0.1:8000` and show “Gemma ready.”
5. Enter the absolute path to `demo_workspace` and scan it.
6. Show Gemma's categories, names, explanations, and confidence.
7. Select individual suggestions (and explain that low confidence needs attention).
8. Click **Organize approved** and show the resulting folders and “Deleted 0.”
9. Click **Undo last run** and show the original files restored.
10. Briefly show the tests and repository.

Record real timings and file counts during this run for the DEV submission. Do not use personal files in the recording.
