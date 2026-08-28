import { FormEvent, useEffect, useState } from "react";

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

  async function loadChat(id: string) {
    const res = await fetch(`/sessions/${id}`);
    if (!res.ok) {
      setError("Could not load this chat");
      return;
    }
    const data = await res.json();
    setMessages(data.messages || []);
  }

  async function newChat() {
    const res = await fetch("/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New chat" }),
    });
    if (!res.ok) {
      setError("Could not create chat");
      return;
    }
    const session: Session = await res.json();
    setSessions((prev) => [session, ...prev]);
    setSelectedId(session.id);
    setMessages([]);
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || !draft.trim() || sending) return;
    setSending(true);
    setError(null);
    const res = await fetch(`/sessions/${selectedId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: draft.trim() }),
    });
    setSending(false);
    if (!res.ok) {
      setError("Could not send message");
      return;
    }
    const data = await res.json();
    setMessages((prev) => [...prev, data.user, data.assistant]);
    setDraft("");
  }

  useEffect(() => {
    loadSessions();
    loadConfig().catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedId) loadChat(selectedId);
    else setMessages([]);
  }, [selectedId]);

  return (
    <div className="shell">
      <aside>
        <p className="brand">Lenny Growth Assistant</p>
        <p className="badge">
          {provider} · {model}
        </p>
        <div className="providers">
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
        <button type="button" onClick={newChat}>
          New chat
        </button>
        {error && <p className="error">{error}</p>}
        <ul>
          {sessions.map((session) => (
            <li key={session.id}>
              <button
                type="button"
                className={session.id === selectedId ? "active" : ""}
                onClick={() => setSelectedId(session.id)}
              >
                {session.title}
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main>
        {!selectedId ? (
          <p className="empty">Pick a chat, or start a new one.</p>
        ) : (
          <>
            <div className="thread">
              {messages.length === 0 && (
                <p className="empty">Ask a product or growth question.</p>
              )}
              {messages.map((message) => (
                <article key={message.id} className={message.role}>
                  <p className="who">{message.role}</p>
                  <div className="body">{message.content}</div>
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
            </div>
            <form onSubmit={send}>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Ask about retention, PLG, hiring…"
                rows={3}
              />
              <button type="submit" disabled={sending}>
                {sending ? "Sending…" : "Send"}
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  );
}
