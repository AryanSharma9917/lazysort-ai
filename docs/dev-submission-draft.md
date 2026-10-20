---
title: "LazySort AI: Drop the mess and let local AI sort it out"
published: false
tags: devchallenge, hf26challenge
---

*This is a submission for the Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady*

## What I Built

LazySort AI is a local-first organizer for the folder you keep avoiding. It scans files, extracts a bounded amount of useful text, and asks Gemma to propose meaningful categories and names. You review every proposal before anything moves.

It rewards laziness by replacing the repetitive loop of opening, identifying, renaming, and filing documents with one reviewable plan. It never deletes files, never lets the model operate the filesystem, and records successful moves so they can be undone.

## Demo

[ADD REAL VIDEO OR DEPLOYMENT LINK]

[ADD REAL SCREENSHOTS]

## Code

[ADD REAL GITHUB REPOSITORY URL]

## How I Built It

FastAPI serves a focused HTML/CSS/JavaScript dashboard and a small local API. A safe scanner collects metadata while ignoring dependency folders and symlinks. Bounded extractors support TXT, Markdown, PDF, DOCX, CSV, and JSON.

Gemma 3 4B runs through Ollama and returns a category, subcategory, descriptive filename, reason, and confidence as structured JSON. Pydantic validates the response. A malformed answer is retried once; a second failure becomes a low-confidence manual-review item.

The model only suggests components. Deterministic code rejects traversal, separators, absolute paths, control characters, reserved names, protected roots, changed extensions, and destinations outside the selected folder. Only operations approved in the UI are moved. Existing files receive a deterministic numeric suffix instead of being overwritten. Successful operations are logged, including during partial failure, and undo runs that log in reverse.

## Why Does Open Innovation Matter?

The files we procrastinate on are often the files we least want to upload: invoices, resumes, notes, and reports. With Ollama at localhost, Gemma processes extracted snippets on the user's machine. There is no mandatory proprietary model API, account, usage fee, or analytics pipeline, and the model can be swapped by configuration.

That is an advantage, not a claim of perfect privacy. A remotely configured Ollama endpoint receives extracted information. Local machines also vary in speed and memory, text extraction cannot read scanned PDFs without OCR, and open-weight models still make mistakes. The preview and validation layers exist because model output is never trusted as filesystem authority.

## My Agent Session

[ADD DEVRELAY SESSION, OR REMOVE THIS SECTION]

## The Lazy Payoff

- Files organized: [REAL NUMBER]
- Manual organization time: [MEASURED]
- LazySort workflow time: [MEASURED]
- Actions avoided: [MEASURED/EXPLAINED]
- Files deleted: 0

## Prize Categories

Best Use of Gemma
