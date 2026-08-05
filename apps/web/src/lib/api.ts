import { TripRequestType } from "../features/wizard/schema";

const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname || "localhost";
    const protocol = window.location.protocol || "http:";
    return `${protocol}//${hostname}:8000/api`;
  }
  return "http://127.0.0.1:8000/api";
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
        throw new Error(`Unable to connect to API backend. Ensure FastAPI server is running on port 8000.`);
      }
    }
    console.error(`Fetch failed for ${primaryUrl}:`, err);
    throw new Error(`Unable to connect to API backend at ${primaryUrl}. Ensure FastAPI server is running on port 8000.`);
  }
}

export async function fetchHotelRecommendations(data: Partial<TripRequestType>) {
  const response = await safeFetch("/recommendations/hotels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to fetch hotels");
  return response.json();
}

export async function fetchActivityRecommendations(data: Partial<TripRequestType>) {
  const response = await safeFetch("/recommendations/activities", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
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

export async function fetchAllDestinations() {
  const response = await safeFetch("/data/destinations");
  if (!response.ok) throw new Error("Failed to fetch all destinations");
  return response.json();
}

export async function fetchAllActivities() {
  const response = await safeFetch("/data/activities");
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
