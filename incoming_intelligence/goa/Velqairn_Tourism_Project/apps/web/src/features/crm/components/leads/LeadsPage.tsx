"use client";
import React, { useEffect, useState, useCallback } from "react";
import type { Lead, LeadStatus } from "../../types";
import { fetchLeads, deleteLead, convertLead, updateLead } from "../../api";
import { LeadForm } from "./LeadForm";
import { WhatsAppReminderModal } from "../reminders/WhatsAppReminderModal";

const STATUS_COLORS: Record<string, string> = {
  new: "#D4AF37",
  contacted: "#9db4e8",
  qualified: "#3FBF7F",
  lost: "#e87878",
  converted: "#a78bfa",
};

const SOURCE_LABELS: Record<string, string> = {
  website: "Website",
  referral: "Referral",
  walk_in: "Walk-in",
  social_media: "Social",
  phone: "Phone",
  other: "Other",
};

export function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editLead, setEditLead] = useState<Lead | null>(null);
  const [waLead, setWaLead] = useState<Lead | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLeads(filterStatus || undefined);
      setLeads(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this lead?")) return;
    await deleteLead(id);
    load();
  };

  const handleConvert = async (id: number) => {
    if (!confirm("Convert this lead to a client?")) return;
    try {
      await convertLead(id);
      alert("Lead converted to client successfully!");
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleStatusChange = async (lead: Lead, newStatus: LeadStatus) => {
    await updateLead(lead.id, { status: newStatus });
    load();
  };

  const filtered = leads.filter(l =>
    l.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (l.email || "").toLowerCase().includes(search.toLowerCase()) ||
    (l.destination || "").toLowerCase().includes(search.toLowerCase())
  );

  const initials = (name: string) => name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

  return (
    <div className="crm-page">
      <div className="crm-page-header">
        <div>
          <h2 className="crm-page-title"><i className="ti ti-user-plus" /> Leads</h2>
          <p className="crm-page-sub">Track and manage incoming enquiries</p>
        </div>
        <button className="btn-gold" onClick={() => { setEditLead(null); setShowForm(true); }}>
          <i className="ti ti-plus" /> Add Lead
        </button>
      </div>

      <div className="crm-toolbar">
        <input
          className="crm-search"
          placeholder="Search by name, email or destination..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="crm-filter-tabs">
          {["", "new", "contacted", "qualified", "lost", "converted"].map(s => (
            <button
              key={s}
              className={`crm-filter-tab${filterStatus === s ? " active" : ""}`}
              onClick={() => setFilterStatus(s)}
            >
              {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="crm-loading"><i className="ti ti-loader-2 crm-spin" /> Loading leads...</div>
      ) : filtered.length === 0 ? (
        <div className="crm-empty">
          <i className="ti ti-user-search" />
          <p>No leads found. Add your first lead to get started.</p>
        </div>
      ) : (
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Destination</th>
                <th>Travel Date</th>
                <th>Budget</th>
                <th>Pax</th>
                <th>Source</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(lead => (
                <tr key={lead.id}>
                  <td>
                    <div className="crm-person-cell">
                      <div className="crm-avatar" style={{ background: "rgba(212,175,55,0.15)", color: "#D4AF37" }}>
                        {initials(lead.full_name)}
                      </div>
                      <div>
                        <div className="crm-person-name">{lead.full_name}</div>
                        <div className="crm-person-email">{lead.email || lead.phone || "—"}</div>
                      </div>
                    </div>
                  </td>
                  <td>{lead.destination || "—"}</td>
                  <td>{lead.travel_date || "—"}</td>
                  <td>{lead.budget ? `₹${lead.budget.toLocaleString()}` : "—"}</td>
                  <td>{lead.pax}</td>
                  <td><span className="crm-chip crm-chip-ghost">{SOURCE_LABELS[lead.source] || lead.source}</span></td>
                  <td>
                    <select
                      className="crm-status-select"
                      value={lead.status}
                      style={{ color: STATUS_COLORS[lead.status] }}
                      onChange={e => handleStatusChange(lead, e.target.value as LeadStatus)}
                    >
                      {["new", "contacted", "qualified", "lost", "converted"].map(s => (
                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <div className="crm-actions">
                      <button
                        className="crm-btn-icon"
                        title="WhatsApp message"
                        style={{ color: "#25D366" }}
                        onClick={() => setWaLead(lead)}
                      >
                        <i className="ti ti-brand-whatsapp" />
                      </button>
                      <button className="crm-btn-icon" title="Edit" onClick={() => { setEditLead(lead); setShowForm(true); }}>
                        <i className="ti ti-edit" />
                      </button>
                      {lead.status !== "converted" && (
                        <button className="crm-btn-icon crm-btn-convert" title="Convert to Client" onClick={() => handleConvert(lead.id)}>
                          <i className="ti ti-user-check" />
                        </button>
                      )}
                      <button
                        className="crm-btn-delete"
                        title="Delete lead"
                        onClick={() => handleDelete(lead.id)}
                      >
                        <i className="ti ti-trash" /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <LeadForm
          lead={editLead}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load(); }}
        />
      )}

      {waLead && (
        <WhatsAppReminderModal
          initialLead={waLead}
          initialPhone={waLead.phone || ""}
          initialName={waLead.full_name}
          onClose={() => setWaLead(null)}
          onSuccess={() => setWaLead(null)}
        />
      )}
    </div>
  );
}
