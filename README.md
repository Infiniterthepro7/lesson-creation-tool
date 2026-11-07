# LessonLab — AI-powered Lesson Creation Tool

A locally running Flask application that researches books, websites and YouTube videos; drafts a 45-minute lesson; runs two independent QC audits; and supports instructor editing, saving, retrying and export.

## Requirements
- Python 3.10+
- Internet access for live research (optional in demo mode)
- An API key for an OpenAI-compatible model or Anthropic for AI lesson generation and model-based QC

## Quick start (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add OPENAI_API_KEY (or configure Anthropic)
python app.py
```
Open http://127.0.0.1:5000.

## Quick start (macOS / Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add OPENAI_API_KEY (or configure Anthropic)
python app.py
```

**Demo mode:** The app starts without an API key. It creates a generic lesson structure and a clearly labelled preliminary QC result. Demo output is not subject-verified and must not be presented as fact-checked AI content. Live research depends on network availability. For a complete AI workflow configure an LLM key and use the research sources/QC reports to review the result.

## Configuration
See `.env.example`:
- `LLM_PROVIDER`: `openai` (OpenAI-compatible endpoint) or `anthropic`
- `LLM_MODEL`: model identifier supported by the selected provider
- `OPENAI_BASE_URL`: defaults to OpenAI; can point to another compatible endpoint
- `SEARCH_PROVIDER`: `ddgs` (no key) or `tavily`
- `TAVILY_API_KEY`: optional higher-quality search provider
- `DATA_DIR`: SQLite project database location

Do not commit `.env` or API keys.

## Workflow
1. Enter lesson title and measurable learning objective.
2. Research stage searches the web, Google Books and YouTube; fetches readable page text where possible.
3. Generation stage drafts a structured lesson with a 45-minute schedule, explanations, examples, applications and knowledge checks.
4. QC 1 independently audits factual support, source quality, consistency and evidence gaps.
5. QC 2 independently audits objective alignment, clarity, structure, examples, applications and assessment.
6. Review/edit the lesson, save changes and rerun QC after editing.
7. Export a ZIP containing Markdown lesson, references, both QC reports and project JSON. Markdown and HTML exports are also available by changing the export `format` query parameter.

## API
- `GET /api/projects` — list saved projects
- `POST /api/projects` — create and start workflow (`title`, `objective`)
- `GET /api/projects/<id>` — project and step status
- `POST /api/projects/<id>/retry` — retry `research`, `generate`, `qc1` or `qc2`
- `PUT /api/projects/<id>/lesson` — save instructor edits
- `GET /api/projects/<id>/export?format=zip|md|html` — export

## Sample inputs
The UI includes the task's required HTTP sample and a second SQL joins sample. `scripts/run_samples.py` can run both headlessly after configuring `.env`.

## Testing
```bash
python scripts/check_setup.py
python -m unittest discover -s tests -v
```
`check_setup.py` checks live integrations and therefore requires network access and an LLM API key. Unit tests use fakes and run offline.

## Design notes / limitations
- SQLite stores projects, generated content, QC reports and edit history locally.
- Pipeline stages run in a background thread. Each stage records status, attempts and error text; completed stages are skipped on retry.
- Research retrieval is best-effort. Search snippets and fetched pages are evidence inputs, not a guarantee of correctness. Review source URLs and primary documentation.
- QC reports are model-assisted audits, not formal proof. The factual layer must not be interpreted as exhaustive verification.
- YouTube search results may not expose transcripts. A video link is a supplementary resource, not evidence that the video was fully reviewed.
- This prototype is designed for local evaluation, not multi-user production deployment. Add authentication, CSRF protection, job queueing and stronger concurrency controls before public hosting.

## Repository structure
```text
app.py                  Flask routes and application factory
lessontool/config.py    Environment configuration
lessontool/llm.py       OpenAI-compatible / Anthropic client
lessontool/search.py    Web, book and video research adapters
lessontool/pipeline.py  Research → generation → two QC layers
lessontool/store.py     SQLite persistence
lessontool/exporter.py  Markdown, HTML and ZIP exports
templates/index.html    Single-page instructor workspace
static/                 UI styles and client logic
scripts/                 Setup and sample-run utilities
tests/                   Offline unit tests
```
