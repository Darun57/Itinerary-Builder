"use client";
import React, { useState, useEffect } from "react";
import type { Lead, Staff } from "../../types";
import { createLead, updateLead, fetchStaff } from "../../api";

interface Props {
  lead: Lead | null;
  onClose: () => void;
  onSaved: () => void;
}

export function LeadForm({ lead, onClose, onSaved }: Props) {
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: lead?.full_name || "",
    email: lead?.email || "",
    phone: lead?.phone || "",
    source: lead?.source || "website",
    status: lead?.status || "new",
    destination: lead?.destination || "",
    trip_type: lead?.trip_type || "",
    travel_date: lead?.travel_date || "",
    budget: lead?.budget?.toString() || "",
    pax: lead?.pax?.toString() || "2",
    notes: lead?.notes || "",
    assigned_staff_id: lead?.assigned_staff_id?.toString() || "",
  });

  useEffect(() => { fetchStaff().then(setStaffList).catch(() => {}); }, []);

  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSave = async () => {
    if (!form.full_name.trim()) { alert("Name is required"); return; }
    setSaving(true);
    try {
      const payload: any = {
        ...form,
        budget: form.budget ? parseFloat(form.budget) : null,
        pax: parseInt(form.pax) || 2,
        assigned_staff_id: form.assigned_staff_id ? parseInt(form.assigned_staff_id) : null,
      };
      if (lead) await updateLead(lead.id, payload);
      else await createLead(payload);
      onSaved();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="crm-modal-overlay" onClick={onClose}>
      <div className="crm-modal" onClick={e => e.stopPropagation()}>
        <div className="crm-modal-header">
          <h3>{lead ? "Edit Lead" : "Add New Lead"}</h3>
          <button className="crm-modal-close" onClick={onClose}><i className="ti ti-x" /></button>
        </div>
        <div className="crm-modal-body">
          <div className="crm-form-grid">
            <div className="crm-form-group crm-span-2">
              <label>Full Name *</label>
              <input className="crm-input" value={form.full_name} onChange={e => set("full_name", e.target.value)} placeholder="e.g. Rahul Sharma" />
            </div>
            <div className="crm-form-group">
              <label>Email</label>
              <input className="crm-input" type="email" value={form.email} onChange={e => set("email", e.target.value)} placeholder="email@example.com" />
            </div>
            <div className="crm-form-group">
              <label>Phone</label>
              <input className="crm-input" value={form.phone} onChange={e => set("phone", e.target.value)} placeholder="+91 98765 43210" />
            </div>
            <div className="crm-form-group">
              <label>Source</label>
              <select className="crm-input" value={form.source} onChange={e => set("source", e.target.value)}>
                {["website","referral","walk_in","social_media","phone","other"].map(s => (
                  <option key={s} value={s}>{s.replace("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}</option>
                ))}
              </select>
            </div>
            <div className="crm-form-group">
              <label>Status</label>
              <select className="crm-input" value={form.status} onChange={e => set("status", e.target.value)}>
                {["new","contacted","qualified","lost"].map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>
                ))}
              </select>
            </div>
            <div className="crm-form-group">
              <label>Destination</label>
              <input className="crm-input" value={form.destination} onChange={e => set("destination", e.target.value)} placeholder="e.g. Andaman Islands" />
            </div>
            <div className="crm-form-group">
              <label>Trip Type</label>
              <select className="crm-input" value={form.trip_type} onChange={e => set("trip_type", e.target.value)}>
                <option value="">Select type</option>
                {["honeymoon","family","adventure","group","solo","corporate"].map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>
                ))}
              </select>
            </div>
            <div className="crm-form-group">
              <label>Travel Date</label>
              <input className="crm-input" value={form.travel_date} onChange={e => set("travel_date", e.target.value)} placeholder="e.g. March 2026" />
            </div>
            <div className="crm-form-group">
              <label>Budget (₹)</label>
              <input className="crm-input" type="number" value={form.budget} onChange={e => set("budget", e.target.value)} placeholder="150000" />
            </div>
            <div className="crm-form-group">
              <label>Pax (travellers)</label>
              <input className="crm-input" type="number" min="1" value={form.pax} onChange={e => set("pax", e.target.value)} />
            </div>
            <div className="crm-form-group">
              <label>Assigned To</label>
              <select className="crm-input" value={form.assigned_staff_id} onChange={e => set("assigned_staff_id", e.target.value)}>
                <option value="">Unassigned</option>
                {staffList.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
              </select>
            </div>
            <div className="crm-form-group crm-span-2">
              <label>Notes</label>
              <textarea className="crm-input crm-textarea" value={form.notes} onChange={e => set("notes", e.target.value)} placeholder="Additional context..." rows={3} />
            </div>
          </div>
        </div>
        <div className="crm-modal-footer">
          <button className="crm-btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-gold" onClick={handleSave} disabled={saving}>
            {saving ? <><i className="ti ti-loader-2 crm-spin" /> Saving...</> : <>{lead ? "Update Lead" : "Create Lead"}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
