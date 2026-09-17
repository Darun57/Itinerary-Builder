"use client";

import React from "react";
import { useWizardStore } from "@/features/wizard/store";

export function Topbar() {
  const { activeView, apiKey, setApiKey } = useWizardStore();
  const [showKeyInput, setShowKeyInput] = React.useState(false);
  
  const crumbText =
    activeView === "dashboard"
      ? "Dashboard"
      : activeView === "builder"
      ? "Itinerary Builder"
      : activeView === "marketing"
      ? "Marketing Hub"
      : "CRM";

  return (
    <div className="topbar">
      <div className="crumbs">
        <i className="ti ti-home" style={{ fontSize: '14px' }}></i> 
        <span><b>{crumbText}</b></span>
      </div>
      <div className="top-actions flex items-center gap-3">
        <div className="relative">
          <button 
            type="button"
            onClick={() => setShowKeyInput(!showKeyInput)}
            className={`ai-pill flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium cursor-pointer transition-all ${
              apiKey ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "bg-amber-500/10 text-amber-500 border border-amber-500/20"
            }`}
          >
            <i className="ti ti-key"></i>
            {apiKey ? "Gemini Key Active" : "Set Gemini Key"}
          </button>
          
          {showKeyInput && (
            <div className="absolute right-0 mt-2 w-80 p-4 rounded-xl bg-card border border-border shadow-xl z-50 animate-in fade-in slide-in-from-top-2">
              <div className="text-xs font-semibold mb-1 text-foreground">Google AI Studio API Key</div>
              <p className="text-[11px] text-muted-foreground mb-3">
                Paste your Gemini API key from AI Studio to connect reasoning models.
              </p>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full text-xs px-3 py-2 rounded-lg bg-background border border-input text-foreground focus:outline-none focus:ring-1 focus:ring-primary mb-3"
              />
              <button
                type="button"
                onClick={() => setShowKeyInput(false)}
                className="w-full text-xs py-1.5 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
              >
                Save & Close
              </button>
            </div>
          )}
        </div>

        <div className="ai-pill"><i className="ti ti-sparkles"></i>AI ready</div>
        <div className="icon-btn"><i className="ti ti-bell"></i><span className="ping"></span></div>
        <div className="avatar">D</div>
      </div>
    </div>
  );
}
