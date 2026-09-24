"use client";
import React, { useState, useEffect } from "react";
import type { Booking, Client, Lead, ReminderType } from "../../types";
import {
  sendReminderNow,
  scheduleReminder,
  previewReminderTemplate,
  fetchReminderTemplates,
} from "../../api";

interface WhatsAppReminderModalProps {
  onClose: () => void;
  onSuccess?: () => void;
  initialBooking?: Booking | null;
  initialClient?: Client | null;
  initialLead?: Lead | null;
  initialPhone?: string;
  initialName?: string;
}

const DEFAULT_TEMPLATES = [
  { value: "pre_trip", label: "🌴 Pre-Trip Reminder (3 days before check-in)" },
  { value: "payment", label: "💳 Payment Pending Reminder" },
  { value: "followup", label: "🌟 Post-Trip Follow-up & Review" },
  { value: "inquiry", label: "💬 New Lead / Inquiry Follow-up" },
  { value: "custom", label: "✍️ Custom Message" },
];

export function WhatsAppReminderModal({
  onClose,
  onSuccess,
  initialBooking,
  initialClient,
  initialLead,
  initialPhone = "",
  initialName = "",
}: WhatsAppReminderModalProps) {
  // Determine client details
  const resolvedName =
    initialName ||
    initialClient?.full_name ||
    initialLead?.full_name ||
    initialBooking?.client?.full_name ||
    "";

  const resolvedPhone =
    initialPhone ||
    initialClient?.phone ||
    initialLead?.phone ||
    initialBooking?.client?.phone ||
    "";

  const [phone, setPhone] = useState(resolvedPhone);
  const [clientName, setClientName] = useState(resolvedName);
  const [reminderType, setReminderType] = useState<ReminderType>(
    initialBooking
      ? "pre_trip"
      : initialLead
      ? "inquiry"
      : "custom"
  );
  const [customText, setCustomText] = useState("");
  const [messageBody, setMessageBody] = useState("");
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Generate preview when type or targets change
  useEffect(() => {
    let active = true;
    async function updatePreview() {
      setPreviewLoading(true);
      try {
        const res = await previewReminderTemplate({
          reminder_type: reminderType,
          booking_id: initialBooking?.id,
          lead_id: initialLead?.id,
          client_id: initialClient?.id,
          custom_message: customText || undefined,
        });
        if (active) {
          setMessageBody(res.preview);
        }
      } catch (err) {
        // Fallback local preview
        if (active) {
          if (reminderType === "custom") {
            setMessageBody(`Hi ${clientName || "Client"}! 👋\n\n${customText || "Enter your custom message here."}\n\n— *Goa Darun Tours and Travels*`);
          } else if (reminderType === "pre_trip") {
            setMessageBody(
              `Hi ${clientName || "Valued Client"}! 🌴\n\nYour trip to *${
                initialBooking?.destination || "Goa"
              }* is coming up soon!\n📅 Check-in: *${
                initialBooking?.check_in || "Upcoming"
              }*\n🏨 Hotel: *${initialBooking?.hotel_name || "Hotel Stay"}*\n\nReply here for any assistance.\n— *Goa Darun Tours and Travels*`
            );
          } else {
            setMessageBody(`Hi ${clientName || "Client"}!\n\nThis is a notification from Goa Darun Tours and Travels.\n\n— *Goa Darun Tours and Travels*`);
          }
        }
      } finally {
        if (active) setPreviewLoading(false);
      }
    }

    updatePreview();
    return () => {
      active = false;
    };
  }, [reminderType, customText, initialBooking, initialLead, initialClient, clientName]);

  const handleSendOrSchedule = async (immediate: boolean) => {
    if (!phone.trim()) {
      setStatusMsg({ type: "error", text: "Please enter a valid phone number." });
      return;
    }
    if (!messageBody.trim()) {
      setStatusMsg({ type: "error", text: "Message body cannot be empty." });
      return;
    }
    if (!immediate && !scheduledAt) {
      setStatusMsg({ type: "error", text: "Please choose a scheduled date and time." });
      return;
    }

    setLoading(true);
    setStatusMsg(null);

    try {
      const payload = {
        phone_number: phone,
        client_name: clientName || undefined,
        client_id: initialClient?.id || initialBooking?.client_id || undefined,
        lead_id: initialLead?.id || undefined,
        booking_id: initialBooking?.id || undefined,
        reminder_type: reminderType,
        message_body: messageBody,
        scheduled_at: immediate ? undefined : new Date(scheduledAt).toISOString(),
      };

      if (immediate) {
        await sendReminderNow(payload);
        setStatusMsg({
          type: "success",
          text: "WhatsApp message sent successfully!",
        });
      } else {
        await scheduleReminder(payload);
        setStatusMsg({
          type: "success",
          text: `Reminder scheduled for ${new Date(scheduledAt).toLocaleString()}!`,
        });
      }

      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
      }, 1400);
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Failed to process reminder." });
    } finally {
      setLoading(false);
    }
  };

  const openWhatsAppWeb = () => {
    const cleanPhone = phone.replace(/[^0-9]/g, "");
    const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(messageBody)}`;
    window.open(url, "_blank");
  };

  return (
    <div className="crm-modal-backdrop animate-in fade-in duration-200">
      <div
        className="crm-modal-card"
        style={{
          maxWidth: "680px",
          width: "95vw",
          borderRadius: "16px",
          background: "linear-gradient(145deg, #16181F 0%, #111318 100%)",
          border: "1px solid rgba(212, 175, 55, 0.25)",
          boxShadow: "0 24px 64px rgba(0, 0, 0, 0.6)",
          padding: "28px",
          color: "#F3F4F6",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "rgba(37, 211, 102, 0.15)",
                border: "1px solid rgba(37, 211, 102, 0.35)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#25D366",
                fontSize: "22px",
              }}
            >
              <i className="ti ti-brand-whatsapp" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: "19px", fontWeight: 700, color: "#FFF" }}>
                Compose WhatsApp Message
              </h3>
              <p style={{ margin: 0, fontSize: "12px", color: "#8E9BB0" }}>
                Send or schedule personalized WhatsApp messages to travelers
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="crm-btn-icon"
            style={{ fontSize: "18px", color: "#8E9BB0", cursor: "pointer" }}
          >
            <i className="ti ti-x" />
          </button>
        </div>

        {/* Status Notification */}
        {statusMsg && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              marginBottom: "16px",
              fontSize: "13px",
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: statusMsg.type === "success" ? "rgba(37, 211, 102, 0.15)" : "rgba(239, 68, 68, 0.15)",
              border: `1px solid ${statusMsg.type === "success" ? "rgba(37, 211, 102, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
              color: statusMsg.type === "success" ? "#25D366" : "#EF4444",
            }}
          >
            <i className={`ti ti-${statusMsg.type === "success" ? "check" : "alert-circle"}`} />
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Two-Column Form and Preview */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.1fr", gap: "20px", marginBottom: "22px" }}>
          {/* Controls Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div>
              <label style={{ display: "block", fontSize: "12px", color: "#8E9BB0", marginBottom: "5px", fontWeight: 600 }}>
                Client Name
              </label>
              <input
                type="text"
                className="crm-input"
                placeholder="Client Name"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", borderRadius: "8px" }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", color: "#8E9BB0", marginBottom: "5px", fontWeight: 600 }}>
                WhatsApp Number <span style={{ color: "#D4AF37" }}>*</span>
              </label>
              <input
                type="text"
                className="crm-input"
                placeholder="+91 98765 43210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", borderRadius: "8px" }}
              />
              <span style={{ fontSize: "10px", color: "#6B7280", marginTop: "3px", display: "block" }}>
                Accepts 10-digit Indian numbers or full E.164 (+91...)
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", color: "#8E9BB0", marginBottom: "5px", fontWeight: 600 }}>
                Message Template
              </label>
              <select
                className="crm-input"
                value={reminderType}
                onChange={(e) => setReminderType(e.target.value as ReminderType)}
                style={{ width: "100%", padding: "8px 12px", borderRadius: "8px" }}
              >
                {DEFAULT_TEMPLATES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {reminderType === "custom" && (
              <div>
                <label style={{ display: "block", fontSize: "12px", color: "#8E9BB0", marginBottom: "5px", fontWeight: 600 }}>
                  Custom Content
                </label>
                <textarea
                  className="crm-input"
                  rows={3}
                  placeholder="Write your custom message text..."
                  value={customText}
                  onChange={(e) => setCustomText(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", resize: "none" }}
                />
              </div>
            )}

            {/* Schedule Toggle */}
            <div
              style={{
                marginTop: "4px",
                padding: "10px",
                borderRadius: "8px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            >
              <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "12px" }}>
                <input
                  type="checkbox"
                  checked={isScheduled}
                  onChange={(e) => setIsScheduled(e.target.checked)}
                />
                <span style={{ fontWeight: 600, color: "#D4AF37" }}>
                  <i className="ti ti-clock" /> Schedule for a future date/time
                </span>
              </label>

              {isScheduled && (
                <div style={{ marginTop: "10px" }}>
                  <input
                    type="datetime-local"
                    className="crm-input"
                    value={scheduledAt}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    style={{ width: "100%", padding: "6px 10px", borderRadius: "6px", fontSize: "12px" }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* WhatsApp Live Bubble Preview */}
          <div style={{ display: "flex", flexDirection: "column" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#8E9BB0", marginBottom: "5px", fontWeight: 600 }}>
              Live WhatsApp Preview
            </label>
            <div
              style={{
                flex: 1,
                borderRadius: "12px",
                background: "#0B141A", // Official WhatsApp Web dark bg
                border: "1px solid #1F2C34",
                padding: "16px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                minHeight: "260px",
                position: "relative",
              }}
            >
              {/* WhatsApp Bubble Header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  paddingBottom: "10px",
                  borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                  marginBottom: "12px",
                }}
              >
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    background: "#25D366",
                    color: "#000",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "14px",
                    fontWeight: 700,
                  }}
                >
                  D
                </div>
                <div>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "#E9EDEF" }}>
                    Goa Darun Tours and Travels
                  </div>
                  <div style={{ fontSize: "10px", color: "#8696A0" }}>Official WhatsApp</div>
                </div>
              </div>

              {/* Message Bubble */}
              <div
                style={{
                  background: "#005C4B", // WhatsApp outgoing dark green bubble
                  borderRadius: "8px 0px 8px 8px",
                  padding: "10px 12px",
                  color: "#E9EDEF",
                  fontSize: "12.5px",
                  lineHeight: "1.5",
                  whiteSpace: "pre-wrap",
                  alignSelf: "flex-end",
                  maxWidth: "92%",
                  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.3)",
                  position: "relative",
                }}
              >
                {previewLoading ? (
                  <span style={{ color: "#8696A0", fontStyle: "italic" }}>Rendering template preview...</span>
                ) : (
                  messageBody || "Message preview will appear here..."
                )}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    gap: "4px",
                    marginTop: "6px",
                    fontSize: "10px",
                    color: "rgba(255, 255, 255, 0.6)",
                  }}
                >
                  <span>Just now</span>
                  <i className="ti ti-checks" style={{ color: "#53BDEB" }} />
                </div>
              </div>

              {/* Notice */}
              <div style={{ marginTop: "14px", fontSize: "10.5px", color: "#8696A0", textAlign: "center" }}>
                🔒 End-to-end encrypted · Goa Darun Tours and Travels
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Direct WhatsApp Click-to-Chat */}
          <button
            type="button"
            onClick={openWhatsAppWeb}
            style={{
              background: "rgba(37, 211, 102, 0.12)",
              color: "#25D366",
              border: "1px solid rgba(37, 211, 102, 0.3)",
              padding: "8px 14px",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "12.5px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
            title="Open directly in WhatsApp Web or WhatsApp app with pre-filled message"
          >
            <i className="ti ti-brand-whatsapp" />
            <span>Open in WhatsApp Web</span>
          </button>

          <div style={{ display: "flex", gap: "10px" }}>
            <button
              type="button"
              className="crm-btn-secondary"
              onClick={onClose}
              disabled={loading}
              style={{ padding: "8px 16px", borderRadius: "8px" }}
            >
              Cancel
            </button>

            {isScheduled ? (
              <button
                type="button"
                className="btn-gold"
                onClick={() => handleSendOrSchedule(false)}
                disabled={loading}
                style={{
                  padding: "8px 20px",
                  borderRadius: "8px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  fontWeight: 600,
                }}
              >
                {loading ? <i className="ti ti-loader-2 crm-spin" /> : <i className="ti ti-calendar-time" />}
                <span>Schedule Reminder</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => handleSendOrSchedule(true)}
                disabled={loading}
                style={{
                  background: "linear-gradient(135deg, #25D366 0%, #128C7E 100%)",
                  color: "#FFFFFF",
                  border: "none",
                  padding: "8px 20px",
                  borderRadius: "8px",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 4px 14px rgba(37, 211, 102, 0.3)",
                }}
              >
                {loading ? <i className="ti ti-loader-2 crm-spin" /> : <i className="ti ti-send" />}
                <span>Send Message</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
