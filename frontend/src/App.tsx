import ArtifactViewer, { Artifact } from "./ArtifactViewer";
import { markdownToHtml } from "./markdown";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type Session = {
  id: string;
  title: string;
  updated_at: string;
};

type Citation = {
  title: string;
  guest: string | null;
  path: string;
};

type Message = {
  id: string;
  role: string;
  content: string;
  citations: Citation[];
};

const STARTERS = [
  {
    label: "Growth question",
    text: "How did Duolingo grow?",
  },
  {
    label: "Ship 30 essay",
    text: "Write a Ship 30 essay about how Duolingo grew",
  },
  {
    label: "HTML one-pager",
    text: "Make an HTML one-pager about how Duolingo grew",
  },
];

function relativeTime(iso: string) {
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return "";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 45) return "just now";
  if (seconds < 3600) return `${Math.max(1, Math.floor(seconds / 60))}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  const days = Math.floor(seconds / 86400);
  return days === 1 ? "yesterday" : `${days}d ago`;
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.2");
  const [openaiReady, setOpenaiReady] = useState(false);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [artifactId, setArtifactId] = useState<string | null>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const thread = useRef<HTMLDivElement>(null);

  const current = sessions.find((session) => session.id === selectedId);
  const showViewer = Boolean(selectedId && artifacts.length);

  function applyConfig(data: {
    provider: string;
    chat_model: string;
    openai_configured?: boolean;
  }) {
    setProvider(data.provider);
    setModel(data.chat_model);
    setOpenaiReady(Boolean(data.openai_configured));
  }

  async function loadConfig() {
    const res = await fetch("/config");
    if (!res.ok) return;
    applyConfig(await res.json());
  }

  async function chooseProvider(next: string) {
    const res = await fetch("/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: next }),
    });
    if (!res.ok) {
      setError("Could not switch model provider");
      return;
    }
    applyConfig(await res.json());
  }

  async function loadSessions() {
    try {
      const res = await fetch("/sessions");
      if (!res.ok) throw new Error("Could not load chats");
      setSessions(await res.json());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load chats");
    }
  }

  async function openChat(id: string) {
    setSelectedId(id);
    setError(null);
    const res = await fetch(`/sessions/${id}`);
    if (!res.ok) {
      setError("Could not load this chat");
      return;
    }
    const data = await res.json();
    setMessages(data.messages || []);
    const next = data.artifacts || [];
    setArtifacts(next);
    setArtifactId(next.length ? next[next.length - 1].id : null);
  }

  async function createChat() {
    const res = await fetch("/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New chat" }),
    });
    if (!res.ok) {
      setError("Could not create chat");
      return null;
    }
    const session: Session = await res.json();
    setSessions((prev) => [session, ...prev]);
    setSelectedId(session.id);
    setMessages([]);
    setArtifacts([]);
    setArtifactId(null);
    setError(null);
    return session;
  }

  async function newChat() {
    const session = await createChat();
    if (session) {
      window.setTimeout(() => composer.current?.focus(), 0);
    }
  }

  async function postMessage(sessionId: string, text: string) {
    if (!text.trim() || sending) return;
    const content = text.trim();
    setSending(true);
    setError(null);
    setDraft("");
    setMessages((prev) => [
      ...prev,
      { id: "pending-user", role: "user", content, citations: [] },
    ]);
    const res = await fetch(`/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    setSending(false);
    if (!res.ok) {
      setMessages((prev) => prev.filter((message) => message.id !== "pending-user"));
      setDraft(content);
      setError("Could not send message");
      return;
    }
    const data = await res.json();
    setMessages((prev) => [
      ...prev.filter((message) => message.id !== "pending-user"),
      data.user,
      data.assistant,
    ]);
    if (data.session_title) {
      setSessions((prev) => {
        const next = prev.map((session) =>
          session.id === sessionId
            ? { ...session, title: data.session_title, updated_at: new Date().toISOString() }
            : session
        );
        const match = next.find((session) => session.id === sessionId);
        if (!match) return next;
        return [match, ...next.filter((session) => session.id !== sessionId)];
      });
    }
    if (data.artifacts?.length) {
      setArtifacts((prev) => [...prev, ...data.artifacts]);
      setArtifactId(data.artifacts[data.artifacts.length - 1].id);
    }
  }

  async function send(event?: FormEvent) {
    event?.preventDefault();
    if (!selectedId) return;
    await postMessage(selectedId, draft);
  }

  async function startWith(text: string) {
    if (selectedId) {
      await postMessage(selectedId, text);
      return;
    }
    const session = await createChat();
    if (session) await postMessage(session.id, text);
  }

  function onComposerKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  useEffect(() => {
    loadSessions();
    loadConfig().catch(() => {});
  }, []);

  useEffect(() => {
    const el = thread.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, sending, selectedId]);

  return (
    <div className={showViewer ? "shell with-viewer" : "shell"}>
      <aside>
        <div className="sidebar-top">
          <div className="brand-block">
            <span className="mark" aria-hidden="true">
              L
            </span>
            <div>
              <p className="brand">Lenny</p>
              <p className="brand-sub">Growth Assistant</p>
            </div>
          </div>
          <p className="badge">
            <span className={provider === "openai" && openaiReady ? "dot on" : "dot"} />
            {provider} · {model}
          </p>
          <div className="providers" role="group" aria-label="Model provider">
            <button
              type="button"
              className={provider === "ollama" ? "on" : ""}
              onClick={() => chooseProvider("ollama")}
            >
              Ollama
            </button>
            <button
              type="button"
              className={provider === "openai" ? "on" : ""}
              onClick={() => chooseProvider("openai")}
            >
              OpenAI
            </button>
          </div>
          {provider === "openai" && !openaiReady && (
            <p className="hint">No OpenAI key set. Answers will use transcript snippets.</p>
          )}
          <button type="button" className="new-chat" onClick={newChat}>
            New chat
          </button>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </div>
        <div className="sidebar-list">
          <p className="nav-label">Chats</p>
          <ul className="chats">
            {sessions.length === 0 && <li className="muted">No chats yet</li>}
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  className={session.id === selectedId ? "active" : ""}
                  onClick={() => openChat(session.id)}
                >
                  <span className="chat-title">{session.title}</span>
                  <span className="chat-time">{relativeTime(session.updated_at)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>
      <main>
        {!selectedId ? (
          <div className="welcome">
            <p className="eyebrow">Internal desk</p>
            <h1>Ask Lenny’s archive. Leave with something you can share.</h1>
            <p className="lede">
              Answers come from the public podcast and newsletter starter pack.
              Essays and one-pagers open beside the thread.
            </p>
            <ul className="starters">
              {STARTERS.map((item) => (
                <li key={item.text}>
                  <button type="button" onClick={() => startWith(item.text)}>
                    <span className="starter-label">{item.label}</span>
                    <span>{item.text}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <>
            <header className="thread-bar">
              <h1>{current?.title || "New chat"}</h1>
              {artifacts.length > 0 && (
                <p className="thread-meta">
                  {artifacts.length} {artifacts.length === 1 ? "artifact" : "artifacts"}
                </p>
              )}
            </header>
            <div className="thread" ref={thread}>
              {messages.length === 0 && !sending && (
                <div className="empty-thread">
                  <p>Ask a product or growth question, or start from a prompt.</p>
                  <ul className="starters compact">
                    {STARTERS.map((item) => (
                      <li key={item.text}>
                        <button type="button" onClick={() => startWith(item.text)}>
                          {item.text}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {messages.map((message) => (
                <article key={message.id} className={message.role}>
                  <p className="who">{message.role === "user" ? "You" : "Assistant"}</p>
                  {message.role === "assistant" ? (
                    <div
                      className="body md"
                      dangerouslySetInnerHTML={{ __html: markdownToHtml(message.content) }}
                    />
                  ) : (
                    <div className="body">{message.content}</div>
                  )}
                  {message.citations?.length > 0 && (
                    <ul className="cites">
                      {message.citations.map((cite, i) => (
                        <li key={i}>
                          {cite.title}
                          {cite.guest ? ` · ${cite.guest}` : ""}
                        </li>
                      ))}
                    </ul>
                  )}
                </article>
              ))}
              {sending && (
                <article className="assistant pending">
                  <p className="who">Assistant</p>
                  <p className="body">Searching the archive and writing…</p>
                </article>
              )}
            </div>
            <form onSubmit={send}>
              <label className="sr-only" htmlFor="composer">
                Message
              </label>
              <textarea
                id="composer"
                ref={composer}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={onComposerKey}
                placeholder="Ask about retention, PLG, hiring…"
                rows={3}
              />
              <div className="composer-row">
                <p className="hint">Enter to send · Shift+Enter for a new line</p>
                <button type="submit" disabled={sending || !draft.trim()}>
                  {sending ? "Sending…" : "Send"}
                </button>
              </div>
            </form>
          </>
        )}
      </main>
      {showViewer && (
        <ArtifactViewer
          artifacts={artifacts}
          selectedId={artifactId}
          onSelect={setArtifactId}
        />
      )}
    </div>
  );
}
