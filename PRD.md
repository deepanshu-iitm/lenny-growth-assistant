# Product requirements — Lenny Growth Assistant

Internal assistant for a product and growth team. It answers from Lenny Rachitsky’s podcast and newsletter archive and turns those answers into shareable writing, without asking people to learn models, prompts, or retrieval.

This document is the product contract. System shape is in `architecture.md`. How to run the stack is in `README.md`.

## 1. Problem

The team already treats Lenny’s archive as a source of judgment on retention, PLG, hiring, and growth loops. Using it in day-to-day work is slow:

- Transcripts and newsletters are long. People search Substack, skim, and paste fragments into a doc.
- Quotes lose their source. A week later nobody can defend where a number came from.
- Writing quality depends on who had time that afternoon. The same Duolingo or Superhuman story gets retold with invented tactics.

The assistant should sit where the work already happens: a chat. The user asks a product question, sees an answer grounded in the archive, and can leave with an essay or a one-pager without opening another tool.

## 2. Users

**Primary — product manager or growth lead.** They know the vocabulary. They will not configure embeddings, temperature, or prompt templates. They need something they can put in a review: a claim, a source, and optionally a draft.

**Secondary — another engineer on the team.** They will ingest a new dump of the archive, add a writing format, or swap the model provider. They should not have to reverse-engineer the product from code.

There is no end-customer surface in this version. There is no login. Everyone in the workspace shares one demo user so evaluation and pairing stay simple. Per-person history, SSO, and audit of who asked what are later, after the team trusts the answers.

## 3. Job to be done

When I am preparing a strategy note, a review, or a share-out, I want a trustworthy answer from Lenny’s archive and a draft I can send, so I do not spend the afternoon reconstructing a transcript by hand.

## 4. Principles

1. **Grounded or silent.** If the archive does not support the question, say so. Do not invent guests, companies, or statistics.
2. **Cite what you used.** Every supported answer names a real title from the corpus. Citations travel with the message, not as an afterthought.
3. **One turn to an artifact.** Asking for a Ship 30 essay or an HTML one-pager should open a document beside the chat in that turn.
4. **Skills are files.** Writing craft lives in `SKILL.md`, not in a hidden system prompt only the original author knows. A new format is a new file plus a thin router, not a new product.
5. **Degrade, do not crash.** If the model is unreachable, return archive snippets or a clear failure line. The session and the search path still work.
6. **Small internal tool, not a platform.** Sharing links, workspaces, and Docs export wait until grounded answer rate is real.

## 5. Success

**North star: grounded answer rate.** On a fixed set of product and growth questions that appear in the ingested corpus, at least 80% of replies must:

1. Cite a real source title from the archive
2. Contain no invented guest, company, or statistic
3. Refuse clearly when the archive does not support an answer

The eval set should be questions the team actually asks (growth loops, retention, hiring, specific companies that appear in the pack). Spot-check with names the corpus covers well (for example Duolingo) and with questions it cannot cover, to confirm refusal.

**Secondary: time to a useful artifact.** From “write a Ship 30 essay about X” or “make an HTML one-pager about X” to a document in the viewer in one turn, without a second tool or a copy-paste step.

We are not optimizing for model cleverness, token speed, or chat personality.

## 6. Scope

### In this version

- Independent chat sessions in Postgres, titled from the first user message
- Ingest of markdown transcripts and newsletters, chunking, search, citations (one source per hit)
- Follow-up turns: prior messages in the writing prompt; search also uses the last user question
- Two providers, switched in the UI: a cloud OpenAI-compatible API and a local Ollama endpoint
- Snippet fallback when the writer is missing or down
- Ship 30–style essays from `skills/ship30/SKILL.md`
- HTML one-pagers from `skills/artifacts/SKILL.md`
- Side viewer for Markdown and HTML; HTML cannot run scripts; the pane opens only when a document exists
- Docker Compose for Postgres, API, and UI; or API and UI run against Compose Postgres in development
- Structured logs for retrieval and writer failures (no secrets, no full prompts)
- Automated tests for health, chunking, ranking, essay vs HTML routing, HTML sanitizing, and both `index.json` shapes

### Out of this version

- Authentication, roles, or an audit log of who asked what
- Streaming tokens
- Vector embeddings in the serving path (the Postgres image can host them later)
- Anthropic Claude Agent SDK as the process runtime
- Multi-user workspaces, share URLs, export to Google Docs
- The paid full Lenny archive and an MCP server in front of it
- Legal, medical, or non-English use

### Why the agent SDK is not the runtime

Skills must work with whichever writer the operator chooses, including a local OpenAI-compatible server. Claude Agent SDK is an Anthropic-hosted agent loop. Putting the product inside that loop would split the stack: one path for Anthropic, another for everything else.

Routing is in FastAPI. Skills are markdown files loaded into the prompt. Writers speak HTTP (`/chat/completions` or Ollama `/api/chat`). If the team later standardizes on Anthropic, the skill files stay; only the loop behind `complete()` changes.

## 7. Corpus

The first corpus is Lenny’s public podcast and newsletter starter pack (markdown plus `index.json`). That pack is enough to prove the product. Swapping in a larger licensed dump should be ingest plus configuration (`DATA_DIR`), not a rewrite of chat, skills, or the UI.

If the configured data directory has no index, the app can ingest a small sample tree so the stack still boots. Production use expects the real pack.

## 8. Writing formats

**Chat answer.** Short, sourced, for a colleague sitting next to you. Excerpts only. No padding.

**Ship 30 essay.** The published craft: hook, headline formula, 1/3/1, claims that appear in the retrieved source. Target length is on the order of 1,250 words. If the archive is thin, the essay stays short. It must not invent tactics to hit a word count. “Ship 30” here is that craft applied to an internal share-out, not a 250-word atomic screenshot.

**HTML one-pager.** A single page the user can glance at in the viewer. No scripts, no third-party embeds, no form posts. Sanitized on the server; rendered in a sandboxed iframe.

## 9. Flows

1. **Ask.** The user starts a chat (or a starter prompt), asks a product or growth question. The system searches the archive, writes from excerpts, and shows citations under the reply.
2. **Refuse.** The archive does not support the question. The assistant says so and does not fabricate a source.
3. **Essay.** The user asks to write or draft a Ship 30 essay on a topic. Retrieval pulls more of the best-matching source. The skill file is applied. Markdown opens in the viewer. The thread itself gets a short confirmation, not a second copy of the full essay.
4. **One-pager.** Same retrieval path with the HTML skill. The viewer shows the page. Scripts do not run.
5. **Follow-up.** “Tell me more” / “what about retention” uses the last user question for search and prior turns for writing, in the same session.
6. **Switch writer.** The sidebar chooses OpenAI or Ollama. The choice is stored on the API host. If the key is missing or the local server is down, snippets still return.

## 10. Functional requirements

- Creating a session does not require a title; the first message names it.
- Messages persist with timestamps and citations.
- Artifacts persist with kind, title, and body, linked to the assistant message that produced them.
- Ingest is idempotent on file checksum. Updating the corpus is re-ingest, not a migration.
- Search prefers title and guest matches over generic body words so a company name beats the word “grow”.
- Essay and HTML routing is explicit (keywords in the user text). Ambiguous “essay” plus “html” prefers essay.
- Operators can list sources and run the same search the chat uses (`/admin/*`) without using the UI.
- `/health` does not require Postgres. `/ready` does.

## 11. Non-functional requirements

- **Trust** over latency. A slower sourced essay is better than a fast generic one.
- **Writer timeout** on the order of two minutes, enough for a long essay, not an overnight job.
- **Cost.** Default cloud model is a small chat model (`gpt-4o-mini` unless configured otherwise). No batch or eval jobs on a schedule in this version.
- **Isolation.** Generated HTML cannot execute in the parent origin.
- **Operability.** JSON logs for retrieve hit counts and writer failures. Compose or documented split-process run.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Hallucination | Write only from retrieved chunks. Prefer a short essay over invented tactics. |
| Keyword search misses paraphrase | Title-weighted ranking. Vectors are the upgrade when the eval set shows systematic misses. |
| Weak local model | Cloud writer is the quality path. Local writer is for air-gapped or offline use. Fallback is snippets. |
| Cost | Small default model, no streaming fan-out, no overnight jobs. |
| HTML breakout | Strip script, iframe, handlers, `javascript:`. Iframe `sandbox=""`. Markdown escaped before render. |
| Stale corpus | Checksum ingest. Re-run ingest after the dump changes. Boot ingest if the catalog is empty. |
| Unauthenticated admin | Suitable for a trusted internal network only. Do not publish `/admin` to the internet. |

## 13. Later, in order

1. Embeddings and pgvector when keyword ranking fails on paraphrase in the eval set.
2. Real users and SSO once answers are trusted.
3. Streaming if essay wait time becomes the complaint.
4. Optional Anthropic loop behind the same skills.
5. Licensed full archive as a data swap.

New content types remain new skill files. Do not introduce a second framework to add a memo or a slide outline.
