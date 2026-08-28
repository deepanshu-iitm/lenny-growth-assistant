function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineFormat(text: string) {
  return escapeHtml(text).replace(
    /\*\*(.+?)\*\*/g,
    "<strong>$1</strong>"
  );
}

export function markdownToHtml(md: string) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out: string[] = [];
  let inList = false;

  function closeList() {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      closeList();
      continue;
    }
    if (line.startsWith("### ")) {
      closeList();
      out.push(`<h3>${inlineFormat(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      closeList();
      out.push(`<h2>${inlineFormat(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      closeList();
      out.push(`<h1>${inlineFormat(line.slice(2))}</h1>`);
      continue;
    }
    if (line.startsWith("- ") || line.startsWith("* ")) {
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      out.push(`<li>${inlineFormat(line.slice(2))}</li>`);
      continue;
    }
    closeList();
    out.push(`<p>${inlineFormat(line)}</p>`);
  }
  closeList();
  return out.join("\n");
}
