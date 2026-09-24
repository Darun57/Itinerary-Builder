"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useWizardStore } from "@/features/wizard/store";
import {
  fetchCRMStats,
  fetchRevenueTrend,
  fetchProfitTrend,
} from "@/features/crm/api";
import type { DashboardStats, RevenueTrendDay } from "@/features/crm/types";

import { RevenuePipelineChart } from "./RevenuePipelineChart";
import { ProfitPipelineChart } from "./ProfitPipelineChart";

export function Dashboard() {
  const { setActiveView, apiKey, setApiKey } = useWizardStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [revenueTrend, setRevenueTrend] = useState<RevenueTrendDay[]>([]);
  const [profitTrend, setProfitTrend] = useState<RevenueTrendDay[]>([]);
  const [revenuePeriod, setRevenuePeriod] = useState<"monthly" | "7d">("monthly");
  const [profitPeriod, setProfitPeriod] = useState<"monthly" | "7d">("monthly");

  const loadData = useCallback(() => {
    fetchCRMStats().then(setStats).catch(() => {});
    fetchRevenueTrend(revenuePeriod).then(setRevenueTrend).catch(() => {});
    fetchProfitTrend(profitPeriod).then(setProfitTrend).catch(() => {});
  }, [revenuePeriod, profitPeriod]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="page active animate-in fade-in slide-in-from-bottom-4 duration-500" id="page-dashboard">
      <div className="welcome">
        <div>
          <h1>Welcome back, Darun</h1>
          <p>Here&apos;s what&apos;s happening across your itineraries today.</p>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div className="flex gap-2 relative">
            <input
              type="password"
              placeholder="Gemini API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="bg-white border border-gray-200 text-gray-900 px-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-[#14213D] focus:ring-2 focus:ring-[#14213D]/10 w-64 shadow-sm"
            />
            <button
              className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-800 rounded-xl text-sm font-medium transition-colors border border-gray-200 shadow-sm"
              onClick={() => {
                if (apiKey) alert("API Key connected securely!");
                else alert("Please enter an API Key first.");
              }}
            >
              Set Key
            </button>
          </div>
          <button
            className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 rounded-xl text-sm font-medium transition-colors border border-gray-200 shadow-sm"
            onClick={() => setActiveView("crm")}
          >
            <i className="ti ti-layout-dashboard" /> CRM
          </button>
          <button className="btn-gold" onClick={() => setActiveView("builder")}>
            <i className="ti ti-plus"></i>New itinerary
          </button>
        </div>
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))" }}>
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon" style={{ background: "rgba(212,175,55,.1)", color: "var(--gold)" }}><i className="ti ti-user-plus"></i></div>
            <span className="stat-trend trend-up">+{stats?.new_leads_today ?? 0} today</span>
          </div>
          <div className="stat-num">{stats?.total_leads ?? "—"}</div>
          <div className="stat-label">Total Leads</div>
        </div>
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon" style={{ background: "rgba(20,33,61,0.08)", color: "#14213D" }}><i className="ti ti-users"></i></div>
            <span className="stat-trend trend-up">{stats?.total_clients ?? 0} clients</span>
          </div>
          <div className="stat-num">{stats?.total_bookings ?? "—"}</div>
          <div className="stat-label">Total Bookings</div>
        </div>
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon" style={{ background: "rgba(63,191,127,.1)", color: "var(--green)" }}><i className="ti ti-checks"></i></div>
            <span className="stat-trend trend-up">{stats?.bookings_completed ?? 0} completed</span>
          </div>
          <div className="stat-num">{stats?.bookings_confirmed ?? "—"}</div>
          <div className="stat-label">Confirmed Bookings</div>
        </div>
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon" style={{ background: "rgba(212,175,55,.1)", color: "var(--gold)" }}><i className="ti ti-currency-rupee"></i></div>
            <span className="stat-trend trend-up">This month</span>
          </div>
          <div className="stat-num">
            {stats ? `\u20b9${Math.round(stats.revenue_this_month).toLocaleString()}` : "—"}
          </div>
          <div className="stat-label">Revenue Snapshot</div>
        </div>
        <div className="stat-card">
          <div className="stat-top">
            <div className="stat-icon" style={{ background: "rgba(16, 185, 129, 0.12)", color: "#10B981" }}>
              <i className="ti ti-chart-line"></i>
            </div>
            <span className="stat-trend trend-up" style={{ color: "#34D399" }}>
              {stats?.revenue_total && stats.profit_total
                ? `${((stats.profit_total / stats.revenue_total) * 100).toFixed(1)}% margin`
                : "Net Profit"}
            </span>
          </div>
          <div className="stat-num" style={{ color: "#34D399" }}>
            {stats?.profit_total !== undefined ? `\u20b9${Math.round(stats.profit_total).toLocaleString()}` : "—"}
          </div>
          <div className="stat-label">Net Profit (YTD)</div>
        </div>
      </div>

      {/* Row 1: Revenue Pipeline Chart */}
      <div style={{ marginBottom: "20px" }}>
        <RevenuePipelineChart
          data={revenueTrend}
          period={revenuePeriod}
          onPeriodChange={setRevenuePeriod}
          totalRevenue={stats?.revenue_total}
        />
      </div>

      {/* Row 2: Profit Pipeline Chart */}
      <div style={{ marginBottom: "20px" }}>
        <ProfitPipelineChart
          data={profitTrend}
          period={profitPeriod}
          onPeriodChange={setProfitPeriod}
          totalProfit={stats?.profit_total}
          totalRevenue={stats?.revenue_total}
        />
      </div>
    </div>
  );
}

