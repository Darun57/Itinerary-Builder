import type { Lead, Client, Booking, Task, Staff, DashboardStats, RevenueTrendDay, WhatsAppReminder, SendReminderPayload } from './types';
export type { RevenueTrendDay };

const BASE = 'http://localhost:8001/api/crm';

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `CRM API error ${res.status}`);
  }
  return res.json();
}

// Dashboard
export const fetchCRMStats = () => req<DashboardStats>('/dashboard/stats');
export const fetchRevenueTrend = (period: string = 'monthly') => req<RevenueTrendDay[]>(`/dashboard/revenue-trend?period=${period}`);
export const fetchProfitTrend = (period: string = 'monthly') => req<RevenueTrendDay[]>(`/dashboard/profit-trend?period=${period}`);

// Staff
export const fetchStaff = () => req<Staff[]>('/staff');
export const createStaff = (d: Partial<Staff>) => req<Staff>('/staff', { method: 'POST', body: JSON.stringify(d) });
export const updateStaff = (id: number, d: Partial<Staff>) => req<Staff>(`/staff/${id}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteStaff = (id: number) => req(`/staff/${id}`, { method: 'DELETE' });

// Leads
export const fetchLeads = (status?: string) => {
  const qs = status ? `?status=${status}` : '';
  return req<Lead[]>(`/leads${qs}`);
};
export const createLead = (d: Partial<Lead>) => req<Lead>('/leads', { method: 'POST', body: JSON.stringify(d) });
export const updateLead = (id: number, d: Partial<Lead>) => req<Lead>(`/leads/${id}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteLead = (id: number) => req(`/leads/${id}`, { method: 'DELETE' });
export const convertLead = (id: number) => req<Client>(`/leads/${id}/convert`, { method: 'POST' });

// Clients
export const fetchClients = () => req<Client[]>('/clients');
export const createClient = (d: Partial<Client>) => req<Client>('/clients', { method: 'POST', body: JSON.stringify(d) });
export const updateClient = (id: number, d: Partial<Client>) => req<Client>(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteClient = (id: number) => req(`/clients/${id}`, { method: 'DELETE' });

// Bookings
export const fetchBookings = (status?: string) => {
  const qs = status ? `?status=${status}` : '';
  return req<Booking[]>(`/bookings${qs}`);
};
export const createBooking = (d: Partial<Booking>) => req<Booking>('/bookings', { method: 'POST', body: JSON.stringify(d) });
export const updateBooking = (id: number, d: Partial<Booking>) => req<Booking>(`/bookings/${id}`, { method: 'PUT', body: JSON.stringify(d) });
export const updateBookingProfit = (id: number, profit: number) => req<Booking>(`/bookings/${id}/profit`, { method: 'PATCH', body: JSON.stringify({ profit }) });
export const deleteBooking = (id: number) => req(`/bookings/${id}`, { method: 'DELETE' });

// Tasks
export const fetchTasks = (isDone?: boolean) => {
  const qs = isDone !== undefined ? `?is_done=${isDone}` : '';
  return req<Task[]>(`/tasks${qs}`);
};
export const createTask = (d: Partial<Task>) => req<Task>('/tasks', { method: 'POST', body: JSON.stringify(d) });
export const updateTask = (id: number, d: Partial<Task>) => req<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteTask = (id: number) => req(`/tasks/${id}`, { method: 'DELETE' });

// WhatsApp Reminders
export const fetchReminders = (status?: string, reminderType?: string) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (reminderType) params.append('reminder_type', reminderType);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return req<WhatsAppReminder[]>(`/reminders${qs}`);
};

export const fetchReminderLogs = () => req<WhatsAppReminder[]>('/reminders/logs');

export const fetchReminderTemplates = () => req<{ value: string; label: string }[]>('/reminders/templates');

export const previewReminderTemplate = (payload: {
  reminder_type: string;
  booking_id?: number;
  lead_id?: number;
  client_id?: number;
  custom_message?: string;
}) => req<{ preview: string; reminder_type: string }>('/reminders/preview', {
  method: 'POST',
  body: JSON.stringify(payload),
});

export const scheduleReminder = (payload: SendReminderPayload) =>
  req<WhatsAppReminder>('/reminders', { method: 'POST', body: JSON.stringify(payload) });

export const sendReminderNow = (payload: SendReminderPayload) =>
  req<WhatsAppReminder>('/reminders/send-now', { method: 'POST', body: JSON.stringify(payload) });

export const sendPendingReminder = (id: number) =>
  req<WhatsAppReminder>(`/reminders/${id}/send`, { method: 'PATCH' });

export const cancelReminder = (id: number) =>
  req<WhatsAppReminder>(`/reminders/${id}/cancel`, { method: 'PATCH' });

export const deleteReminder = (id: number) =>
  req<{ message: string }>(`/reminders/${id}`, { method: 'DELETE' });

export const triggerAutoSchedule = () =>
  req<{ created: number; details: string[]; message: string }>('/reminders/auto-schedule', { method: 'POST' });

export const markReminderSent = (id: number) =>
  req<WhatsAppReminder>(`/reminders/${id}/send`, { method: 'PATCH' });

export const syncCrmReminders = () =>
  req<{ synced: number; message: string }>('/reminders/sync-crm', { method: 'POST' });


