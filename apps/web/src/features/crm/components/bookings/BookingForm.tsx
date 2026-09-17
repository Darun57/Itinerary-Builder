"use client";
import React, { useState, useEffect } from "react";
import type { Booking, Client, Staff } from "../../types";
import { createBooking, updateBooking, fetchStaff } from "../../api";

interface Props { booking: Booking | null; clients: Client[]; onClose: () => void; onSaved: () => void; }

export function BookingForm({ booking, clients, onClose, onSaved }: Props) {
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    client_id: booking?.client_id?.toString() || "",
    destination: booking?.destination || "",
    hotel_name: booking?.hotel_name || "",
    trip_type: booking?.trip_type || "",
    check_in: booking?.check_in || "",
    check_out: booking?.check_out || "",
    nights: booking?.nights?.toString() || "",
    pax: booking?.pax?.toString() || "2",
    status: booking?.status || "inquiry",
    total_price: booking?.total_price?.toString() || "",
    amount_paid: booking?.amount_paid?.toString() || "0",
    profit: booking?.profit?.toString() || "",
    notes: booking?.notes || "",
    assigned_staff_id: booking?.assigned_staff_id?.toString() || "",
  });

  useEffect(() => { fetchStaff().then(setStaffList).catch(() => {}); }, []);
  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSave = async () => {
    if (!form.client_id) { alert("Please select a client"); return; }
    setSaving(true);
    try {
      const totalVal = form.total_price ? parseFloat(form.total_price) : null;
      let paidVal = parseFloat(form.amount_paid) || 0;
      if (paidVal === 0 && (form.status === "confirmed" || form.status === "completed" || form.status === "on_trip") && totalVal && totalVal > 0) {
        paidVal = totalVal;
      }
      const payload: any = {
        ...form,
        client_id: parseInt(form.client_id),
        nights: form.nights ? parseInt(form.nights) : null,
        pax: parseInt(form.pax) || 2,
        total_price: totalVal,
        amount_paid: paidVal,
        profit: form.profit ? parseFloat(form.profit) : 0,
        assigned_staff_id: form.assigned_staff_id ? parseInt(form.assigned_staff_id) : null,
      };
      if (booking) await updateBooking(booking.id, payload);
      else await createBooking(payload);
      onSaved();
    } catch (e: any) { alert(e.message); } finally { setSaving(false); }
  };

  return (
    <div className="crm-modal-overlay" onClick={onClose}>
      <div className="crm-modal" onClick={e => e.stopPropagation()}>
        <div className="crm-modal-header">
          <h3>{booking ? `Edit ${booking.booking_ref}` : "New Booking"}</h3>
          <button className="crm-modal-close" onClick={onClose}><i className="ti ti-x" /></button>
        </div>
        <div className="crm-modal-body">
          <div className="crm-form-grid">
            <div className="crm-form-group crm-span-2">
              <label>Client *</label>
              <select className="crm-input" value={form.client_id} onChange={e => set("client_id", e.target.value)}>
                <option value="">Select client</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.full_name}</option>)}
              </select>
            </div>
            <div className="crm-form-group"><label>Destination</label><input className="crm-input" value={form.destination} onChange={e => set("destination", e.target.value)} placeholder="Andaman Islands" /></div>
            <div className="crm-form-group"><label>Hotel</label><input className="crm-input" value={form.hotel_name} onChange={e => set("hotel_name", e.target.value)} /></div>
            <div className="crm-form-group"><label>Trip Type</label>
              <select className="crm-input" value={form.trip_type} onChange={e => set("trip_type", e.target.value)}>
                <option value="">Select type</option>
                {["honeymoon","family","adventure","group","solo","corporate"].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
              </select>
            </div>
            <div className="crm-form-group"><label>Status</label>
              <select className="crm-input" value={form.status} onChange={e => set("status", e.target.value)}>
                {["inquiry","confirmed","on_trip","completed","cancelled"].map(s => <option key={s} value={s}>{s.replace("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}</option>)}
              </select>
            </div>
            <div className="crm-form-group"><label>Check In</label><input className="crm-input" value={form.check_in} onChange={e => set("check_in", e.target.value)} placeholder="DD/MM/YYYY" /></div>
            <div className="crm-form-group"><label>Check Out</label><input className="crm-input" value={form.check_out} onChange={e => set("check_out", e.target.value)} placeholder="DD/MM/YYYY" /></div>
            <div className="crm-form-group"><label>Nights</label><input className="crm-input" type="number" min="1" value={form.nights} onChange={e => set("nights", e.target.value)} /></div>
            <div className="crm-form-group"><label>Pax</label><input className="crm-input" type="number" min="1" value={form.pax} onChange={e => set("pax", e.target.value)} /></div>
            <div className="crm-form-group"><label>Total Price (₹)</label><input className="crm-input" type="number" value={form.total_price} onChange={e => set("total_price", e.target.value)} /></div>
            <div className="crm-form-group"><label>Amount Paid (₹)</label><input className="crm-input" type="number" value={form.amount_paid} onChange={e => set("amount_paid", e.target.value)} /></div>
            <div className="crm-form-group"><label>Net Profit (₹)</label><input className="crm-input" type="number" placeholder="e.g. 45000" value={form.profit} onChange={e => set("profit", e.target.value)} style={{ borderColor: form.profit ? "#10B981" : undefined }} /></div>
            <div className="crm-form-group"><label>Assigned To</label>
              <select className="crm-input" value={form.assigned_staff_id} onChange={e => set("assigned_staff_id", e.target.value)}>
                <option value="">Unassigned</option>
                {staffList.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
              </select>
            </div>
            <div className="crm-form-group crm-span-2"><label>Notes</label><textarea className="crm-input crm-textarea" value={form.notes} onChange={e => set("notes", e.target.value)} rows={2} /></div>
          </div>
        </div>
        <div className="crm-modal-footer">
          <button className="crm-btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-gold" onClick={handleSave} disabled={saving}>
            {saving ? <><i className="ti ti-loader-2 crm-spin" /> Saving...</> : <>{booking ? "Update Booking" : "Create Booking"}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
