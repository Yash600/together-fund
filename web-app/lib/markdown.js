/**
 * Tiny markdown-to-HTML converter -- intentionally minimal (headers, bold,
 * links, bullet lists, paragraphs) rather than pulling in a full markdown
 * dependency, since the LLM output we render follows a predictable shape.
 */
export function mdToHtml(md) {
  if (!md) return "";
  const escapeHtml = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const lines = escapeHtml(md).split("\n");
  const html = [];
  let inList = false;

  const inline = (text) =>
    text
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const listMatch = line.match(/^[-*]\s+(.*)/);

    if (listMatch) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${inline(listMatch[1])}</li>`);
      continue;
    } else if (inList) {
      html.push("</ul>");
      inList = false;
    }

    if (/^###\s+/.test(line)) {
      html.push(`<h4>${inline(line.replace(/^###\s+/, ""))}</h4>`);
    } else if (/^##\s+/.test(line)) {
      html.push(`<h3>${inline(line.replace(/^##\s+/, ""))}</h3>`);
    } else if (/^#\s+/.test(line)) {
      html.push(`<h2>${inline(line.replace(/^#\s+/, ""))}</h2>`);
    } else if (line.trim() === "") {
      html.push("");
    } else {
      html.push(`<p>${inline(line)}</p>`);
    }
  }
  if (inList) html.push("</ul>");
  return html.join("\n");
}
