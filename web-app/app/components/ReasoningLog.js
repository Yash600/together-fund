"use client";

export default function ReasoningLog({ entries }) {
  return (
    <div>
      <div className="tf-section-label">Reasoning trace</div>
      <div className="tf-log">
        {entries.length === 0 ? (
          <p className="tf-log-line tf-log-empty">Run the agent to see each step logged here in real time.</p>
        ) : (
          entries.map((e, i) => (
            <p className="tf-log-line" key={i}>
              <span className="tf-log-step">[{e.step}]</span> {e.detail}
              {e.data ? ` ${JSON.stringify(e.data)}` : ""}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
