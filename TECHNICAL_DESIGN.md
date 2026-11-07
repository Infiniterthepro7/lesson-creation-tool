# Technical design

## Architecture

The application is split into a thin Flask layer, a workflow coordinator, external adapters and a local persistence layer:

- **Flask (`app.py`)** validates inputs, serves the instructor UI and exposes project/retry/edit/export endpoints.
- **Pipeline (`lessontool/pipeline.py`)** runs four ordered stages: research → lesson generation → factual/research QC → instructional QC. Each stage records status, attempt count and error text.
- **Research adapters (`lessontool/search.py`)** query DuckDuckGo or Tavily for web pages, Google Books for books, and video search for YouTube learning resources. Page text is extracted when reachable.
- **LLM adapter (`lessontool/llm.py`)** supports Anthropic Messages and OpenAI-compatible Chat Completions APIs. The model is configured through environment variables, not hard-coded.
- **SQLite (`lessontool/store.py`)** persists project inputs, lesson content, sources, audit reports and edit history.
- **Exporter (`lessontool/exporter.py`)** produces Markdown, HTML or a ZIP bundle with the lesson, references, QC reports and project JSON.

## Why two QC passes?

The research/factual audit focuses on whether claims are supported by the retrieved sources, source quality, contradictions and evidence gaps. The instructional audit has a separate rubric: learning-objective alignment, clarity, sequencing, examples, practice and assessment. Keeping the reports separate makes it easier for an instructor to see whether a problem is about correctness or teaching quality.

## Reliability decisions

- Each stage is independently retryable; completed upstream work is not needlessly repeated.
- Instructor edits are stored as a new edit-history entry and are not overwritten by a background refresh.
- Missing API credentials activate a labelled demo mode rather than silently pretending a model ran.
- Research failure is represented as an empty source set and the factual QC flags that evidence limitation.
- The app runs locally and uses SQLite; no deployment is required for evaluation.

## Known prototype limitations

Search and extraction are best-effort and may be rate-limited. A search result is not proof that a source was fully read. The generated audit is an AI-assisted review, not an external fact-checking guarantee. The single-process background thread is suitable for a local demo, not concurrent production workloads.
