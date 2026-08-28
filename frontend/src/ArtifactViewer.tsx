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

function kindLabel(kind: string) {
  if (kind === "html") return "HTML";
  if (kind === "markdown") return "Essay";
  return kind;
}

export default function ArtifactViewer({ artifacts, selectedId, onSelect }: Props) {
  const current = artifacts.find((item) => item.id === selectedId) || artifacts[artifacts.length - 1];

  if (!current) {
    return null;
  }

  return (
    <section className="viewer" aria-label="Artifact viewer">
      <header>
        <div className="viewer-heading">
          <p className="kind-pill">{kindLabel(current.kind)}</p>
          <p className="viewer-note">Sandboxed · no scripts</p>
        </div>
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
                  {kindLabel(item.kind)} · {item.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </header>
      <div className="viewer-body">
        {current.kind === "html" ? (
          <iframe
            className="html-frame"
            title={current.title}
            sandbox=""
            srcDoc={current.content}
          />
        ) : (
          <div
            className="md paper"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(current.content) }}
          />
        )}
      </div>
    </section>
  );
}
