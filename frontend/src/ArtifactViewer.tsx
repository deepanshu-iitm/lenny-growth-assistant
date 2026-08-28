import { markdownToHtml } from "./markdown";

export type Artifact = {
  id: string;
  kind: string;
  title: string;
  content: string;
};

type Props = {
  artifacts: Artifact[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export default function ArtifactViewer({ artifacts, selectedId, onSelect }: Props) {
  const current = artifacts.find((item) => item.id === selectedId) || artifacts[artifacts.length - 1];

  if (!current) {
    return (
      <section className="viewer" aria-label="Artifact viewer">
        <p className="empty">Essays and HTML open here, beside the chat.</p>
      </section>
    );
  }

  return (
    <section className="viewer" aria-label="Artifact viewer">
      <header>
        <p className="who">{current.kind}</p>
        <h2>{current.title}</h2>
        {artifacts.length > 1 && (
          <ul className="tabs">
            {artifacts.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={item.id === current.id ? "active" : ""}
                  onClick={() => onSelect(item.id)}
                >
                  {item.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </header>
      {current.kind === "html" ? (
        <iframe
          className="html-frame"
          title={current.title}
          sandbox=""
          srcDoc={current.content}
        />
      ) : (
        <div
          className="md"
          dangerouslySetInnerHTML={{ __html: markdownToHtml(current.content) }}
        />
      )}
      <p className="hint">
        HTML runs in a sandbox with no scripts, forms, or same-origin access.
        Markdown is escaped before it is rendered.
      </p>
    </section>
  );
}
