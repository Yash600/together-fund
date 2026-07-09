"use client";

// Renders a tool's step-by-step reasoning trace: what it was about to do,
// what it decided/retrieved, formatted as readable fields instead of a raw
// JSON dump -- works generically across all three tools' different log
// shapes (retrieved chunks, extracted claims, search results, scores, etc).

function renderPrimitive(v) {
  if (v === null || v === undefined || v === "") return "-";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(3);
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function renderField(val) {
  if (Array.isArray(val)) {
    if (val.length === 0) return <span className="tf-log-val">(none)</span>;
    if (typeof val[0] === "object" && val[0] !== null) {
      return (
        <div className="tf-log-items">
          {val.map((item, i) => (
            <div className="tf-log-item" key={i}>
              {Object.entries(item)
                .map(([k, v]) => `${k}: ${renderPrimitive(v)}`)
                .join("  ·  ")}
            </div>
          ))}
        </div>
      );
    }
    return <span className="tf-log-val">{val.map(renderPrimitive).join(", ")}</span>;
  }
  if (val !== null && typeof val === "object") {
    return (
      <div className="tf-log-items">
        {Object.entries(val).map(([k, v]) => (
          <div className="tf-log-item" key={k}>
            <b>{k.replace(/_/g, " ")}:</b> {renderPrimitive(v)}
          </div>
        ))}
      </div>
    );
  }
  return <span className="tf-log-val">{renderPrimitive(val)}</span>;
}

export default function ReasoningLog({ entries, emptyText }) {
  return (
    <div className="tf-log">
      {!entries || entries.length === 0 ? (
        <div className="tf-log-empty">
          {emptyText || "Run it to see each step logged here as it happens -- what it's about to do, what it retrieved, what it decided."}
        </div>
      ) : (
        entries.map((e, i) => (
          <div className="tf-log-entry" key={i}>
            <div className="tf-log-head">
              <span className="tf-log-step">{e.step}</span>
              <span className="tf-log-detail">{e.detail}</span>
            </div>
            {e.data && Object.keys(e.data).length > 0 && (
              <div className="tf-log-data">
                {Object.entries(e.data).map(([key, val]) => (
                  <div className="tf-log-field" key={key}>
                    <span className="tf-log-key">{key.replace(/_/g, " ")}</span>
                    {renderField(val)}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
