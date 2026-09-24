"use client";
import React, { useState } from "react";
import { LeadsPage } from "./leads/LeadsPage";
import { ClientsPage } from "./clients/ClientsPage";
import { BookingsPage } from "./bookings/BookingsPage";
import { RemindersPanel } from "./reminders/RemindersPanel";

type CRMView = "leads" | "clients" | "bookings" | "reminders";

const navItems: { id: CRMView; label: string; icon: string }[] = [
  { id: "leads", label: "Leads", icon: "ti-user-plus" },
  { id: "clients", label: "Clients", icon: "ti-users" },
  { id: "bookings", label: "Bookings", icon: "ti-calendar-check" },
  { id: "reminders", label: "WhatsApp Bot", icon: "ti-brand-whatsapp" },
];

interface CRMLayoutProps {
  onBack: () => void;
}

export function CRMLayout({ onBack }: CRMLayoutProps) {
  const [activeView, setActiveView] = useState<CRMView>("leads");

  const renderView = () => {
    switch (activeView) {
      case "leads": return <LeadsPage />;
      case "clients": return <ClientsPage />;
      case "bookings": return <BookingsPage />;
      case "reminders": return <RemindersPanel />;
    }
  };

  return (
    <div className="crm-layout">
      <div className="crm-sidebar">
        <div className="crm-sidebar-header">
          <button className="crm-back-btn" onClick={onBack}>
            <i className="ti ti-arrow-left" />
          </button>
          <div className="crm-sidebar-title">
            <span className="crm-logo-icon"><i className="ti ti-layout-dashboard" /></span>
            <span>CRM</span>
          </div>
        </div>
        <nav className="crm-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`crm-nav-item${activeView === item.id ? " active" : ""}`}
              onClick={() => setActiveView(item.id)}
            >
              <i className={`ti ${item.icon}`} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="crm-sidebar-footer">
          <div className="crm-sidebar-badge">
            <i className="ti ti-shield-check" />
            <span>Internal CRM</span>
          </div>
        </div>
      </div>
      <div className="crm-main">
        <div className="crm-content animate-in fade-in duration-300">
          {renderView()}
        </div>
      </div>
    </div>
  );
}
