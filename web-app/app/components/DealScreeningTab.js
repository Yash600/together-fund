"use client";

import { useState } from "react";
import { streamSSE } from "../../lib/sse";
import MarkdownView from "./MarkdownView";

const API_URL = process.env.NEXT_PUBLIC_DEAL_SCREENING_URL || "http://localhost:8001";

export default function DealScreeningTab() {
  const [file, setFile] = useState(null);
  const [log, setLog] = useState([]);
  const [memo, setMemo] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function run() {
    if (!file || running) return;
    setRunning(true);
    setLog([]);
    setMemo("");
    setError("");
    setStatus("Running...");

    try {
      const formData = new FormData();
      formData.append("file", file);
      await streamSSE(
        `${API_URL}/api/deal-screening/analyze`,
        { method: "POST", body: formData },
        (event) => {
          if (event.type === "log") {
            setLog((prev) => [...prev, event]);
          } else if (event.type === "result") {
            setMemo(event.memo);
          }
        }
      );
      setStatus("Done");
    } catch (e) {
      setError(String(e.message || e));
      setStatus("");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2 className="tf-panel-title">Deal Screening</h2>
      <p className="tf-panel-desc">
        Upload a pitch deck PDF -- extracts structured claims, flags internal inconsistencies,
        scores fit against Together Fund's thesis, and drafts a first-pass screening memo.
      </p>

      <div className="tf-card">
        <div className="tf-field-row">
          <input
            className="tf-file-input"
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button className="tf-button" onClick={run} disabled={running || !file}>
            {running ? "Screening..." : "Screen Deck"}
          </button>
        </div>
      </div>

      {status && <div className="tf-status">{status}</div>}
      {error && <div className="tf-status error">Error: {error}</div>}

      <MarkdownView markdown={memo} />
    </div>
  );
}
