"use client";

import React, { useState, useMemo } from "react";
import type { RevenueTrendDay } from "@/features/crm/types";

interface ProfitPipelineChartProps {
  data: RevenueTrendDay[];
  period: "monthly" | "7d";
  onPeriodChange: (period: "monthly" | "7d") => void;
  totalProfit?: number;
  totalRevenue?: number;
  onOpenProfitModal?: () => void;
}

export function ProfitPipelineChart({
  data,
  period,
  onPeriodChange,
  totalProfit,
  totalRevenue,
  onOpenProfitModal,
}: ProfitPipelineChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  // Compute headline total profit (in full rupees)
  const displayTotal = useMemo(() => {
    if (totalProfit !== undefined && totalProfit > 0) {
      return totalProfit;
    }
    const sum = data.reduce((acc, curr) => acc + curr.amount, 0);
    return sum;
  }, [data, totalProfit]);

  // Calculate profit margin percentage vs total revenue
  const marginPct = useMemo(() => {
    if (totalRevenue && totalRevenue > 0 && displayTotal > 0) {
      return ((displayTotal / totalRevenue) * 100).toFixed(1);
    }
    return "22.5"; // default benchmark
  }, [displayTotal, totalRevenue]);

  // Calculate maximum value and clean tick steps in full rupees (NO 'k' or 'k rs')
  const { ceiling, ticks } = useMemo(() => {
    const maxAmount = Math.max(...data.map((d) => d.amount), 0);
    if (maxAmount <= 0) {
      return {
        ceiling: 50000,
        ticks: [50000, 37500, 25000, 12500, 0],
      };
    }
    const targetTicks = 4;
    const rawStep = maxAmount / targetTicks;
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
    const residual = rawStep / magnitude;
    let mult = 1;
    if (residual > 5) mult = 10;
    else if (residual > 2.5) mult = 5;
    else if (residual > 1.5) mult = 2;
    else mult = 1;

    const step = mult * magnitude;
    const ceil = Math.max(maxAmount, Math.ceil(maxAmount / step) * step);
    const tickList: number[] = [];
    for (let val = ceil; val >= 0; val -= step) {
      tickList.push(val);
    }
    if (tickList[tickList.length - 1] !== 0) {
      tickList.push(0);
    }
    return { ceiling: ceil, ticks: tickList };
  }, [data]);

  // Dimensions for SVG
  const width = 680;
  const height = 220;
  const paddingLeft = 85;
  const paddingRight = 30;
  const paddingTop = 25;
  const paddingBottom = 35;
  const plotWidth = width - paddingLeft - paddingRight;
  const plotHeight = height - paddingTop - paddingBottom;
  const bottomY = paddingTop + plotHeight;

  // Calculate coordinates of data points
  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.map((d, i) => {
      const x =
        data.length === 1
          ? paddingLeft + plotWidth / 2
          : paddingLeft + (i / (data.length - 1)) * plotWidth;
      const ratio = ceiling > 0 ? d.amount / ceiling : 0;
      const y = bottomY - ratio * plotHeight;
      return {
        ...d,
        x,
        y: Math.min(Math.max(y, paddingTop), bottomY),
      };
    });
  }, [data, ceiling, plotWidth, plotHeight, bottomY, paddingLeft, paddingTop]);

  // Generate smooth cubic Bézier spline
  const { splinePath, areaPath } = useMemo(() => {
    if (points.length === 0) return { splinePath: "", areaPath: "" };
    if (points.length === 1) {
      const p = points[0];
      return {
        splinePath: `M ${p.x - 20} ${p.y} L ${p.x + 20} ${p.y}`,
        areaPath: `M ${p.x - 20} ${p.y} L ${p.x + 20} ${p.y} L ${p.x + 20} ${bottomY} L ${p.x - 20} ${bottomY} Z`,
      };
    }

    let path = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
    const minY = Math.min(...points.map((p) => p.y));

    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2] || p2;

      const tension = 0.22;
      const cp1x = p1.x + (p2.x - p0.x) * tension;
      let cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      let cp2y = p2.y - (p3.y - p1.y) * tension;

      cp1y = Math.min(Math.max(cp1y, minY), bottomY);
      cp2y = Math.min(Math.max(cp2y, minY), bottomY);

      path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }

    const last = points[points.length - 1];
    const first = points[0];
    const area = `${path} L ${last.x.toFixed(1)} ${bottomY} L ${first.x.toFixed(1)} ${bottomY} Z`;

    return { splinePath: path, areaPath: area };
  }, [points, bottomY]);

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E5E7EB",
        borderRadius: "16px",
        padding: "24px 26px 20px",
        boxShadow: "0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
        position: "relative",
        overflow: "hidden",
        width: "100%",
      }}
    >
      {/* Top Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "16px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: "#059669",
              textTransform: "uppercase",
              marginBottom: "6px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                background: "#10B981",
                boxShadow: "0 0 8px #10B981",
              }}
            />
            PROFIT PIPELINE
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <span
              style={{
                fontSize: "30px",
                fontWeight: 700,
                color: "#111827",
                fontFamily: "var(--font-heading, Georgia, serif)",
                letterSpacing: "-0.02em",
              }}
            >
              ₹{Math.round(displayTotal)}
            </span>
            <span
              style={{
                fontSize: "14px",
                fontWeight: 600,
                color: "#6B7280",
                letterSpacing: "0.02em",
              }}
            >
              {period === "monthly" ? "YTD Profit" : "Last 7 Days"}
            </span>
          </div>
        </div>

        {/* Right Actions: Badge + Button + Period Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {onOpenProfitModal && (
            <button
              onClick={onOpenProfitModal}
              style={{
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid rgba(16, 185, 129, 0.35)",
                color: "#34D399",
                borderRadius: "9px",
                padding: "5px 12px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "5px",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = "rgba(16, 185, 129, 0.28)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = "rgba(16, 185, 129, 0.15)")
              }
              title="Manually record profit for completed bookings"
            >
              <i className="ti ti-plus" /> Record Profit
            </button>
          )}

          <div
            style={{
              background: "rgba(16, 185, 129, 0.12)",
              color: "#34D399",
              border: "1px solid rgba(16, 185, 129, 0.25)",
              padding: "5px 12px",
              borderRadius: "20px",
              fontSize: "12px",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>+{marginPct}% net margin</span>
          </div>

          <div
            style={{
              display: "flex",
              background: "#F3F4F6",
              border: "1px solid #E5E7EB",
              borderRadius: "10px",
              padding: "3px",
              gap: "2px",
            }}
          >
            <button
              onClick={() => onPeriodChange("monthly")}
              style={{
                padding: "4px 10px",
                borderRadius: "7px",
                fontSize: "11px",
                fontWeight: period === "monthly" ? 700 : 500,
                border: "none",
                cursor: "pointer",
                transition: "all 0.2s",
                background:
                  period === "monthly"
                    ? "linear-gradient(135deg, #10B981, #059669)"
                    : "transparent",
                color: period === "monthly" ? "#FFFFFF" : "#6B7280",
              }}
            >
              Monthly
            </button>
            <button
              onClick={() => onPeriodChange("7d")}
              style={{
                padding: "4px 10px",
                borderRadius: "7px",
                fontSize: "11px",
                fontWeight: period === "7d" ? 700 : 500,
                border: "none",
                cursor: "pointer",
                transition: "all 0.2s",
                background:
                  period === "7d"
                    ? "linear-gradient(135deg, #10B981, #059669)"
                    : "transparent",
                color: period === "7d" ? "#FFFFFF" : "#6B7280",
              }}
            >
              7 Days
            </button>
          </div>
        </div>
      </div>

      {/* SVG Chart Area */}
      <div style={{ position: "relative", width: "100%", height: "220px" }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: "100%", height: "100%", overflow: "visible" }}
        >
          <defs>
            {/* Soft emerald gradient fill */}
            <linearGradient id="profitAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.32" />
              <stop offset="65%" stopColor="#10B981" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
            </linearGradient>

            {/* Glowing emerald drop shadow for line */}
            <filter id="profitLineGlow" x="-10%" y="-20%" width="120%" height="150%">
              <feDropShadow
                dx="0"
                dy="3"
                stdDeviation="5"
                floodColor="#10B981"
                floodOpacity="0.5"
              />
            </filter>
          </defs>

          {/* Horizontal Gridlines & Y-Axis Labels (FULL RUPEES, NO 'k' or 'k rs') */}
          {ticks.map((tickVal) => {
            const ratio = ceiling > 0 ? tickVal / ceiling : 0;
            const y = bottomY - ratio * plotHeight;
            return (
              <g key={tickVal}>
                {/* Y Axis Label */}
                <text
                  x={paddingLeft - 12}
                  y={y + 4}
                  textAnchor="end"
                  fill="#9CA3AF"
                  fontSize="11px"
                  fontWeight="500"
                  fontFamily="inherit"
                >
                  ₹{Math.round(tickVal)}
                </text>
                {/* Grid Line */}
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="#E5E7EB"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
              </g>
            );
          })}

          {/* Area Fill */}
          {areaPath && (
            <path
              d={areaPath}
              fill="url(#profitAreaGrad)"
              style={{ transition: "d 0.5s ease" }}
            />
          )}

          {/* Spline Stroke Curve */}
          {splinePath && (
            <path
              d={splinePath}
              fill="none"
              stroke="#10B981"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#profitLineGlow)"
              style={{ transition: "d 0.5s ease" }}
            />
          )}

          {/* Vertical Hover Guides & Interactive Points */}
          {points.map((p, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <g key={p.date || idx}>
                {/* Vertical dash line on hover */}
                {isHovered && (
                  <line
                    x1={p.x}
                    y1={paddingTop}
                    x2={p.x}
                    y2={bottomY}
                    stroke="rgba(16, 185, 129, 0.4)"
                    strokeDasharray="3 3"
                    strokeWidth="1"
                  />
                )}

                {/* Visible dot when hovered or has significant amount */}
                {(isHovered || p.amount > 0) && (
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? 6 : 4}
                    fill="#34D399"
                    stroke="#FFFFFF"
                    strokeWidth={isHovered ? 3 : 2}
                    style={{ transition: "all 0.2s" }}
                  />
                )}

                {/* Transparent wider hit area for hover */}
                <rect
                  x={p.x - plotWidth / (points.length * 2)}
                  y={paddingTop}
                  width={plotWidth / points.length}
                  height={plotHeight + paddingBottom}
                  fill="transparent"
                  style={{ cursor: "pointer" }}
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />

                {/* X Axis Label */}
                <text
                  x={p.x}
                  y={bottomY + 22}
                  textAnchor="middle"
                  fill={isHovered ? "#111827" : "#9CA3AF"}
                  fontSize="12px"
                  fontWeight={isHovered ? "700" : "500"}
                  style={{ transition: "fill 0.2s" }}
                >
                  {p.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Interactive Floating Tooltip (NO 'k' or 'k rs' — full rupees) */}
        {hoveredIdx !== null && points[hoveredIdx] && (
          <div
            style={{
              position: "absolute",
              left: `${(points[hoveredIdx].x / width) * 100}%`,
              top: `${(points[hoveredIdx].y / height) * 100}%`,
              transform: "translate(-50%, -125%)",
              background: "rgba(255, 255, 255, 0.97)",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              backdropFilter: "blur(8px)",
              padding: "6px 12px",
              borderRadius: "8px",
              pointerEvents: "none",
              boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              whiteSpace: "nowrap",
              zIndex: 10,
            }}
          >
            <div style={{ fontSize: "11px", color: "#6B7280", marginBottom: "2px" }}>
              {points[hoveredIdx].label} Net Profit
            </div>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "#34D399" }}>
              ₹{Math.round(points[hoveredIdx].amount)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
