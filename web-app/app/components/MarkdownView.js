"use client";

import { mdToHtml } from "../../lib/markdown";

export default function MarkdownView({ markdown }) {
  if (!markdown) return null;
  return (
    <div>
      <div className="tf-section-label">Result</div>
      <div className="tf-card tf-result" dangerouslySetInnerHTML={{ __html: mdToHtml(markdown) }} />
    </div>
  );
}
