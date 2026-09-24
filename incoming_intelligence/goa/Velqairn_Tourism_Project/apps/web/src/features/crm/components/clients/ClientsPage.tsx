"use client";
import React, { useEffect, useState, useCallback } from "react";
import type { Client } from "../../types";
import { fetchClients, deleteClient } from "../../api";
import { ClientForm } from "./ClientForm";
import { WhatsAppReminderModal } from "../reminders/WhatsAppReminderModal";

export function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editClient, setEditClient] = useState<Client | null>(null);
  const [waClient, setWaClient] = useState<Client | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setClients(await fetchClients()); } catch (e) { console.error(e); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this client?")) return;
    await deleteClient(id);
    load();
  };

  const initials = (name: string) => name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

  const filtered = clients.filter(c =>
    c.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (c.email || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="crm-page">
      <div className="crm-page-header">
        <div>
          <h2 className="crm-page-title"><i className="ti ti-users" /> Clients</h2>
          <p className="crm-page-sub">Manage your confirmed client profiles</p>
        </div>
        <button className="btn-gold" onClick={() => { setEditClient(null); setShowForm(true); }}>
          <i className="ti ti-plus" /> Add Client
        </button>
      </div>
      <div className="crm-toolbar">
        <input className="crm-search" placeholder="Search by name or email..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="crm-loading"><i className="ti ti-loader-2 crm-spin" /> Loading clients...</div>
      ) : filtered.length === 0 ? (
        <div className="crm-empty">
          <i className="ti ti-users" />
          <p>No clients yet. Convert a lead or add a client directly.</p>
        </div>
      ) : (
        <div className="crm-cards-grid">
          {filtered.map(client => (
            <div key={client.id} className="crm-client-card">
              <div className="crm-client-card-top">
                <div className="crm-avatar crm-avatar-lg" style={{ background: "rgba(157,180,232,0.15)", color: "#9db4e8" }}>
                  {initials(client.full_name)}
                </div>
                <div className="crm-actions" style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                  {client.phone && (
                    <button
                      className="crm-btn-icon"
                      style={{ color: "#25D366", borderColor: "rgba(37, 211, 102, 0.3)" }}
                      title="Open WhatsApp chat or schedule reminder"
                      onClick={() => setWaClient(client)}
                    >
                      <i className="ti ti-brand-whatsapp" />
                    </button>
                  )}
                  <button className="crm-btn-icon" onClick={() => { setEditClient(client); setShowForm(true); }}><i className="ti ti-edit" /></button>
                  <button className="crm-btn-delete" onClick={() => handleDelete(client.id)}><i className="ti ti-trash" /> Delete</button>
                </div>
              </div>
              <div className="crm-client-name">{client.full_name}</div>
              <div className="crm-client-meta">{client.email || "—"}</div>
              <div className="crm-client-meta">{client.phone || "—"}</div>
              {client.anniversary_date && (
                <div className="crm-client-badge"><i className="ti ti-heart" /> Anniversary: {client.anniversary_date}</div>
              )}
              {client.assigned_staff && (
                <div className="crm-client-agent">
                  <span className="crm-avatar crm-avatar-xs">{client.assigned_staff.avatar_initials || "?"}</span>
                  {client.assigned_staff.full_name}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <ClientForm client={editClient} onClose={() => setShowForm(false)} onSaved={() => { setShowForm(false); load(); }} />
      )}

      {waClient && (
        <WhatsAppReminderModal initialClient={waClient} onClose={() => setWaClient(null)} />
      )}
    </div>
  );
}
