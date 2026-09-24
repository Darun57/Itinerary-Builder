"use client";
import React, { useState, useEffect, useCallback } from "react";
import type { WhatsAppReminder, ReminderType } from "../../types";
import {
  fetchReminders,
  fetchReminderLogs,
  sendPendingReminder,
  markReminderSent,
  cancelReminder,
  deleteReminder,
  triggerAutoSchedule,
  syncCrmReminders,
} from "../../api";
import { WhatsAppReminderModal } from "./WhatsAppReminderModal";

export function RemindersPanel() {
  const [activeTab, setActiveTab] = useState<"pending" | "logs">("pending");
  const [reminders, setReminders] = useState<WhatsAppReminder[]>([]);
  const [logs, setLogs] = useState<WhatsAppReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [showModal, setShowModal] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [pendingList, logsList] = await Promise.all([
        fetchReminders("pending"),
        fetchReminderLogs(),
      ]);
      setReminders(pendingList);
      setLogs(logsList);
    } catch (err) {
      console.error("Failed to load reminders:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAutoScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await triggerAutoSchedule();
      setScanResult(res.message);
      loadData();
    } catch (err: any) {
      setScanResult("Error scanning: " + err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleSyncCrm = async () => {
    setSyncing(true);
    setScanResult(null);
    try {
      const res = await syncCrmReminders();
      setScanResult(res.message);
      loadData();
    } catch (err: any) {
      setScanResult("Error syncing: " + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleSendNow = async (id: number) => {
    try {
      await sendPendingReminder(id);
      loadData();
    } catch (err: any) {
      alert("Failed to send: " + err.message);
    }
  };

  const handleMarkSent = async (id: number) => {
    try {
      await markReminderSent(id);
      loadData();
    } catch (err: any) {
      alert("Failed to mark sent: " + err.message);
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm("Cancel this scheduled reminder?")) return;
    try {
      setReminders((prev) => prev.filter((r) => r.id !== id));
      await cancelReminder(id);
      loadData();
    } catch (err: any) {
      alert("Failed to cancel: " + err.message);
      loadData();
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this reminder record?")) return;
    try {
      setReminders((prev) => prev.filter((r) => r.id !== id));
      setLogs((prev) => prev.filter((r) => r.id !== id));
      await deleteReminder(id);
      loadData();
    } catch (err: any) {
      alert("Failed to delete: " + err.message);
      loadData();
    }
  };

  const currentList = activeTab === "pending" ? reminders : logs;

  const filteredList = currentList.filter((r) => {
    const matchSearch =
      (r.client_name || "").toLowerCase().includes(search.toLowerCase()) ||
      r.phone_number.includes(search) ||
      r.message_body.toLowerCase().includes(search.toLowerCase());
    const matchType = !typeFilter || r.reminder_type === typeFilter;
    return matchSearch && matchType;
  });

  const pendingCount = reminders.length;
  const sentCount = logs.filter((l) => l.status === "sent").length;
  const failedCount = logs.filter((l) => l.status === "failed").length;

  return (
    <div className="crm-page">
      {/* Page Header */}
      <div className="crm-page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 className="crm-page-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#25D366", fontSize: "24px" }}>
                <i className="ti ti-brand-whatsapp" />
              </span>
              WhatsApp Reminders
            </h2>
          </div>
          <p className="crm-page-sub">
            Send and schedule automated WhatsApp updates to your travelers.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
          <button
            onClick={handleAutoScan}
            disabled={scanning}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              color: "#E5E7EB",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              padding: "8px 14px",
              borderRadius: "8px",
              fontWeight: 500,
              fontSize: "13px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.15s ease",
            }}
            title="Scan upcoming bookings and auto-generate reminders"
          >
            {scanning ? <i className="ti ti-loader-2 crm-spin" /> : <i className="ti ti-robot" />}
            <span>{scanning ? "Scanning..." : "Scan Bookings"}</span>
          </button>

          <button
            onClick={handleSyncCrm}
            disabled={syncing}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              color: "#E5E7EB",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              padding: "8px 14px",
              borderRadius: "8px",
              fontWeight: 500,
              fontSize: "13px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.15s ease",
            }}
            title="Sync all phone numbers from Leads, Clients, and Bookings"
          >
            {syncing ? <i className="ti ti-loader-2 crm-spin" /> : <i className="ti ti-refresh" />}
            <span>{syncing ? "Syncing..." : "Sync Contacts"}</span>
          </button>

          <button
            onClick={() => setShowModal(true)}
            style={{
              background: "#25D366",
              color: "#FFFFFF",
              border: "none",
              padding: "8px 18px",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 2px 10px rgba(37, 211, 102, 0.3)",
              transition: "all 0.15s ease",
            }}
          >
            <i className="ti ti-plus" />
            <span>New Message</span>
          </button>
        </div>
      </div>

      {/* Auto-Scan Notification */}
      {scanResult && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: "8px",
            marginBottom: "16px",
            fontSize: "13px",
            background: "rgba(37, 211, 102, 0.12)",
            border: "1px solid rgba(37, 211, 102, 0.25)",
            color: "#25D366",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <i className="ti ti-info-circle" />
            <span>{scanResult}</span>
          </div>
          <button
            onClick={() => setScanResult(null)}
            style={{ background: "none", border: "none", color: "#25D366", cursor: "pointer" }}
          >
            <i className="ti ti-x" />
          </button>
        </div>
      )}

      {/* Simplified KPI Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", marginBottom: "20px" }}>
        <div
          style={{
            background: "#16181F",
            border: "1px solid #232731",
            borderRadius: "10px",
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: "12px", color: "#8E9BB0", marginBottom: "4px" }}>Pending Reminders</div>
            <div style={{ fontSize: "24px", fontWeight: 700, color: "#D4AF37" }}>{pendingCount}</div>
          </div>
          <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: "rgba(212, 175, 55, 0.12)", color: "#D4AF37", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px" }}>
            <i className="ti ti-clock" />
          </div>
        </div>

        <div
          style={{
            background: "#16181F",
            border: "1px solid #232731",
            borderRadius: "10px",
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: "12px", color: "#8E9BB0", marginBottom: "4px" }}>Delivered Messages</div>
            <div style={{ fontSize: "24px", fontWeight: 700, color: "#25D366" }}>{sentCount}</div>
          </div>
          <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: "rgba(37, 211, 102, 0.12)", color: "#25D366", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px" }}>
            <i className="ti ti-circle-check" />
          </div>
        </div>

        <div
          style={{
            background: "#16181F",
            border: "1px solid #232731",
            borderRadius: "10px",
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: "12px", color: "#8E9BB0", marginBottom: "4px" }}>Auto-Pilot Rules</div>
            <div style={{ fontSize: "15px", fontWeight: 600, color: "#9db4e8", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#25D366", display: "inline-block" }} />
              Active (Pre-Trip & Payment)
            </div>
          </div>
          <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: "rgba(157, 180, 232, 0.12)", color: "#9db4e8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px" }}>
            <i className="ti ti-robot" />
          </div>
        </div>
      </div>

      {/* Filter and Tab Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        {/* Navigation Tabs */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => setActiveTab("pending")}
            style={{
              padding: "7px 14px",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              background: activeTab === "pending" ? "#262B36" : "transparent",
              color: activeTab === "pending" ? "#D4AF37" : "#8E9BB0",
              border: activeTab === "pending" ? "1px solid rgba(212, 175, 55, 0.3)" : "1px solid transparent",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <i className="ti ti-clock" />
            <span>Pending</span>
            <span
              style={{
                background: "rgba(212, 175, 55, 0.2)",
                padding: "1px 6px",
                borderRadius: "10px",
                fontSize: "11px",
              }}
            >
              {pendingCount}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("logs")}
            style={{
              padding: "7px 14px",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              background: activeTab === "logs" ? "#262B36" : "transparent",
              color: activeTab === "logs" ? "#25D366" : "#8E9BB0",
              border: activeTab === "logs" ? "1px solid rgba(37, 211, 102, 0.3)" : "1px solid transparent",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <i className="ti ti-list-check" />
            <span>Sent History</span>
            <span
              style={{
                background: "rgba(37, 211, 102, 0.2)",
                padding: "1px 6px",
                borderRadius: "10px",
                fontSize: "11px",
              }}
            >
              {logs.length}
            </span>
          </button>
        </div>

        {/* Search & Filters */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <input
            type="text"
            className="crm-search"
            placeholder="Search traveler, phone, text..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: "230px", fontSize: "12.5px" }}
          />

          <select
            className="crm-input"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: "8px", fontSize: "12px" }}
          >
            <option value="">All Types</option>
            <option value="pre_trip">🌴 Pre-Trip</option>
            <option value="payment">💳 Payment</option>
            <option value="followup">🌟 Follow-up</option>
            <option value="inquiry">💬 Inquiry</option>
            <option value="custom">✍️ Custom</option>
          </select>
        </div>
      </div>

      {/* Reminders List */}
      {loading ? (
        <div className="crm-loading">
          <i className="ti ti-loader-2 crm-spin" /> Loading WhatsApp reminders...
        </div>
      ) : filteredList.length === 0 ? (
        <div className="crm-empty" style={{ padding: "40px 20px" }}>
          <i className="ti ti-brand-whatsapp" style={{ color: "#25D366", fontSize: "36px" }} />
          <p style={{ marginTop: "10px", color: "#8E9BB0" }}>
            {activeTab === "pending"
              ? "No pending reminders. Click 'Scan Bookings' or compose a new message."
              : "No sent message history yet."}
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {filteredList.map((r) => {
            const isPending = r.status === "pending";
            const cleanPhone = r.phone_number.replace(/[^0-9]/g, "");

            return (
              <div
                key={r.id}
                style={{
                  background: "#16181F",
                  border: "1px solid #232731",
                  borderRadius: "12px",
                  padding: "16px 20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                }}
              >
                {/* Header Row: Traveler details + Status */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "50%",
                        background: "rgba(37, 211, 102, 0.15)",
                        color: "#25D366",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "16px",
                        fontWeight: 700,
                      }}
                    >
                      {r.client_name ? r.client_name.charAt(0).toUpperCase() : "T"}
                    </div>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontWeight: 700, fontSize: "14px", color: "#FFFFFF" }}>
                          {r.client_name || "Traveler"}
                        </span>
                        <span
                          style={{
                            fontSize: "12px",
                            color: "#25D366",
                            fontWeight: 600,
                            background: "rgba(37, 211, 102, 0.08)",
                            padding: "2px 8px",
                            borderRadius: "6px",
                          }}
                        >
                          {r.phone_number}
                        </span>
                        <span
                          style={{
                            fontSize: "11px",
                            textTransform: "capitalize",
                            color: "#8E9BB0",
                            background: "rgba(255, 255, 255, 0.04)",
                            border: "1px solid rgba(255, 255, 255, 0.08)",
                            padding: "2px 8px",
                            borderRadius: "6px",
                          }}
                        >
                          {r.reminder_type.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        textTransform: "uppercase",
                        padding: "3px 10px",
                        borderRadius: "12px",
                        background: isPending ? "rgba(212, 175, 55, 0.12)" : "rgba(37, 211, 102, 0.12)",
                        color: isPending ? "#D4AF37" : "#25D366",
                        border: `1px solid ${isPending ? "rgba(212, 175, 55, 0.25)" : "rgba(37, 211, 102, 0.25)"}`,
                      }}
                    >
                      {r.status}
                    </span>
                  </div>
                </div>

                {/* Message Preview: Clean WhatsApp-style bubble */}
                <div
                  style={{
                    background: "rgba(37, 211, 102, 0.04)",
                    border: "1px solid rgba(37, 211, 102, 0.12)",
                    borderLeft: "3px solid #25D366",
                    borderRadius: "8px",
                    padding: "12px 16px",
                    color: "#E2E8F0",
                    fontSize: "13px",
                    lineHeight: "1.5",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {r.message_body}
                </div>

                {/* Bottom Bar: Timestamps + Simplified Actions */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", paddingTop: "4px" }}>
                  <div style={{ fontSize: "11.5px", color: "#8E9BB0", display: "flex", alignItems: "center", gap: "6px" }}>
                    {r.scheduled_at && (
                      <span>
                        <i className="ti ti-clock" /> Scheduled: {new Date(r.scheduled_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </span>
                    )}
                    {r.sent_at && (
                      <span>
                        <i className="ti ti-check" /> Sent: {new Date(r.sent_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </span>
                    )}
                  </div>

                  {/* Actions: Clean & Simple */}
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {isPending ? (
                      <>
                        <button
                          onClick={() => {
                            window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(r.message_body)}`, "_blank");
                            setTimeout(() => {
                              if (confirm("Opened WhatsApp! Did you send the message? Mark as Sent?")) {
                                handleMarkSent(r.id);
                              }
                            }, 600);
                          }}
                          style={{
                            background: "#25D366",
                            color: "#FFFFFF",
                            border: "none",
                            padding: "6px 14px",
                            borderRadius: "7px",
                            fontSize: "12.5px",
                            fontWeight: 600,
                            cursor: "pointer",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            boxShadow: "0 2px 6px rgba(37, 211, 102, 0.25)",
                          }}
                          title="Open WhatsApp with pre-filled message"
                        >
                          <i className="ti ti-brand-whatsapp" style={{ fontSize: "16px" }} />
                          <span>Send WhatsApp</span>
                        </button>

                        <button
                          onClick={() => handleMarkSent(r.id)}
                          style={{
                            background: "rgba(255, 255, 255, 0.05)",
                            color: "#C5CBD3",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            padding: "6px 12px",
                            borderRadius: "7px",
                            fontSize: "12px",
                            fontWeight: 500,
                            cursor: "pointer",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                          }}
                          title="Mark reminder as sent without opening WhatsApp"
                        >
                          <i className="ti ti-check" />
                          <span>Mark Sent</span>
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(r.message_body)}`, "_blank");
                        }}
                        style={{
                          background: "rgba(37, 211, 102, 0.08)",
                          color: "#25D366",
                          border: "1px solid rgba(37, 211, 102, 0.25)",
                          padding: "5px 12px",
                          borderRadius: "7px",
                          fontSize: "12px",
                          fontWeight: 500,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "5px",
                        }}
                      >
                        <i className="ti ti-brand-whatsapp" />
                        <span>Chat Again</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleDelete(r.id)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#EF4444",
                        opacity: 0.7,
                        padding: "6px 8px",
                        borderRadius: "6px",
                        fontSize: "14px",
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        transition: "opacity 0.15s ease",
                      }}
                      title="Delete this reminder"
                      onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
                      onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.7")}
                    >
                      <i className="ti ti-trash" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <WhatsAppReminderModal
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}

