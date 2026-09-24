import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { TripRequestType, defaultTripValues } from './schema';
import { resolvePrimaryIsland } from './utils';
import { getDestinationDayDefaults } from './destinationDefaults';

const ANDAMAN_LOCATION_KEYWORDS = [
  "port blair", "havelock", "swaraj dweep", "neil", "shaheed dweep",
  "baratang", "diglipur", "rangat", "mayabunder", "little andaman",
  "wandoor", "chidiya tapu", "long island"
];

const ANDAMAN_ATTRACTION_KEYWORDS = [
  "cellular jail", "corbyn", "radhanagar", "elephant beach",
  "kalapathar", "bharatpur", "laxmanpur", "natural bridge",
  "sitapur", "limestone caves", "mud volcano", "jolly buoy",
  "ross island", "north bay", "chatham", "samudrika", "anthropological"
];

function isAndamanLocation(loc: string): boolean {
  const l = loc.toLowerCase();
  return ANDAMAN_LOCATION_KEYWORDS.some(k => l.includes(k));
}

function isAndamanAttraction(att: string): boolean {
  const a = att.toLowerCase();
  return ANDAMAN_ATTRACTION_KEYWORDS.some(k => a.includes(k));
}

function isAndamanActivity(act: string): boolean {
  const a = act.toLowerCase();
  if (a.startsWith("act-")) return true;
  return ANDAMAN_LOCATION_KEYWORDS.some(k => a.includes(k)) || ANDAMAN_ATTRACTION_KEYWORDS.some(k => a.includes(k));
}

function isAndamanHotel(hotel: string): boolean {
  const h = hotel.toLowerCase();
  return ANDAMAN_LOCATION_KEYWORDS.some(k => h.includes(k)) ||
    ["symphony palms", "barefoot", "seashell", "sinclairs", "tsg", "coral reef resort", "silver sand"].some(k => h.includes(k));
}

export function sanitizeDestinationFormData(formData: Partial<TripRequestType>): Partial<TripRequestType> {
  if (!formData || !formData.destination) return formData;

  const dest = formData.destination.trim();
  const isAndaman = !dest || dest.toLowerCase().includes("andaman");

  if (!isAndaman) {
    const sanitized = { ...formData };

    // 1. Non-Andaman destinations do not support inter-island ferries
    if (sanitized.preferred_ferries && sanitized.preferred_ferries.length > 0) {
      sanitized.preferred_ferries = [];
    }

    // 2. Remove Andaman activities
    if (sanitized.preferred_activities && sanitized.preferred_activities.length > 0) {
      sanitized.preferred_activities = sanitized.preferred_activities.filter((act) => !isAndamanActivity(String(act)));
    }

    if (sanitized.included_activities && sanitized.included_activities.length > 0) {
      sanitized.included_activities = sanitized.included_activities.filter(
        (act) => !isAndamanActivity(String(act.activity_name || "")) && !isAndamanLocation(String(act.location || ""))
      );
    }

    // 3. Remove Andaman hotels / location selections
    if (sanitized.hotel_selection_islands && sanitized.hotel_selection_islands.length > 0) {
      sanitized.hotel_selection_islands = sanitized.hotel_selection_islands.filter((loc) => !isAndamanLocation(String(loc)));
    }

    if (sanitized.selected_hotels && sanitized.selected_hotels.length > 0) {
      sanitized.selected_hotels = sanitized.selected_hotels.filter((h) => !isAndamanHotel(String(h)));
    }

    // 4. Remove Andaman destinations from selected_destinations
    if (sanitized.selected_destinations && sanitized.selected_destinations.length > 0) {
      sanitized.selected_destinations = sanitized.selected_destinations.filter((d) => !isAndamanLocation(String(d)));
    }

    // 5. Check if daily_island_plan contains Andaman locations or attractions
    const currentPlan = sanitized.daily_island_plan || [];
    const hasAndamanContamination = currentPlan.some((day) => {
      const isl = String(day.primary_island || "").toLowerCase();
      const atts = (day.attractions || []).map((a) => String(a).toLowerCase());
      return isAndamanLocation(isl) || atts.some((a) => isAndamanAttraction(a));
    });

    if (hasAndamanContamination || currentPlan.length === 0) {
      const numDays = Math.max(1, Number(sanitized.number_of_days) || 5);
      const defaults = getDestinationDayDefaults(dest);
      sanitized.daily_island_plan = Array.from({ length: numDays }).map((_, i) => {
        const def = defaults[i % defaults.length];
        return {
          day_number: i + 1,
          primary_island: def.region,
          attractions: [...def.attractions],
          activities: [],
          hotel: "",
          transfer_type: "Private AC Chauffeur Sedan/SUV",
          ferry: "None",
          ferry_timing: "",
        };
      });
    }

    return sanitized;
  }

  // If destination is Andaman, ensure non-Andaman hubs are not contaminating
  const currentPlan = formData.daily_island_plan || [];
  const nonAndamanSample = ["candolim", "baga", "vagator", "panaji", "jaipur", "jodhpur", "udaipur", "srinagar", "gulmarg"];
  const hasNonAndamanContamination = currentPlan.some((day) => {
    const isl = String(day.primary_island || "").toLowerCase();
    return nonAndamanSample.some((na) => isl.includes(na));
  });

  if (hasNonAndamanContamination) {
    const sanitized = { ...formData };
    const numDays = Math.max(1, Number(sanitized.number_of_days) || 5);
    const defaults = getDestinationDayDefaults("Andaman Islands");
    sanitized.daily_island_plan = Array.from({ length: numDays }).map((_, i) => {
      const def = defaults[i % defaults.length];
      return {
        day_number: i + 1,
        primary_island: resolvePrimaryIsland({ attractions: def.attractions }, i, "Andaman Islands"),
        attractions: [...def.attractions],
        activities: [],
        hotel: "",
        transfer_type: "Private Cab",
        ferry: "None",
        ferry_timing: "",
      };
    });
    return sanitized;
  }

  return formData;
}

interface WizardState {
  activeView: "dashboard" | "builder" | "crm" | "marketing";
  apiKey: string;
  step: number;
  formData: Partial<TripRequestType>;
  generatedItinerary: string | null;
  setActiveView: (view: "dashboard" | "builder" | "crm" | "marketing") => void;
  setApiKey: (key: string) => void;
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  updateFormData: (data: Partial<TripRequestType>) => void;
  setGeneratedItinerary: (text: string | null) => void;
  resetWizard: () => void;
}

export const useWizardStore = create<WizardState>()(
  persist(
    (set) => ({
      activeView: "dashboard",
      apiKey: "",
      step: 1,
      formData: defaultTripValues,
      generatedItinerary: null,
      setActiveView: (view) => set({ activeView: view }),
      setApiKey: (key) => set({ apiKey: key }),
      setStep: (step) => set({ step }),
      nextStep: () => set((state) => ({ step: Math.min(state.step + 1, 6) })),
      prevStep: () => set((state) => ({ step: Math.max(state.step - 1, 1) })),
      updateFormData: (data) =>
        set((state) => {
          const oldDest = (state.formData.destination || "").trim();
          const newDest = (data.destination || "").trim();
          const isDestSwitch = Boolean(newDest && oldDest && newDest.toLowerCase() !== oldDest.toLowerCase());

          let baseData = { ...state.formData };

          if (isDestSwitch) {
            const numDays = Math.max(1, Number(data.number_of_days ?? state.formData.number_of_days) || 2);
            const defaults = getDestinationDayDefaults(newDest);
            const isAndamanNew = newDest.toLowerCase().includes("andaman");

            const freshPlan = Array.from({ length: numDays }).map((_, i) => {
              const def = defaults[i % defaults.length];
              const resolvedIsland = isAndamanNew
                ? resolvePrimaryIsland({ attractions: def.attractions }, i, newDest)
                : def.region;
              return {
                day_number: i + 1,
                primary_island: resolvedIsland,
                attractions: [...def.attractions],
                activities: [] as string[],
                hotel: "",
                transfer_type: isAndamanNew ? "Private Cab" : "Private AC Chauffeur Sedan/SUV",
                ferry: "None",
                ferry_timing: "",
              };
            });

            // Wipe all destination-specific selections on destination switch
            baseData = {
              ...baseData,
              preferred_ferries: [],
              preferred_activities: [],
              included_activities: [],
              selected_hotels: [],
              hotel_selection_islands: [],
              selected_destinations: [],
              daily_island_plan: freshPlan,
            };
          }

          const newData = { ...baseData, ...data };

          if (!isDestSwitch && newData.number_of_days !== undefined) {
            const numDays = Number(newData.number_of_days) || 0;
            const currentPlan = newData.daily_island_plan || [];
            const dest = newData.destination || "Andaman Islands";
            const defaults = getDestinationDayDefaults(dest);
            const isAndaman = !dest || dest.toLowerCase().includes("andaman");

            if (currentPlan.length < numDays) {
              const toAdd = numDays - currentPlan.length;
              const newDays = Array.from({ length: toAdd }).map((_, i) => {
                const dayIdx = currentPlan.length + i;
                const def = defaults[dayIdx % defaults.length];
                const resolvedIsland = isAndaman
                  ? resolvePrimaryIsland({ attractions: def.attractions }, dayIdx, dest)
                  : def.region;
                return {
                  day_number: dayIdx + 1,
                  primary_island: resolvedIsland,
                  attractions: [...def.attractions],
                  activities: [],
                  hotel: "",
                  transfer_type: isAndaman ? "Private Cab" : "Private AC Chauffeur Sedan/SUV",
                  ferry: "None",
                  ferry_timing: "",
                };
              });
              newData.daily_island_plan = [...currentPlan, ...newDays];
            } else if (currentPlan.length > numDays) {
              newData.daily_island_plan = currentPlan.slice(0, numDays);
            }
          }

          return { formData: newData };
        }),
      setGeneratedItinerary: (text) => set({ generatedItinerary: text }),
      resetWizard: () => set({ step: 1, formData: defaultTripValues, generatedItinerary: null }),
    }),
    {
      name: 'itinerary-wizard-storage',
      version: 2,
      migrate: (persistedState: any, version: number) => {
        if (persistedState && persistedState.formData) {
          persistedState.formData = sanitizeDestinationFormData(persistedState.formData);
        }
        return persistedState;
      },
      partialize: (state) => ({
        activeView: state.activeView,
        apiKey: state.apiKey,
        formData: state.formData,
      }),
      onRehydrateStorage: () => (hydratedState) => {
        if (hydratedState) {
          hydratedState.generatedItinerary = null;
          if (typeof hydratedState.step !== 'number' || hydratedState.step > 6 || hydratedState.step < 1) {
            hydratedState.step = 1;
          }
          if (hydratedState.formData) {
            hydratedState.formData = sanitizeDestinationFormData(hydratedState.formData);
          }
        }
      },
    }
  )
);
