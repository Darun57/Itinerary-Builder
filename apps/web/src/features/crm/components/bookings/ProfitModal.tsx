"use client";

import React, { useState, useEffect } from "react";
import type { Booking } from "../../types";
import { updateBookingProfit } from "../../api";

interface ProfitModalProps {
  booking: Booking | null;
  allCompletedBookings?: Booking[];
  onSelectBooking?: (b: Booking) => void;
  onClose: () => void;
  onSaved: () => void;
}

export function ProfitModal({
  booking: initialBooking,
  allCompletedBookings = [],
  onClose,
  onSaved,
}: ProfitModalProps) {
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(
    initialBooking || (allCompletedBookings.length > 0 ? allCompletedBookings[0] : null)
  );

  const [profitInput, setProfitInput] = useState<string>(
    selectedBooking?.profit !== undefined && selectedBooking.profit !== null
      ? selectedBooking.profit.toString()
      : ""
  );
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (initialBooking) {
      setSelectedBooking(initialBooking);
      setProfitInput(
        initialBooking.profit !== undefined && initialBooking.profit !== null
          ? initialBooking.profit.toString()
          : ""
      );
    }
  }, [initialBooking]);

  const handleBookingChange = (id: number) => {
    const found = allCompletedBookings.find((b) => b.id === id) || null;
    setSelectedBooking(found);
    if (found) {
      setProfitInput(
        found.profit !== undefined && found.profit !== null
          ? found.profit.toString()
          : ""
      );
    }
  };

  const revenueBase =
    (selectedBooking?.total_price && selectedBooking.total_price > 0
      ? selectedBooking.total_price
      : selectedBooking?.amount_paid) || 0;

  const numericProfit = parseFloat(profitInput) || 0;
  const marginPct =
    revenueBase > 0 ? ((numericProfit / revenueBase) * 100).toFixed(1) : "0.0";

  const applyPreset = (pct: number) => {
    if (revenueBase > 0) {
      const calc = Math.round(revenueBase * (pct / 100));
      setProfitInput(calc.toString());
    }
  };

  const handleSave = async () => {
    if (!selectedBooking) {
      setErrorMsg("Please select a booking to update.");
      return;
    }
    const val = parseFloat(profitInput);
    if (isNaN(val) || val < 0) {
      setErrorMsg("Please enter a valid non-negative profit amount.");
      return;
    }

    setSaving(true);
    setErrorMsg(null);
    try {
      await updateBookingProfit(selectedBooking.id, val);
      onSaved();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update profit.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="crm-modal-overlay"
      onClick={onClose}
      style={{
        zIndex: 1000,
        backgroundColor: "rgba(3, 7, 18, 0.75)",
        backdropFilter: "blur(6px)",
      }}
    >
      <div
        className="crm-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "480px",
          width: "92%",
          background: "#0d1527",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: "18px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.75)",
          padding: "0",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "linear-gradient(180deg, #101c36 0%, #0d1527 100%)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#10B981",
                fontSize: "18px",
              }}
            >
              <i className="ti ti-currency-rupee" />
            </div>
            <div>
              <h3
                style={{
                  margin: 0,
                  fontSize: "17px",
                  fontWeight: 700,
                  color: "#FFFFFF",
                }}
              >
                Record Booking Profit
              </h3>
              <p style={{ margin: 0, fontSize: "12px", color: "#8E9BB0" }}>
                Manually record or update net profit for completed bookings
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#8E9BB0",
              cursor: "pointer",
              fontSize: "18px",
              padding: "4px",
            }}
          >
            <i className="ti ti-x" />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: "22px 24px" }}>
          {errorMsg && (
            <div
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#FCA5A5",
                padding: "10px 14px",
                borderRadius: "8px",
                fontSize: "13px",
                marginBottom: "16px",
              }}
            >
              {errorMsg}
            </div>
          )}

          {/* Booking Selector if list is provided and no specific booking selected */}
          {allCompletedBookings.length > 1 && (
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#A0AEC0",
                  display: "block",
                  marginBottom: "6px",
                }}
              >
                Select Booking:
              </label>
              <select
                className="crm-input"
                value={selectedBooking?.id || ""}
                onChange={(e) => handleBookingChange(Number(e.target.value))}
                style={{
                  width: "100%",
                  background: "#152037",
                  border: "1px solid #283754",
                  color: "#FFFFFF",
                  padding: "9px 12px",
                  borderRadius: "8px",
                  fontSize: "13px",
                }}
              >
                {allCompletedBookings.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.booking_ref || `Booking #${b.id}`} — {b.destination || "Trip"} (
                    ₹{(b.total_price || b.amount_paid || 0).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Booking Summary Box */}
          {selectedBooking && (
            <div
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "14px 16px",
                marginBottom: "18px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "8px",
                }}
              >
                <span
                  style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    color: "#D4AF37",
                  }}
                >
                  {selectedBooking.booking_ref || `Booking #${selectedBooking.id}`}
                </span>
                <span
                  style={{
                    fontSize: "11px",
                    textTransform: "uppercase",
                    padding: "2px 8px",
                    borderRadius: "10px",
                    background:
                      selectedBooking.status === "completed"
                        ? "rgba(16, 185, 129, 0.15)"
                        : "rgba(212, 175, 55, 0.15)",
                    color:
                      selectedBooking.status === "completed"
                        ? "#10B981"
                        : "#D4AF37",
                    fontWeight: 600,
                  }}
                >
                  {selectedBooking.status}
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  color: "#A0AEC0",
                  marginTop: "6px",
                }}
              >
                <span>Destination:</span>
                <strong style={{ color: "#E2E8F0" }}>
                  {selectedBooking.destination || "—"}
                </strong>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  color: "#A0AEC0",
                  marginTop: "4px",
                }}
              >
                <span>Total Booking Price:</span>
                <strong style={{ color: "#E2E8F0" }}>
                  ₹{(selectedBooking.total_price || selectedBooking.amount_paid || 0).toLocaleString()}
                </strong>
              </div>
            </div>
          )}

          {/* Profit Amount Input */}
          <div style={{ marginBottom: "16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "6px",
              }}
            >
              <label
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#CBD5E1",
                }}
              >
                Profit Amount (₹) *
              </label>
              {revenueBase > 0 && (
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#10B981",
                  }}
                >
                  Margin: {marginPct}%
                </span>
              )}
            </div>

            <div style={{ position: "relative" }}>
              <span
                style={{
                  position: "absolute",
                  left: "14px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "#10B981",
                  fontWeight: 700,
                  fontSize: "16px",
                }}
              >
                ₹
              </span>
              <input
                type="number"
                min="0"
                step="500"
                value={profitInput}
                onChange={(e) => setProfitInput(e.target.value)}
                placeholder="e.g. 45000"
                style={{
                  width: "100%",
                  padding: "11px 14px 11px 32px",
                  background: "#152037",
                  border: "1px solid #2D3E60",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "15px",
                  fontWeight: 600,
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          </div>

          {/* Quick Presets */}
          {revenueBase > 0 && (
            <div style={{ marginBottom: "20px" }}>
              <div
                style={{
                  fontSize: "11px",
                  color: "#8E9BB0",
                  marginBottom: "8px",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                Quick Margin Presets
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {[10, 15, 20, 25, 30].map((pct) => (
                  <button
                    key={pct}
                    type="button"
                    onClick={() => applyPreset(pct)}
                    style={{
                      background: "rgba(16, 185, 129, 0.1)",
                      border: "1px solid rgba(16, 185, 129, 0.25)",
                      color: "#34D399",
                      padding: "5px 10px",
                      borderRadius: "7px",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background =
                        "rgba(16, 185, 129, 0.25)")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background =
                        "rgba(16, 185, 129, 0.1)")
                    }
                  >
                    {pct}% (₹{Math.round(revenueBase * (pct / 100)).toLocaleString()})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            background: "#0a1120",
          }}
        >
          <button
            type="button"
            onClick={onClose}
            className="crm-btn-ghost"
            style={{
              padding: "9px 18px",
              borderRadius: "9px",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{
              background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
              color: "#FFFFFF",
              border: "none",
              padding: "9px 22px",
              borderRadius: "9px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: saving ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 4px 14px rgba(16, 185, 129, 0.35)",
            }}
          >
            {saving ? (
              <>
                <i className="ti ti-loader-2 crm-spin" /> Saving...
              </>
            ) : (
              <>
                <i className="ti ti-check" /> Save Profit
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
