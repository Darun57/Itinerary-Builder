"use client";
import React, { useEffect, useState, useCallback } from "react";
import type { Booking, Client } from "../../types";
import { fetchBookings, updateBooking, deleteBooking, fetchClients } from "../../api";
import { BookingForm } from "./BookingForm";
import { ProfitModal } from "./ProfitModal";
import { WhatsAppReminderModal } from "../reminders/WhatsAppReminderModal";

const COLUMNS = [
  { id: "inquiry", label: "Inquiry", color: "#9db4e8" },
  { id: "confirmed", label: "Confirmed", color: "#D4AF37" },
  { id: "on_trip", label: "On Trip", color: "#a78bfa" },
  { id: "completed", label: "Completed", color: "#3FBF7F" },
  { id: "cancelled", label: "Cancelled", color: "#e87878" },
];

export function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editBooking, setEditBooking] = useState<Booking | null>(null);
  const [profitBooking, setProfitBooking] = useState<Booking | null>(null);
  const [waBooking, setWaBooking] = useState<Booking | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, c] = await Promise.all([fetchBookings(), fetchClients()]);
      setBookings(b);
      setClients(c);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const moveStatus = async (booking: Booking, newStatus: string) => {
    const updates: any = { status: newStatus };
    if ((newStatus === "confirmed" || newStatus === "completed" || newStatus === "on_trip") && (!booking.amount_paid || booking.amount_paid === 0) && booking.total_price && booking.total_price > 0) {
      updates.amount_paid = booking.total_price;
    }
    await updateBooking(booking.id, updates);
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this booking?")) return;
    await deleteBooking(id);
    load();
  };

  const clientName = (id: number) => clients.find(c => c.id === id)?.full_name || "Unknown";

  if (loading) return <div className="crm-loading"><i className="ti ti-loader-2 crm-spin" /> Loading bookings...</div>;

  return (
    <div className="crm-page">
      <div className="crm-page-header">
        <div>
          <h2 className="crm-page-title"><i className="ti ti-calendar-check" /> Bookings Pipeline</h2>
          <p className="crm-page-sub">Move bookings across pipeline stages or change status directly</p>
        </div>
        <button className="btn-gold" onClick={() => { setEditBooking(null); setShowForm(true); }}>
          <i className="ti ti-plus" /> New Booking
        </button>
      </div>

      <div className="crm-kanban">
        {COLUMNS.map(col => {
          const colBookings = bookings.filter(b => b.status === col.id);
          return (
            <div key={col.id} className="crm-kanban-col">
              <div className="crm-kanban-col-header" style={{ borderColor: col.color }}>
                <span style={{ color: col.color }}>{col.label}</span>
                <span className="crm-kanban-count">{colBookings.length}</span>
              </div>
              <div className="crm-kanban-cards">
                {colBookings.length === 0 && (
                  <div className="crm-kanban-empty">No bookings</div>
                )}
                {colBookings.map(b => (
                  <div key={b.id} className="crm-kanban-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span className="crm-kanban-card-ref">{b.booking_ref}</span>
                      <select
                        className="crm-status-pill-select"
                        value={b.status}
                        onChange={(e) => moveStatus(b, e.target.value)}
                        style={{
                          background: "rgba(255,255,255,0.06)",
                          color: COLUMNS.find(c => c.id === b.status)?.color || "#D4AF37",
                          border: "1px solid #262B36",
                          borderRadius: "6px",
                          padding: "2px 6px",
                          fontSize: "11px",
                          fontWeight: 600,
                          cursor: "pointer"
                        }}
                      >
                        {COLUMNS.map(c => (
                          <option key={c.id} value={c.id} style={{ background: "#171A22", color: c.color }}>
                            {c.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="crm-kanban-card-name">{clientName(b.client_id)}</div>
                    <div className="crm-kanban-card-dest">
                      <i className="ti ti-map-pin" /> {b.destination || "—"}
                    </div>
                    {b.hotel_name && <div className="crm-kanban-card-hotel"><i className="ti ti-building" /> {b.hotel_name}</div>}
                    <div className="crm-kanban-card-dates">
                      {b.check_in && <span>{b.check_in}</span>}
                      {b.nights && <span> · {b.nights}N</span>}
                      {b.pax && <span> · {b.pax} pax</span>}
                    </div>
                    {b.total_price && (
                      <div className="crm-kanban-card-price">₹{b.total_price.toLocaleString()}</div>
                    )}
                    {b.profit !== undefined && b.profit !== null && b.profit > 0 ? (
                      <div
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "11px",
                          fontWeight: 700,
                          color: "#10B981",
                          background: "rgba(16, 185, 129, 0.12)",
                          border: "1px solid rgba(16, 185, 129, 0.25)",
                          borderRadius: "6px",
                          padding: "2px 7px",
                          marginTop: "4px",
                          cursor: "pointer",
                        }}
                        onClick={() => setProfitBooking(b)}
                        title="Click to edit profit"
                      >
                        <i className="ti ti-chart-line" /> Net Profit: ₹{b.profit.toLocaleString()}
                      </div>
                    ) : (
                      b.status === "completed" && (
                        <div
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            fontSize: "11px",
                            color: "#8E9BB0",
                            background: "rgba(255, 255, 255, 0.04)",
                            border: "1px dashed rgba(255, 255, 255, 0.15)",
                            borderRadius: "6px",
                            padding: "2px 7px",
                            marginTop: "4px",
                            cursor: "pointer",
                          }}
                          onClick={() => setProfitBooking(b)}
                          title="Click to record profit"
                        >
                          <i className="ti ti-plus" /> Add Profit
                        </div>
                      )
                    )}
                    <div className="crm-kanban-card-actions">
                      <button className="crm-btn-icon" onClick={() => { setEditBooking(b); setShowForm(true); }} title="Edit booking details">
                        <i className="ti ti-edit" />
                      </button>
                      <button
                        className="crm-move-btn"
                        style={{
                          color: "#10B981",
                          border: "1px solid rgba(16, 185, 129, 0.3)",
                          background: "rgba(16, 185, 129, 0.1)",
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                        }}
                        title="Record or update profit"
                        onClick={() => setProfitBooking(b)}
                      >
                        <i className="ti ti-currency-rupee" /> Profit
                      </button>
                      <button
                        className="crm-move-btn"
                        style={{
                          color: "#25D366",
                          border: "1px solid rgba(37, 211, 102, 0.3)",
                          background: "rgba(37, 211, 102, 0.1)",
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                        }}
                        title="Send WhatsApp trip reminder or message"
                        onClick={() => setWaBooking(b)}
                      >
                        <i className="ti ti-brand-whatsapp" /> WhatsApp
                      </button>
                      <div className="crm-kanban-move">
                        {COLUMNS.filter(c => c.id !== col.id).map(c => (
                          <button key={c.id} className="crm-move-btn" style={{ color: c.color }} title={`Move to ${c.label}`} onClick={() => moveStatus(b, c.id)}>
                            → {c.label}
                          </button>
                        ))}
                      </div>
                      <button className="crm-btn-delete" onClick={() => handleDelete(b.id)}>
                        <i className="ti ti-trash" /> Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {showForm && (
        <BookingForm
          booking={editBooking}
          clients={clients}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load(); }}
        />
      )}

      {profitBooking && (
        <ProfitModal
          booking={profitBooking}
          onClose={() => setProfitBooking(null)}
          onSaved={() => { setProfitBooking(null); load(); }}
        />
      )}

      {waBooking && (
        <WhatsAppReminderModal
          initialBooking={waBooking}
          initialClient={clients.find((c) => c.id === waBooking.client_id) || null}
          onClose={() => setWaBooking(null)}
          onSuccess={() => setWaBooking(null)}
        />
      )}
    </div>
  );
}

