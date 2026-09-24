"use client";
import React, { useEffect, useState, useCallback } from "react";
import type { Staff } from "../../types";
import { fetchStaff, createStaff, updateStaff, deleteStaff } from "../../api";

const ROLE_COLORS: Record<string, string> = { admin: "#D4AF37", manager: "#a78bfa", agent: "#9db4e8" };

export function StaffPage() {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editStaff, setEditStaff] = useState<Staff | null>(null);
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", role: "agent" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setStaff(await fetchStaff()); } catch (e) { console.error(e); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openEdit = (s: Staff) => { setEditStaff(s); setForm({ full_name: s.full_name, email: s.email || "", phone: s.phone || "", role: s.role }); setShowForm(true); };
  const openNew = () => { setEditStaff(null); setForm({ full_name: "", email: "", phone: "", role: "agent" }); setShowForm(true); };
  const set = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }));

  const handleSave = async () => {
    if (!form.full_name.trim()) { alert("Name required"); return; }
    setSaving(true);
    try {
      if (editStaff) await updateStaff(editStaff.id, form as any);
      else await createStaff(form as any);
      setShowForm(false);
      load();
    } catch (e: any) { alert(e.message); } finally { setSaving(false); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deactivate this staff member?")) return;
    await deleteStaff(id);
    load();
  };

  return (
    <div className="crm-page">
      <div className="crm-page-header">
        <div>
          <h2 className="crm-page-title"><i className="ti ti-id-badge" /> Staff & Agents</h2>
          <p className="crm-page-sub">Manage your internal team</p>
        </div>
        <button className="btn-gold" onClick={openNew}><i className="ti ti-plus" /> Add Staff</button>
      </div>

      {showForm && (
        <div className="crm-modal-overlay" onClick={() => setShowForm(false)}>
          <div className="crm-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: "480px" }}>
            <div className="crm-modal-header">
              <h3>{editStaff ? "Edit Staff" : "Add Staff Member"}</h3>
              <button className="crm-modal-close" onClick={() => setShowForm(false)}><i className="ti ti-x" /></button>
            </div>
            <div className="crm-modal-body">
              <div className="crm-form-grid">
                <div className="crm-form-group crm-span-2"><label>Full Name *</label><input className="crm-input" value={form.full_name} onChange={e => set("full_name", e.target.value)} /></div>
                <div className="crm-form-group"><label>Email</label><input className="crm-input" type="email" value={form.email} onChange={e => set("email", e.target.value)} /></div>
                <div className="crm-form-group"><label>Phone</label><input className="crm-input" value={form.phone} onChange={e => set("phone", e.target.value)} /></div>
                <div className="crm-form-group crm-span-2"><label>Role</label>
                  <select className="crm-input" value={form.role} onChange={e => set("role", e.target.value)}>
                    {["agent","manager","admin"].map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase()+r.slice(1)}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div className="crm-modal-footer">
              <button className="crm-btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn-gold" onClick={handleSave} disabled={saving}>
                {saving ? <><i className="ti ti-loader-2 crm-spin" /> Saving...</> : <>{editStaff ? "Update" : "Add Staff"}</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="crm-loading"><i className="ti ti-loader-2 crm-spin" /> Loading staff...</div>
      ) : staff.length === 0 ? (
        <div className="crm-empty"><i className="ti ti-id-badge" /><p>No staff added yet.</p></div>
      ) : (
        <div className="crm-cards-grid">
          {staff.map(s => (
            <div key={s.id} className="crm-client-card">
              <div className="crm-client-card-top">
                <div className="crm-avatar crm-avatar-lg" style={{ background: ROLE_COLORS[s.role] + "22", color: ROLE_COLORS[s.role] }}>
                  {s.avatar_initials || s.full_name.slice(0, 2).toUpperCase()}
                </div>
                <div className="crm-actions">
                  <button className="crm-btn-icon" onClick={() => openEdit(s)}><i className="ti ti-edit" /></button>
                  <button className="crm-btn-icon crm-btn-danger" onClick={() => handleDelete(s.id)}><i className="ti ti-trash" /></button>
                </div>
              </div>
              <div className="crm-client-name">{s.full_name}</div>
              <div className="crm-client-meta">{s.email || "—"}</div>
              <div className="crm-client-meta">{s.phone || "—"}</div>
              <div style={{ marginTop: "8px" }}>
                <span className="crm-chip" style={{ color: ROLE_COLORS[s.role], borderColor: ROLE_COLORS[s.role] + "55" }}>
                  {s.role.charAt(0).toUpperCase() + s.role.slice(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
