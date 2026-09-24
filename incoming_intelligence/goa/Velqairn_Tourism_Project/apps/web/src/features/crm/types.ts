// CRM TypeScript Types

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'lost' | 'converted';
export type LeadSource = 'website' | 'referral' | 'walk_in' | 'social_media' | 'phone' | 'other';
export type BookingStatus = 'inquiry' | 'confirmed' | 'on_trip' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high';
export type StaffRole = 'agent' | 'manager' | 'admin';

export interface RevenueTrendDay {
  date: string;
  label: string;
  amount: number;
  height: number;
}

export interface Staff {
  id: number;
  full_name: string;
  email?: string;
  phone?: string;
  role: StaffRole;
  is_active: boolean;
  avatar_initials?: string;
  created_at?: string;
}

export interface Lead {
  id: number;
  full_name: string;
  email?: string;
  phone?: string;
  source: LeadSource;
  status: LeadStatus;
  destination?: string;
  trip_type?: string;
  travel_date?: string;
  budget?: number;
  pax: number;
  notes?: string;
  assigned_staff_id?: number;
  assigned_staff?: Staff;
  created_at?: string;
  updated_at?: string;
}

export interface Client {
  id: number;
  lead_id?: number;
  full_name: string;
  email?: string;
  phone?: string;
  address?: string;
  passport_number?: string;
  date_of_birth?: string;
  anniversary_date?: string;
  preferences?: string;
  notes?: string;
  assigned_staff_id?: number;
  assigned_staff?: Staff;
  created_at?: string;
  updated_at?: string;
}

export interface Booking {
  id: number;
  client_id: number;
  booking_ref?: string;
  destination?: string;
  hotel_name?: string;
  trip_type?: string;
  check_in?: string;
  check_out?: string;
  nights?: number;
  pax: number;
  status: BookingStatus;
  total_price?: number;
  amount_paid: number;
  profit?: number;
  itinerary_text?: string;
  notes?: string;
  assigned_staff_id?: number;
  client?: Client;
  assigned_staff?: Staff;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: number;
  title: string;
  description?: string;
  priority: TaskPriority;
  due_date?: string;
  is_done: boolean;
  lead_id?: number;
  client_id?: number;
  booking_id?: number;
  assigned_staff_id?: number;
  assigned_staff?: Staff;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardStats {
  total_leads: number;
  new_leads_today: number;
  total_clients: number;
  total_bookings: number;
  bookings_confirmed: number;
  bookings_completed: number;
  revenue_total: number;
  revenue_this_month: number;
  profit_total?: number;
  profit_this_month?: number;
  pending_tasks: number;
  total_staff: number;
}

export type ReminderType = 'pre_trip' | 'payment' | 'followup' | 'inquiry' | 'custom';
export type ReminderStatus = 'pending' | 'sent' | 'failed' | 'cancelled';

export interface WhatsAppReminder {
  id: number;
  phone_number: string;
  client_name?: string;
  client_id?: number;
  lead_id?: number;
  booking_id?: number;
  reminder_type: ReminderType;
  message_body: string;
  scheduled_at?: string;
  sent_at?: string;
  status: ReminderStatus;
  twilio_sid?: string;
  error_message?: string;
  created_at?: string;
}

export interface SendReminderPayload {
  phone_number: string;
  client_name?: string;
  client_id?: number;
  lead_id?: number;
  booking_id?: number;
  reminder_type: ReminderType;
  message_body: string;
  scheduled_at?: string;
}

