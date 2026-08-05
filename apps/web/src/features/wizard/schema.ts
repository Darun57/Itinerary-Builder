import { z } from "zod";

export const DayPlanSchema = z.object({
  day_number: z.number(),
  primary_island: z.string(),
  attractions: z.array(z.string()),
  activities: z.array(z.string()),
  hotel: z.string(),
  transfer_type: z.string(),
  ferry: z.string().optional(),
  ferry_timing: z.string().optional(),
});


export const tripRequestSchema = z.object({
  // Step 1: Customer Details
  customer_name: z.string().min(2, "Customer name is required"),
  lead_id: z.string().optional().default(""),
  customer_nationality: z.string().min(1, "Nationality is required"),
  customer_country: z.string().min(1, "Country is required"),
  customer_email: z.string().email("Valid email is required"),
  customer_phone_number: z.string().min(5, "Phone number is required"),

  // Step 2: Trip Details
  destination: z.string().min(1, "Destination is required"),
  selected_destinations: z.array(z.string()).default([]),
  number_of_nights: z.coerce.number().min(1),
  number_of_days: z.coerce.number().min(1),
  arrival_date: z.string().min(1, "Arrival date is required"),
  departure_date: z.string().min(1, "Departure date is required"),
  travel_month: z.string().optional().default(""),
  flexible_travel_dates: z.boolean().default(false),
  trip_type: z.string().min(1),
  budget_category: z.string().min(1),
  number_of_adults: z.coerce.number().min(1),
  number_of_children: z.coerce.number().default(0),
  number_of_infants: z.coerce.number().default(0),
  number_of_senior_citizens: z.coerce.number().default(0),
  travel_style: z.array(z.string()).default([]),
  trip_pace: z.string().min(1),

  // Step 3: Accommodation
  hotel_category_preference: z.string().min(1),
  room_type_preference: z.string().optional().default(""),
  room_view_preference: z.string().optional().default(""),
  hotel_selection_islands: z.array(z.string()).default([]),
  selected_hotels: z.array(z.string()).default([]),

  // Step 4: Activities
  preferred_activities: z.array(z.string()).default([]),
  special_occasions: z.array(z.string()).default([]),

  // Step 5: Transport & Meals
  transfer_type: z.string().min(1),
  preferred_ferries: z.array(z.string()).default([]),
  meal_plan: z.string().min(1),
  food_preferences: z.array(z.string()).default([]),
  flight_option: z.string().default("Excluded"),
  flight_per_person_rate: z.coerce.number().default(0),
  per_person_cost: z.coerce.number().default(0),
  total_package_cost: z.coerce.number().default(0),

  // Step 6: Preferences & Internal
  accessibility_requirements: z.array(z.string()).default([]),
  restrictions_exclusions: z.array(z.string()).default([]),
  internal_staff_notes: z.string().default(""),
  special_requests: z.string().default(""),

  // Advanced / AI Gen details
  daily_island_plan: z.array(DayPlanSchema).default([]),
});

export type TripRequestType = z.infer<typeof tripRequestSchema>;

export const defaultTripValues: Partial<TripRequestType> = {
  lead_id: "",
  customer_name: "",
  customer_nationality: "Indian",
  customer_country: "India",
  customer_email: "",
  customer_phone_number: "",
  destination: "Andaman and Nicobar Islands",
  selected_destinations: [],
  number_of_nights: 1,
  number_of_days: 2,
  arrival_date: "",
  departure_date: "",
  travel_month: "",
  flexible_travel_dates: false,
  trip_type: "",
  budget_category: "",
  number_of_adults: 2,
  number_of_children: 0,
  number_of_infants: 0,
  number_of_senior_citizens: 0,
  travel_style: [],
  trip_pace: "",
  hotel_category_preference: "",
  room_type_preference: "",
  room_view_preference: "",
  hotel_selection_islands: [],
  selected_hotels: [],
  preferred_activities: [],
  special_occasions: [],
  transfer_type: "",
  preferred_ferries: [],
  meal_plan: "",
  food_preferences: [],
  flight_option: "Excluded",
  flight_per_person_rate: 0,
  per_person_cost: 0,
  total_package_cost: 0,
  accessibility_requirements: [],
  restrictions_exclusions: [],
  internal_staff_notes: "",
  special_requests: "",
  daily_island_plan: [],
};
