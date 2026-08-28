# PRD — Lenny Growth Assistant

**Status:** working local demo. Remaining handoff: `design.md`, sanitized agent transcripts, recorded demo.

## User and problem

**Primary user:** a product manager or growth lead on an internal team. They already know retention, PLG, and hiring. They do not want to learn prompts, models, or retrieval.

**Job to be done:** get a trustworthy answer from Lenny’s podcast and newsletter archive, then turn that answer into something they can share — a Ship 30-style essay or a one-pager — without leaving the chat.

**Pain today:** the archive is long. People search Substack, skim transcripts, and paste quotes into a doc. Answers drift. Sources get lost. Writing quality depends on whoever had time that afternoon.

## Success metric

**Grounded answer rate.** For product/growth questions that appear in the ingested starter pack, a reply must:

1. Cite a real source title from the archive
2. Contain no invented guest, company, or statistic
3. Say so clearly when the archive does not support an answer

The bar for this take-home is the three demo prompts (a Duolingo question, a Ship 30 essay, an HTML one-pager), not an automated 20-question harness.

Secondary: time-to-first-useful-artifact. An essay or one-pager should appear in the viewer in one turn.

We are not optimizing for model cleverness. We are optimizing for “I can defend this in a product review.”

## Assumptions

- The public Lenny starter pack is enough to prove the product. The paid full archive is a later data swap, not a rebuild.
- One demo user is enough for an internal eval. Auth and per-seat history come after the team trusts the answers.
- Evaluators may not host a local 3B model. OpenAI is the reliable writing path; Ollama is optional.
- Users ask in English about product, growth, and hiring.
- “Ship 30 for 30” means the published craft (hooks, headline formula, 1/3/1, grounded claims), aimed at ~1,250 words, not a 250-word atomic screenshot. If the archive is thin, the essay stays short rather than inventing tactics.

## Scope

**In**

- Chat sessions in Postgres, named from the first user message
- Ingest markdown transcripts, chunk them, search, cite one source per hit
- Follow-up turns: prior messages go into the prompt; search also uses the last user question
- OpenAI and Ollama, switched in the UI, snippet fallback if the model is down
- Ship 30 essays from `skills/ship30/SKILL.md`
- HTML one-pagers from `skills/artifacts/SKILL.md`
- Artifact viewer beside chat; HTML is sandboxed; viewer only opens when there is a document
- One-command Docker Compose (Postgres + API + nginx UI)
- JSON logs for retrieve and LLM failures; pytest for health, ranking, routing, and HTML sanitizing

**Out, on purpose**

- Login, roles, audit log of who asked what
- Streaming tokens
- Vector embeddings (pgvector image is ready; keyword + title ranking ships first)
- Anthropic Claude Agent SDK as the process runtime
- Multi-user workspaces, sharing links, export to Google Docs
- The paid Lenny archive and MCP server

**Why the SDK is out of the runtime:** the local demo must also run on Ollama. Claude Agent SDK is an Anthropic-hosted agent loop. Wiring the product to that SDK would make the offline path a second codebase. Skills are files. Routing is keyword checks in FastAPI. Providers are OpenAI-compatible HTTP. If the team later standardizes on Anthropic, the skill files stay; only the loop changes.

## Flows

1. **Ask** — New chat or a starter prompt → search archive → model writes from excerpts only → citations under the reply.
2. **Refuse** — Question the archive cannot support → the assistant says so and does not invent a source.
3. **Essay** — User asks for a Ship 30 essay → retrieve more chunks from the best source → apply the skill → Markdown opens in the viewer.
4. **One-pager** — User asks for HTML → same retrieval → HTML skill → viewer iframe with `sandbox=""`.
5. **Switch model** — Sidebar Ollama / OpenAI. Choice is saved in `backend/.runtime.json` on the API host. If OpenAI has no key or Ollama is down, snippets still return.
6. **Follow-up** — “tell me more” uses the last user question for search and prior turns for writing.

## Acceptance criteria

- Clone, follow the README, run `docker compose up --build` (with `data/lenny` cloned and `OPENAI_API_KEY` in `backend/.env`), ask a Duolingo growth question, see a citation.
- `Write a Ship 30 essay about how Duolingo grew` produces a viewer document whose claims appear in that newsletter, not generic “build a community” filler.
- `Make an HTML one-pager about how Duolingo grew` renders beside chat. Script tags do not run.
- With no model running, the API still responds (snippets or a short “couldn’t reach the model” line).
- `GET /health` is up without Postgres; `GET /ready` is not.

## Risks

| Risk | What we do |
|---|---|
| Hallucination | Answer only from retrieved chunks. Essays may be shorter than 1,250 words rather than padded. |
| Keyword search misses | Title match is weighted above body. Proper names work; vague “how do we grow?” is weaker. Vectors are the upgrade. |
| Local model quality / RAM | Default writing path is OpenAI. Ollama is optional. |
| Cost | `gpt-4o-mini`, non-streaming, timeout 120s. |
| HTML breakout | Strip script/iframe/event handlers. Iframe `sandbox=""`. Markdown is escaped before render. |
| Stale archive | Ingest is idempotent on file checksum. Empty DB ingests on boot. Re-run `POST /admin/ingest` after updating `data/lenny`. |
| Provider toggle | Saved on the API filesystem. Recreating the API container without that file means click OpenAI again. |

## What is left

- `design.md` — UI and product-cut rationale
- Sanitized agent transcripts
- Camera-on demo of the three prompts

The system is a small internal tool, not a platform. New content types should be new skill files, not a new framework.
