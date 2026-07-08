"use client";

import { useState } from "react";
import { streamSSE } from "../../lib/sse";
import MarkdownView from "./MarkdownView";

const API_URL = process.env.NEXT_PUBLIC_FOUNDER_RESEARCH_URL || "http://localhost:8002";

export default function FounderResearchTab() {
  const [founder, setFounder] = useState("");
  const [company, setCompany] = useState("");
  const [log, setLog] = useState([]);
  const [brief, setBrief] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function run() {
    if (!founder.trim() || !company.trim() || running) return;
    setRunning(true);
    setLog([]);
    setBrief("");
    setError("");
    setStatus("Running...");

    try {
      await streamSSE(
        `${API_URL}/api/founder-research/analyze`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ founder_name: founder, company_name: company }),
        },
        (event) => {
          if (event.type === "log") {
            setLog((prev) => [...prev, event]);
          } else if (event.type === "result") {
            setBrief(event.brief);
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
      <h2 className="tf-panel-title">Founder Research</h2>
      <p className="tf-panel-desc">
        Give a founder and company name -- plans live web searches, verifies what's actually
        supported by the results, maps the US-India competitive landscape, and drafts a
        founder-market-fit brief with citations.
      </p>

      <div className="tf-card">
        <div className="tf-field-row">
          <input
            className="tf-input"
            placeholder="Founder name"
            value={founder}
            onChange={(e) => setFounder(e.target.value)}
          />
          <input
            className="tf-input"
            placeholder="Company name"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
          />
          <button className="tf-button" onClick={run} disabled={running}>
            {running ? "Researching..." : "Research"}
          </button>
        </div>
      </div>

      {status && <div className="tf-status">{status}</div>}
      {error && <div className="tf-status error">Error: {error}</div>}

      <MarkdownView markdown={brief} />
    </div>
  );
}
