/**
 * Minimal SSE-over-fetch client. Native EventSource only supports GET with no
 * custom body, but our backends stream over POST (file upload / JSON body),
 * so we read the response stream manually and split on the "data: ...\n\n"
 * SSE framing our three FastAPI apps emit.
 */
export async function streamSSE(url, options, onEvent) {
  const resp = await fetch(url, options);
  if (!resp.ok || !resp.body) {
    const text = await resp.text().catch(() => "");
    throw new Error(`Request failed (${resp.status}): ${text || resp.statusText}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const dataLines = part
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim());
      if (dataLines.length === 0) continue;
      const raw = dataLines.join("\n");
      if (!raw || raw === "{}") continue;
      try {
        onEvent(JSON.parse(raw));
      } catch {
        // ignore malformed/keepalive chunks
      }
    }
  }
}
