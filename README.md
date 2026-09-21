# Job Application Agent — Extended

> A multi-agent AI system that analyzes a job description and generates an ATS-optimized, tailored CV and cover letter.

This project is a modified, extended version of [**AI-Powered Job Application Agent**](https://github.com/Ismail-2001/AI-Job-Application-Agent) by **Ismail Sajid** ([@Ismail-2001](https://github.com/Ismail-2001)), used and redistributed here under the terms of its MIT License. The original author's copyright notice is preserved unmodified in [LICENSE](LICENSE). None of the original design, prompts, or architecture in this credit section should be read as this repository's own invention — see [What Was Changed](#what-was-changed-vs-the-original) below for exactly what is new here.

**This repository does not claim to be the original creation of its maintainer.** It is a derivative work: the base multi-agent architecture, prompts, and web/CLI interface are Ismail Sajid's; the items listed below are additions built on top of that base.

---

## What This Project Does

Given a job description, the system:
1. Extracts structured requirements, skills, and ATS keywords (`JobAnalyzer` agent)
2. Calculates a compatibility score against your profile (`MatchCalculator`)
3. Rewrites your CV to emphasize matching experience (`CVCustomizer` agent)
4. Writes a tailored cover letter (`CoverLetterGenerator` agent)
5. Produces both as downloadable documents

## What Was Changed vs. the Original

These are the substantive changes made in this fork, each independently explainable:

### 1. LLM provider abstraction (`utils/llm_client.py`, `utils/llm_factory.py`)
The original had two independent, near-duplicate client classes (`DeepSeekClient`, `GeminiClient`) with copy-pasted JSON-parsing logic and mismatched method signatures — `GeminiClient.generate_content` didn't even accept `system_instruction` the way `DeepSeekClient` did. This fork introduces:
- An abstract `LLMClient` base class with a single shared `generate_json` / `_parse_json_safe` implementation.
- Both provider clients now subclass it and share one interface.
- A `create_llm_client()` factory that reads `LLM_PROVIDER` from the environment, so switching providers is a config change, not a code change.
- Fixed the Gemini system-instruction handling to use the SDK's model-level `system_instruction` parameter instead of silently ignoring it.

### 2. Application history (`utils/history_store.py`)
The original was fully stateless — every generated CV/cover letter overwrote the last, with no record of past runs (this was on the original repo's own roadmap as an unimplemented "Job History Tracking" item). This fork adds:
- A local SQLite-backed store (`data/history.db`) recording role, company, match score, and output file paths for every run.
- New API endpoints: `GET /api/history`, `GET /api/history/<id>`, `DELETE /api/history/<id>`.
- CLI runs (`main.py`) and web runs (`app.py`) both log to it.
- No new frontend UI was built for browsing history in this pass — it's API/CLI only for now.

### 3. PDF export (`utils/document_builder.py`)
The original only produced `.docx` files. This fork adds a parallel PDF pipeline (via `reportlab`) that mirrors the DOCX layout — `create_cv_pdf()` and `create_cover_letter_pdf()` — so every run now produces both formats.

### 4. Working Docker setup (`Dockerfile`, `docker-compose.yml`)
The original README documented Docker deployment instructions, but no `Dockerfile` existed in the repository. This fork adds a real, buildable `Dockerfile` (Python 3.11-slim, gunicorn) and `docker-compose.yml`.

### 5. Test suite (`tests/`)
The original shipped ad hoc manual scripts (`test_system.py`, `test_api.py`) that print pass/fail to the console rather than integrating with a test runner. This fork adds a `pytest` suite covering the agents (with a fake LLM client — no network calls), `MatchCalculator`, `DocumentBuilder` (both DOCX and PDF output), `HistoryStore`, and the provider factory.

### Removed / not carried over from the source repo
- The original author's personal data (`data/master_profile.json` — name, personal email, phone number) was **not** copied into this repository; only the anonymized `.template` file is included.
- A `.env.example` in the source repo contained what appeared to be a live, non-placeholder Google API key. This fork's `.env.example` contains placeholder values only.
- ~15 internal working-session/audit markdown files from the source repo (design session logs, IDE prompt files, implementation status reports) were not carried over, as they were development artifacts rather than user-facing documentation.

---

## Tech Stack

- **Python 3.10+**, Flask
- **DeepSeek** or **Google Gemini** as the LLM backend (pluggable via `LLM_PROVIDER`)
- `python-docx` + `reportlab` for document generation
- SQLite for local application history
- `pytest` for testing

## Installation & Setup

```bash
git clone <this-repo-url>
cd job-app-agent-extended

python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file from the template and fill in your own API key:

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=deepseek          # or "gemini"
DEEPSEEK_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here   # only needed if LLM_PROVIDER=gemini
```

Set up your profile:

```bash
python setup_profile.py
# or manually: cp data/master_profile.json.template data/master_profile.json
```

See [PROFILE_SETUP_GUIDE.md](PROFILE_SETUP_GUIDE.md) for details.

## Usage

**Web interface:**
```bash
python app.py
# open http://localhost:5000
```

**CLI:**
```bash
python main.py
```

**Docker:**
```bash
docker compose up --build
```

**Tests:**
```bash
pip install -r requirements-dev.txt
pytest
```

## API Reference (additions)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/history` | List recent applications, newest first |
| GET | `/api/history/<id>` | Get one application, including full stored job analysis |
| DELETE | `/api/history/<id>` | Delete an application record |

All other endpoints are as in the original project.

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) Ismail Sajid, original work. Modifications in this repository are made available under the same license.

## Attribution

- **Original project & architecture:** [Ismail Sajid](https://github.com/Ismail-2001) — [AI-Job-Application-Agent](https://github.com/Ismail-2001/AI-Job-Application-Agent)
- **Extended by:** [Sami123d](https://github.com/Sami123d)
