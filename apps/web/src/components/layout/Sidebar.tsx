"use client";

import React from "react";
import { useWizardStore } from "@/features/wizard/store";

export function Sidebar() {
  const { activeView, setActiveView } = useWizardStore();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">D</div>
        <div>
          <div className="brand-name">Darun Tourism</div>
          <div className="brand-sub">AI Studio</div>
        </div>
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

      <div className="nav-label">Records</div>
      <div className="nav-item"><i className="ti ti-users"></i>Customers</div>
      <div className="nav-item"><i className="ti ti-target-arrow"></i>Leads</div>
      <div className="nav-item"><i className="ti ti-building-skyscraper"></i>Hotels</div>
      <div className="nav-item"><i className="ti ti-ski-jumping"></i>Activities</div>
      <div className="nav-item"><i className="ti ti-plane"></i>Transport</div>
      <div className="nav-item"><i className="ti ti-file-text"></i>Generated PDFs</div>

      <div className="nav-label">Grow</div>
      <div className="nav-item"><i className="ti ti-address-book"></i>CRM</div>
      <div className="nav-item"><i className="ti ti-chart-bar"></i>Analytics</div>
      <div className="nav-item"><i className="ti ti-settings"></i>Settings</div>

      <div className="sidebar-footer">
        <div className="ai-mini"><span className="dot-live"></span>AI engine online</div>
      </div>
    </aside>
  );
}
