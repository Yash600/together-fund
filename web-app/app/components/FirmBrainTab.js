"use client";

import { useState } from "react";
import { streamSSE } from "../../lib/sse";
import { mdToHtml } from "../../lib/markdown";

const API_URL = process.env.NEXT_PUBLIC_FIRM_BRAIN_URL || "http://localhost:8000";

// Deliberately generic -- we don't know the company name in whatever gets
// uploaded this session, so these can't reference a specific company.
const SAMPLE_QUERIES = [
  "What is this company about?",
  "What are the biggest risks?",
  "Summarize the traction and team",
  "What's the recommendation?",
];

function makeSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function FirmBrainTab() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]); // { id, role: 'user' | 'assistant', content, isError }
  const [running, setRunning] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  // One session_id per tab load, sent with every upload and query so the
  // backend can scope retrieval to only this tab's own uploads. A different
  // tab (different session_id) never sees these documents, and reloading
  // the page starts a brand new, empty session.
  const [sessionId] = useState(makeSessionId);
  const [sessionUploadCount, setSessionUploadCount] = useState(0);

  async function uploadDoc() {
    if (!uploadFile || uploading) return;
    setUploading(true);
    setUploadStatus(`Uploading ${uploadFile.name}...`);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("session_id", sessionId);
      const resp = await fetch(`${API_URL}/api/firm-brain/upload`, {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        const text = await resp.text().catch(() => "");
        throw new Error(`Upload failed (${resp.status}): ${text || resp.statusText}`);
      }
      const data = await resp.json();
      setSessionUploadCount(data.session_total_chunks || 0);
      setUploadStatus(
        `Added ${data.added_chunks} section(s) from "${data.filename}" to this session's knowledge base -- ` +
          `ask below and it'll answer only from what you've uploaded this session.`
      );
      setUploadFile(null);
    } catch (e) {
      setUploadStatus(`Error: ${String(e.message || e)}`);
    } finally {
      setUploading(false);
    }
  }

  async function run() {
    const q = query.trim();
    if (!q || running) return;

    setMessages((prev) => [...prev, { id: `${Date.now()}-u`, role: "user", content: q }]);
    setQuery(""); // clear the input immediately, like a normal chat app

    // Nothing uploaded this session yet -- don't even hit the backend, just
    // ask for a document like the backend would.
    if (sessionUploadCount === 0) {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-a`,
          role: "assistant",
          content: "Please upload a document above first, then ask your question.",
        },
      ]);
      return;
    }

    setRunning(true);

    let finalAnswer = null;
    try {
      await streamSSE(
        `${API_URL}/api/firm-brain/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, session_id: sessionId }),
        },
        (event) => {
          if (event.type === "answer") {
            finalAnswer = event.answer;
          }
        }
      );
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now()}-a`, role: "assistant", content: finalAnswer || "(no answer returned)" },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now()}-a`, role: "assistant", content: `Error: ${String(e.message || e)}`, isError: true },
      ]);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2 className="tf-panel-title">Firm Brain</h2>
      <p className="tf-panel-desc">
        For internal use during deal evaluation. Upload a document a partner or associate has
        already written about a company under review -- an investment memo, founder call notes,
        a due diligence summary, or a portfolio update -- and ask questions about it instead of
        re-reading the whole thing: traction, team, risks, thesis fit, whatever you need. Answers
        come only from what you've uploaded this session, nothing else, so treat this as a
        working copy of one document, not a firm-wide archive.
      </p>

      <div className="tf-card">
        <div className="tf-section-label">Add a document to the knowledge base</div>
        <div className="tf-field-row">
          <input
            className="tf-file-input"
            type="file"
            accept=".md,.txt,.pdf"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
          />
          <button className="tf-button" onClick={uploadDoc} disabled={uploading || !uploadFile}>
            {uploading ? "Uploading..." : "Add to Knowledge Base"}
          </button>
        </div>
        {uploadStatus && <div className="tf-status">{uploadStatus}</div>}
        <p style={{ fontSize: 13, color: "var(--tf-ink-soft)", margin: 0 }}>
          Accepts .md, .txt, or .pdf -- chunked, embedded, and scoped to this browser tab only.
          Nothing else is queried: no pre-loaded corpus, no other tab's uploads. Ask below only
          once you've uploaded something.
          {sessionUploadCount > 0 && (
            <> This session currently has {sessionUploadCount} chunk(s) uploaded.</>
          )}
        </p>
      </div>

      <div className="tf-card">
        <div className="tf-chat">
          {messages.length === 0 && (
            <div className="tf-chat-empty">Ask a question below to start the conversation.</div>
          )}
          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="tf-chat-msg tf-chat-user">
                {m.content}
              </div>
            ) : (
              <div
                key={m.id}
                className={`tf-chat-msg tf-chat-assistant tf-result${m.isError ? " error" : ""}`}
                dangerouslySetInnerHTML={{ __html: mdToHtml(m.content) }}
              />
            )
          )}
          {running && <div className="tf-chat-thinking">Thinking...</div>}
        </div>
      </div>

      <div className="tf-card">
        <div className="tf-field-row">
          <input
            className="tf-input"
            placeholder="Ask Firm Brain a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
          />
          <button className="tf-button" onClick={run} disabled={running}>
            {running ? "Thinking..." : "Ask"}
          </button>
        </div>
        <div className="tf-sample-links">
          {SAMPLE_QUERIES.map((q) => (
            <button key={q} className="tf-sample-chip" onClick={() => setQuery(q)}>
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
