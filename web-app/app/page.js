"use client";

import { useState } from "react";
import FirmBrainTab from "./components/FirmBrainTab";
import DealScreeningTab from "./components/DealScreeningTab";
import FounderResearchTab from "./components/FounderResearchTab";
import GemMark from "./components/GemMark";
import BigFooterMark from "./components/BigFooterMark";

const TABS = [
  { id: "firm-brain", label: "Firm Brain", render: () => <FirmBrainTab /> },
  { id: "deal-screening", label: "Deal Screening", render: () => <DealScreeningTab /> },
  { id: "founder-research", label: "Founder Research", render: () => <FounderResearchTab /> },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState(TABS[0].id);
  const active = TABS.find((t) => t.id === activeTab) || TABS[0];

  return (
    <main className="tf-shell">
      <div className="tf-header">
        <div>
          <div className="tf-wordmark">
            Together<span>.</span>tools
          </div>
        </div>
        <GemMark />
      </div>

      <div className="tf-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tf-tab ${tab.id === activeTab ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {active.render()}

      <BigFooterMark />
    </main>
  );
}
