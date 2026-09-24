import { TripRequestType } from "../features/wizard/schema";

const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname || "localhost";
    const protocol = window.location.protocol || "http:";
    return `${protocol}//${hostname}:8001/api`;
  }
  return "http://127.0.0.1:8001/api";
};

async function safeFetch(path: string, options?: RequestInit): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const primaryUrl = `${baseUrl}${path}`;
  try {
    return await fetch(primaryUrl, options);
  } catch (err) {
    const fallbackBase = baseUrl.includes("localhost")
      ? baseUrl.replace("localhost", "127.0.0.1")
      : baseUrl.includes("127.0.0.1")
        ? baseUrl.replace("127.0.0.1", "localhost")
        : baseUrl;
    const fallbackUrl = `${fallbackBase}${path}`;
    if (fallbackUrl !== primaryUrl) {
      try {
        return await fetch(fallbackUrl, options);
      } catch (fallbackErr) {
        console.error(`Fetch failed for primary (${primaryUrl}) and fallback (${fallbackUrl}):`, fallbackErr);
        throw new Error(`Unable to connect to API backend. Ensure FastAPI server is running on port 8001.`);
      }
    }
    console.error(`Fetch failed for ${primaryUrl}:`, err);
    throw new Error(`Unable to connect to API backend at ${primaryUrl}. Ensure FastAPI server is running on port 8001.`);
  }
}

function cleanTripPayload(data: Partial<TripRequestType>): any {
  if (!data || typeof data !== "object") return data;
  const copy: any = { ...data };
  const numericKeys = [
    "number_of_nights",
    "number_of_days",
    "number_of_adults",
    "number_of_children",
    "number_of_infants",
    "number_of_senior_citizens",
    "flight_per_person_rate",
    "per_person_cost",
    "child_cost",
    "infant_cost",
    "senior_cost",
    "total_package_cost",
  ];
  for (const k of numericKeys) {
    if (copy[k] === "" || copy[k] === null || copy[k] === undefined || isNaN(Number(copy[k]))) {
      copy[k] = 0;
    } else {
      copy[k] = Number(copy[k]);
    }
  }
  if (Array.isArray(copy.daily_island_plan)) {
    copy.daily_island_plan = copy.daily_island_plan.map((dp: any, idx: number) => ({
      day_number: Number(dp?.day_number) || (idx + 1),
      primary_island: String(dp?.primary_island || ""),
      attractions: Array.isArray(dp?.attractions) ? dp.attractions : [],
      activities: Array.isArray(dp?.activities) ? dp.activities : [],
      hotel: String(dp?.hotel || ""),
      transfer_type: String(dp?.transfer_type || "Private Cab"),
      ferry: String(dp?.ferry || ""),
      ferry_timing: String(dp?.ferry_timing || ""),
    }));
  }
  if (Array.isArray(copy.pricing_tiers)) {
    copy.pricing_tiers = copy.pricing_tiers.map((pt: any) => ({
      category: pt?.category || "adult",
      label: pt?.label || "",
      pax: Number(pt?.pax) || 1,
      cost: Number(pt?.cost) || 0,
    }));
  }
  return copy;
}

export async function fetchHotelRecommendations(data: Partial<TripRequestType>) {
  const payload = cleanTripPayload(data);
  const response = await safeFetch("/recommendations/hotels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    console.error("fetchHotelRecommendations error:", response.status, errText);
    throw new Error(`Failed to fetch hotels: ${response.status} ${errText}`);
  }
  return response.json();
}

export async function fetchActivityRecommendations(data: Partial<TripRequestType>) {
  const payload = cleanTripPayload(data);
  const response = await safeFetch("/recommendations/activities", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Failed to fetch activities");
  return response.json();
}

export async function fetchDestinationRecommendations(data: Partial<TripRequestType>) {
  const response = await safeFetch("/recommendations/destinations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to fetch destinations");
  return response.json();
}

export async function fetchAvailableDestinations() {
  const response = await safeFetch("/destinations?status=active");
  if (!response.ok) throw new Error("Failed to fetch available destinations");
  return response.json();
}

export async function fetchDestinationCapabilities(region: string) {
  const response = await safeFetch(`/destinations/${encodeURIComponent(region)}/capabilities`);
  if (!response.ok) throw new Error(`Failed to fetch capabilities for ${region}`);
  return response.json();
}

export async function fetchAllDestinations(region?: string) {
  const url = region ? `/data/destinations?region=${encodeURIComponent(region)}` : "/data/destinations";
  const response = await safeFetch(url);
  if (!response.ok) throw new Error("Failed to fetch all destinations");
  return response.json();
}

export async function fetchDestinationContext(region: string) {
  const response = await safeFetch(`/destinations/${encodeURIComponent(region)}/context`);
  if (!response.ok) throw new Error(`Failed to fetch destination context for ${region}`);
  return response.json();
}

export async function fetchDestinationMovements(region: string) {
  const response = await safeFetch(`/destinations/${encodeURIComponent(region)}/movements`);
  if (!response.ok) throw new Error(`Failed to fetch movements for ${region}`);
  return response.json();
}

export async function fetchAllActivities(region?: string) {
  const url = region ? `/data/activities?region=${encodeURIComponent(region)}` : "/data/activities";
  const response = await safeFetch(url);
  if (!response.ok) throw new Error("Failed to fetch all activities");
  return response.json();
}

export async function fetchAllFerries() {
  const response = await safeFetch("/data/ferries");
  if (!response.ok) throw new Error("Failed to fetch all ferries");
  return response.json();
}

export async function fetchFerryRecommendations(data: Partial<TripRequestType>) {
  const response = await safeFetch("/recommendations/ferries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to fetch ferries");
  return response.json();
}

export async function generateAIItinerary(data: TripRequestType, apiKey: string) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const response = await safeFetch("/ai/generate", {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => null);
    throw new Error(errData?.detail || "Failed to generate AI itinerary");
  }
  return response.json();
}

export interface NewHotelPayload {
  hotel_name: string;
  location: string;
  category: string;
  room_type?: string;
  description?: string;
  availability_status?: string;
}

export async function fetchAllHotels(region?: string) {
  const url = region ? `/hotels?region=${encodeURIComponent(region)}` : "/hotels";
  const response = await safeFetch(url, { method: "GET" });
  if (!response.ok) return [];
  return response.json();
}

export async function createHotel(data: NewHotelPayload) {
  const response = await safeFetch("/hotels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => null);
    throw new Error(err?.detail || "Failed to create hotel");
  }
  return response.json();
}

export async function generatePDF(payload: { request: TripRequestType; itinerary_text: string }) {
  const response = await safeFetch("/pdf/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || "Failed to generate PDF");
  }
  return response.blob();
}
