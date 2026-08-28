# Design — Lenny Growth Assistant

How the product should feel and why the UI is shaped this way. Requirements are in `PRD.md`. Implementation is in `architecture.md`.

## 1. Design problem

The user is not exploring a model. They are preparing something they may have to defend in a review: a claim from Lenny’s archive, then optionally a draft others can read.

If the interface looks like a generic chatbot, they will treat answers like chat. If it looks like a CMS, they will hunt for settings. The surface should feel like an **internal desk**: chats on the left, the conversation in the middle, the document on the right when there is one.

The visual language is editorial on purpose (paper, serif titles, rust accent). Lenny’s work is writing. The tool should look closer to a newsletter desk than to a developer console or a purple “AI” shell.

## 2. Who it is for, on screen

**The PM or growth lead** should be able to sit down and ask a question without reading a manual. They need to see:

- Which chat they are in
- What the assistant used (citations)
- When a document is ready (viewer)
- Which writer is active (OpenAI vs local), without being asked for an API key in the thread

**The engineer** needs a provider control and a clear empty state when a key is missing. That control lives in the sidebar, not in the composer. The composer is for the question, not for ops.

There is no account picker and no “new workspace.” One shared user keeps pairing and eval simple. That is a product cut, not a missing button.

## 3. Information architecture

Three regions, one job each:

| Region | Job | Scrolls |
|---|---|---|
| Sidebar | Identity, writer, session list | Chat list only |
| Main | Question and answer | Thread only |
| Viewer | The thing you might paste into a doc | Document only |

The shell is a locked viewport. Brand, writer toggle, thread title, and composer do not move when the user reads. Independent panes matter because essays are long; a page-level scroll would drag the session list away while they read.

**The viewer is not always there.** A split screen with an empty “artifacts go here” column teaches the wrong model: that every turn produces a file. Chat answers stay in the thread. The third column appears only when this session has a Markdown essay or an HTML page. Until then, the conversation gets the full width.

On a narrow viewport the regions stack. That is acceptable for this version; the product is designed for a laptop or monitor at a desk.

## 4. Core loops, as the user sees them

**Ask.** Landing screen with three starters that match the real jobs (a growth question, an essay, a one-pager). Clicking a starter creates a chat and sends. “New chat” is always available so people are not trapped on the welcome view.

**Read.** User messages sit as compact bubbles on the right. Assistant messages are document-like on the left: no chrome, citations as small chips under the body. Guest names ride on the chip when the corpus has them. The chips are not links into Substack in this version; they are proof of which title was used.

**Wait.** While the archive is searched and the writer runs, the thread shows the user text immediately and a single “Searching the archive and writing…” line. There is no token stream. The honest wait is better than a fake typing indicator on a two-minute essay.

**Leave with a file.** If the turn produced an artifact, the viewer opens on that document. The thread says the title was drafted and opened beside the chat. Duplicating a 1,250-word essay in both places would make the conversation unusable.

**Follow up.** Same composer, same session. The product should feel like continuing a conversation, not like filling a search box again. Session titles come from the first line so the list stays readable.

## 5. Asking for documents

The user should not pick “Essay” from a dropdown. They write it in English, the way they would Slack a colleague:

- Essay: “write / draft” plus “essay”, or “Ship 30”
- One-pager: “HTML”, “one-pager”, “landing page”, and similar

If both could apply, essay wins. That matches the more expensive, more specific ask.

The cost of keyword routing is that a clever phrasing might miss. The cost of a mode switcher is that the PM now has a control they did not ask for. This version prefers natural language and a small, documented set of markers (`architecture.md`). Starter prompts on the welcome screen teach the phrases that work.

## 6. Writer control

The segmented control is **Ollama | OpenAI**, with the active model name under the brand.

- It is an operator choice: quality path vs local path, not a personality picker.
- If OpenAI is selected and no key is configured, a short hint appears in the sidebar. The composer still works; answers fall back to snippets. Do not block send. Blocking would make the tool feel broken when the archive still has something to say.
- The choice persists on the API host for the life of that process (and across reload via `.runtime.json`). It is not a per-chat setting. Mixing writers inside one thread would make citations harder to reason about in this version.

Do not put temperature, system prompts, or “creative / precise” sliders in the UI. Those fight the grounded-or-silent rule.

## 7. Visual system

| Token | Choice | Why |
|---|---|---|
| UI sans | IBM Plex Sans | Readable, institutional, not a marketing font |
| Titles | Fraunces | Editorial, paired with Lenny-as-writing |
| Paper / panel | Warm off-white | Desk, not IDE |
| Accent | Rust | One action color (new chat, send, selected tab) |
| Sage | Citation chips | “This came from the archive,” distinct from the accent |
| User bubble | Warm gray | Secondary to the assistant’s prose |

Spacing is tight enough for a tool, loose enough to read long answers. Corners are slightly rounded. Focus rings use the rust accent. Scrollbars in the panes are quiet.

The mark is an “L” in a rust square. It is a placeholder brand, not a marketing site logo.

## 8. Artifact viewer

The viewer is a **reading surface**, not a code preview.

- Kind pill: Essay vs HTML.
- Title from the document (`# ` or `<title>` / `<h1>`).
- Extra artifacts in the same session are tabs. A chat can accumulate a one-pager and an essay; the user should not lose the first when they ask for the second.
- HTML: sandboxed iframe, note in the header that scripts do not run. The note is for trust, not for developers only.
- Markdown: escaped, then a small heading/list treatment so Ship 30 formatting is skimmable. Full CommonMark is out of scope; the skill already constrains the shape.

There is no download or “copy HTML” in this version. The job is to read and paste. Export can wait until people actually share these files.

## 9. Copy

Voice is plain and specific. Error strings say what failed (“Could not send message”), not “Something went wrong.” Refusal belongs in the assistant’s answer, in the archive’s voice of “this isn’t in the sources,” not as a red banner.

Composer placeholder: “Ask about retention, PLG, hiring…” — the domain, not “Message Lenny.” The product is not impersonating Lenny; it is using the archive.

Keyboard hint under the composer (Enter to send) is for desk use. Do not hide send behind an icon-only control.

## 10. Trust, made visible

| Mechanism | Where it shows up |
|---|---|
| Citations | Chips under the assistant message |
| Empty archive / no hits | Prose refusal, no fake chips |
| Model down | Snippets or an explicit line in the thread |
| HTML isolation | Sandbox + header note |
| Shared workspace | No avatar menu; one list of chats |

If a citation cannot be tied to a real source row, it must not appear. An unsourced chip is worse than none.

## 11. Accessibility and motion

- `lang="en"` on the document.
- Provider group has an accessible name.
- Composer has a visible label (visually hidden is acceptable if the placeholder is not the only name).
- Errors use `role="alert"`.
- Keyboard: all primary actions are buttons or a submit control; Enter sends in the textarea.
- Independent scrolling uses `overscroll-behavior: contain` so one pane does not chain-scroll another.

Reduced-motion extras and a dark theme are not in this version. The paper palette is the product, not a theme toggle.

## 12. Explicit non-goals in the UI

- Streaming tokens (would imply a different wait model and a different trust story)
- Per-message “regenerate” (re-ask in the same chat instead)
- Prompt library beyond the three starters
- File upload (the corpus is ingested by operators)
- Login wall
- Mobile-first navigation chrome

## 13. What to change later, if the eval demands it

- Deep links to a session, once there are real users
- A visible “from the archive” quote expand, if chips are not enough to defend a number
- Export (Markdown download) once essays leave the building
- Embeddings will not change the layout; they should only change hit quality
- A mode switcher only if keyword routing fails in real use

Until then, keep the desk: list, conversation, document. Add chrome only when a principle in the PRD is failing on screen.
