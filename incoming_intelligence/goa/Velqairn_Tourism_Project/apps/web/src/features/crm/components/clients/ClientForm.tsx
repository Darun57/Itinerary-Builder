"use client";
import React, { useState, useEffect } from "react";
import type { Client, Staff } from "../../types";
import { createClient, updateClient, fetchStaff } from "../../api";

interface Props { client: Client | null; onClose: () => void; onSaved: () => void; }

export function ClientForm({ client, onClose, onSaved }: Props) {
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: client?.full_name || "",
    email: client?.email || "",
    phone: client?.phone || "",
    address: client?.address || "",
    passport_number: client?.passport_number || "",
    date_of_birth: client?.date_of_birth || "",
    anniversary_date: client?.anniversary_date || "",
    preferences: client?.preferences || "",
    notes: client?.notes || "",
    assigned_staff_id: client?.assigned_staff_id?.toString() || "",
  });

  useEffect(() => { fetchStaff().then(setStaffList).catch(() => {}); }, []);
  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSave = async () => {
    if (!form.full_name.trim()) { alert("Name is required"); return; }
    setSaving(true);
    try {
      const payload: any = { ...form, assigned_staff_id: form.assigned_staff_id ? parseInt(form.assigned_staff_id) : null };
      if (client) await updateClient(client.id, payload);
      else await createClient(payload);
      onSaved();
    } catch (e: any) { alert(e.message); } finally { setSaving(false); }
  };

  return (
    <div className="crm-modal-overlay" onClick={onClose}>
      <div className="crm-modal" onClick={e => e.stopPropagation()}>
        <div className="crm-modal-header">
          <h3>{client ? "Edit Client" : "Add Client"}</h3>
          <button className="crm-modal-close" onClick={onClose}><i className="ti ti-x" /></button>
        </div>
        <div className="crm-modal-body">
          <div className="crm-form-grid">
            <div className="crm-form-group crm-span-2"><label>Full Name *</label><input className="crm-input" value={form.full_name} onChange={e => set("full_name", e.target.value)} /></div>
            <div className="crm-form-group"><label>Email</label><input className="crm-input" type="email" value={form.email} onChange={e => set("email", e.target.value)} /></div>
            <div className="crm-form-group"><label>Phone</label><input className="crm-input" value={form.phone} onChange={e => set("phone", e.target.value)} /></div>
            <div className="crm-form-group crm-span-2"><label>Address</label><input className="crm-input" value={form.address} onChange={e => set("address", e.target.value)} /></div>
            <div className="crm-form-group"><label>Passport Number</label><input className="crm-input" value={form.passport_number} onChange={e => set("passport_number", e.target.value)} /></div>
            <div className="crm-form-group"><label>Date of Birth</label><input className="crm-input" value={form.date_of_birth} onChange={e => set("date_of_birth", e.target.value)} placeholder="DD/MM/YYYY" /></div>
            <div className="crm-form-group"><label>Anniversary Date</label><input className="crm-input" value={form.anniversary_date} onChange={e => set("anniversary_date", e.target.value)} placeholder="DD/MM/YYYY" /></div>
            <div className="crm-form-group"><label>Assigned To</label>
              <select className="crm-input" value={form.assigned_staff_id} onChange={e => set("assigned_staff_id", e.target.value)}>
                <option value="">Unassigned</option>
                {staffList.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
              </select>
            </div>
            <div className="crm-form-group crm-span-2"><label>Preferences</label><textarea className="crm-input crm-textarea" value={form.preferences} onChange={e => set("preferences", e.target.value)} placeholder="e.g. Vegetarian, no flights, sea-facing rooms..." rows={2} /></div>
            <div className="crm-form-group crm-span-2"><label>Notes</label><textarea className="crm-input crm-textarea" value={form.notes} onChange={e => set("notes", e.target.value)} rows={2} /></div>
          </div>
        </div>
        <div className="crm-modal-footer">
          <button className="crm-btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-gold" onClick={handleSave} disabled={saving}>
            {saving ? <><i className="ti ti-loader-2 crm-spin" /> Saving...</> : <>{client ? "Update" : "Create Client"}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
