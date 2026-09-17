"use client";

import React from "react";
import { useWizardStore } from "@/features/wizard/store";

export function Sidebar() {
  const { activeView, setActiveView } = useWizardStore();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">V</div>
        <div className="brand-name">VELQAIRN</div>
      </div>

      <div className="nav-label">Workspace</div>
      <div
        className={`nav-item ${activeView === "dashboard" ? "active" : ""}`}
        onClick={() => setActiveView("dashboard")}
      >
        <i className="ti ti-layout-grid"></i>Dashboard
      </div>
      <div
        className={`nav-item ${activeView === "builder" ? "active" : ""}`}
        onClick={() => setActiveView("builder")}
      >
        <i className="ti ti-route"></i>Itinerary Builder<span className="nav-badge">3</span>
      </div>
      <div
        className={`nav-item ${activeView === "crm" ? "active" : ""}`}
        onClick={() => setActiveView("crm")}
      >
        <i className="ti ti-address-book"></i>CRM
      </div>
      <div
        className={`nav-item ${activeView === "marketing" ? "active" : ""}`}
        onClick={() => setActiveView("marketing")}
      >
        <i className="ti ti-speakerphone"></i>Marketing
      </div>

      <div className="sidebar-footer">
        <div className="ai-mini"><span className="dot-live"></span>AI engine online</div>
      </div>
    </aside>
  );
}
