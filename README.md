# Lenny Growth Assistant

Internal chat for a product/growth team. It answers from Lenny’s public podcast and newsletter starter pack, can draft a Ship 30-style essay, and can open Markdown or HTML beside the chat.

There is no login. Everyone shares one demo user.

## What you need

- Docker (for Postgres)
- Python 3.10+
- Node 18+ (the UI is Vite + React)
- Git
- Optional: [Ollama](https://ollama.com) with `llama3.2`, **or** an OpenAI API key

## Run it

From the repo root, clone the public starter pack, then start Postgres:

```bash
git clone --depth 1 https://github.com/LennysNewsletter/lennys-newsletterpodcastdata.git data/lenny
docker compose up -d postgres
```

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env   # Windows
# cp ../.env.example .env   # macOS/Linux
```

Put your OpenAI key in `backend/.env` if you have one (`OPENAI_API_KEY=...`). Leave it blank to use snippets, or Ollama if that is running.

```bash
uvicorn app.main:app --reload --port 8000
```

In another terminal, ingest the archive (once):

```bash
# Windows PowerShell
Invoke-RestMethod -Method POST http://127.0.0.1:8000/admin/ingest

# macOS/Linux
curl -X POST http://127.0.0.1:8000/admin/ingest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

After `data/lenny` is cloned, you can start everything with:

```bash
docker compose up --build
```

Put `OPENAI_API_KEY` in `backend/.env`. The UI is still [http://localhost:5173](http://localhost:5173). Stop a local uvicorn on port 8000 first.

## Models

The sidebar toggles **Ollama** and **OpenAI**. That choice lives in memory: if uvicorn reloads, click the provider again.

| Choice | What happens |
| --- | --- |
| OpenAI, key set | Grounded written answers (`gpt-4o-mini` by default) |
| Ollama running | Same, via local `llama3.2` |
| Neither | Transcript snippets still come back. The app does not crash. |

## What to try

- `How did Duolingo grow?`
- `Write a Ship 30 essay about how Duolingo grew` — essay opens in the right-hand viewer
- `Make an HTML one-pager about how Duolingo grew` — HTML opens in the same viewer, in a sandbox with no scripts

Skills live in `skills/ship30/SKILL.md` and `skills/artifacts/SKILL.md`.

## Layout

- `backend/` — FastAPI, Postgres, retrieval, LLM calls
- `frontend/` — chat + artifact viewer
- `data/lenny/` — Lenny’s public starter pack (clone it as above)
- `skills/` — writing and HTML rules

## Environment

See `.env.example`. Copy it to `backend/.env`. Required vs optional:

- `DATABASE_URL` — required for a real run (default matches docker compose)
- `OPENAI_API_KEY` — optional
- `LLM_PROVIDER` — `ollama` or `openai` (the UI can override until the process restarts)

## Check it works

- `GET http://127.0.0.1:8000/health` returns ok
- `GET http://127.0.0.1:8000/ready` shows the database is up
- In the UI: one question, one Ship 30 essay, one HTML one-pager

If the database is down, start Postgres with `docker compose up -d postgres`. If answers are empty, run ingest again. If OpenAI does not write, put the key in `backend/.env` and restart uvicorn.
