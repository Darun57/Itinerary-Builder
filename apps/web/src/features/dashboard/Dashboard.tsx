"use client";

import React from "react";
import { useWizardStore } from "@/features/wizard/store";

export function Dashboard() {
  const { setActiveView, apiKey, setApiKey } = useWizardStore();

  return (
    <div className="page active animate-in fade-in slide-in-from-bottom-4 duration-500" id="page-dashboard">
      <div className="welcome">
        <div>
          <h1>Welcome back, Ravi</h1>
          <p>Here's what's happening across your itineraries today.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className="flex gap-2 relative">
            <input 
              type="password" 
              placeholder="Gemini API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="bg-[#171A22] border border-[#262B36] text-[#EDEFF3] px-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-[#D4AF37] w-64"
            />
            <button 
              className="px-4 py-2 bg-[#262B36] hover:bg-[#333947] text-[#EDEFF3] rounded-xl text-sm font-medium transition-colors border border-[#333947]"
              onClick={() => {
                if(apiKey) alert("API Key connected securely!");
                else alert("Please enter an API Key first.");
              }}
            >
              Set Key
            </button>
          </div>
          <button className="btn-gold" onClick={() => setActiveView('builder')}><i className="ti ti-plus"></i>New itinerary</button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-top"><div className="stat-icon" style={{background:'rgba(212,175,55,.1)', color:'var(--gold)'}}><i className="ti ti-calendar-event"></i></div><span className="stat-trend trend-up">+12%</span></div>
          <div className="stat-num">28</div><div className="stat-label">Today's bookings</div>
        </div>
        <div className="stat-card">
          <div className="stat-top"><div className="stat-icon" style={{background:'rgba(20,33,61,.6)', color:'#9db4e8'}}><i className="ti ti-clock-hour-4"></i></div><span className="stat-trend trend-up">+4</span></div>
          <div className="stat-num">14</div><div className="stat-label">Pending itineraries</div>
        </div>
        <div className="stat-card">
          <div className="stat-top"><div className="stat-icon" style={{background:'rgba(63,191,127,.1)', color:'var(--green)'}}><i className="ti ti-sparkles"></i></div><span className="stat-trend trend-up">92%</span></div>
          <div className="stat-num">341</div><div className="stat-label">AI generations this month</div>
        </div>
        <div className="stat-card">
          <div className="stat-top"><div className="stat-icon" style={{background:'rgba(212,175,55,.1)', color:'var(--gold)'}}><i className="ti ti-currency-dollar"></i></div><span className="stat-trend trend-up">+18%</span></div>
          <div className="stat-num">$186K</div><div className="stat-label">Revenue snapshot</div>
        </div>
      </div>

      <div className="row-2">
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Revenue trend</span><span className="panel-link">Last 7 days</span></div>
          <div className="chart-bars">
            <div className="bar-col"><div className="bar" style={{height:'58%'}}></div><span className="bar-lbl">Mon</span></div>
            <div className="bar-col"><div className="bar" style={{height:'74%'}}></div><span className="bar-lbl">Tue</span></div>
            <div className="bar-col"><div className="bar" style={{height:'45%'}}></div><span className="bar-lbl">Wed</span></div>
            <div className="bar-col"><div className="bar" style={{height:'88%'}}></div><span className="bar-lbl">Thu</span></div>
            <div className="bar-col"><div className="bar" style={{height:'66%'}}></div><span className="bar-lbl">Fri</span></div>
            <div className="bar-col"><div className="bar" style={{height:'97%'}}></div><span className="bar-lbl">Sat</span></div>
            <div className="bar-col"><div className="bar" style={{height:'80%'}}></div><span className="bar-lbl">Sun</span></div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-head"><span className="panel-title">Recent activity</span></div>
          <div className="timeline-item"><div className="tl-dot"></div><div><div className="tl-text">Itinerary generated for Meera Shah</div><div className="tl-sub">Maldives · 6D5N · 2 min ago</div></div></div>
          <div className="timeline-item"><div className="tl-dot" style={{background:'#9db4e8'}}></div><div><div className="tl-text">Hotel confirmed at Soneva Fushi</div><div className="tl-sub">Booking #4471 · 18 min ago</div></div></div>
          <div className="timeline-item"><div className="tl-dot"></div><div><div className="tl-text">New lead: Arjun Patel, honeymoon</div><div className="tl-sub">Via website form · 1 hr ago</div></div></div>
          <div className="timeline-item"><div className="tl-dot" style={{background:'#3FBF7F'}}></div><div><div className="tl-text">PDF downloaded by consultant</div><div className="tl-sub">Kapoor family trip · 3 hrs ago</div></div></div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head"><span className="panel-title">Recent customers</span><span className="panel-link">View all</span></div>
        <div className="cust-row"><div className="cust-avatar">MS</div><div><div className="cust-name">Meera Shah</div><div className="cust-meta">Maldives · Honeymoon · 6D5N</div></div><span className="chip chip-gold">Itinerary ready</span></div>
        <div className="cust-row"><div className="cust-avatar">AP</div><div><div className="cust-name">Arjun Patel</div><div className="cust-meta">Sri Lanka · Family · 8D7N</div></div><span className="chip chip-navy">In progress</span></div>
        <div className="cust-row"><div className="cust-avatar">KF</div><div><div className="cust-name">Kapoor family</div><div className="cust-meta">Maldives · Group of 6 · 5D4N</div></div><span className="chip chip-gold">PDF sent</span></div>
      </div>
    </div>
  );
}
