import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { TripRequestType, defaultTripValues } from './schema';
import { resolvePrimaryIsland } from './utils';

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

const GOA_TERMS = [
  "panaji", "fontainhas", "calangute", "baga", "candolim", "vagator", "anjuna",
  "miramar", "dona paula", "dudhsagar", "colva", "benaulim", "palolem", "agonda",
  "cavelossim", "aguada", "chapora", "morjim", "ashwem", "arambol", "mandovi"
];

const ANDAMAN_DAY_DEFAULTS = [
  { region: "Port Blair", attractions: ["Cellular Jail", "Corbyn's Cove Beach"] },
  { region: "Port Blair", attractions: ["Ross Island (NSCB Island)", "North Bay Island"] },
  { region: "Swaraj Dweep (Havelock)", attractions: ["Radhanagar Beach", "Kalapathar Beach"] },
  { region: "Swaraj Dweep (Havelock)", attractions: ["Elephant Beach"] },
  { region: "Shaheed Dweep (Neil)", attractions: ["Natural Bridge", "Laxmanpur Beach", "Bharatpur Beach"] },
  { region: "Port Blair", attractions: ["Chidiya Tapu", "Local Shopping"] },
  { region: "Port Blair", attractions: ["Departure"] },
];

function hasGoaTerm(text: string): boolean {
  const lower = String(text || "").toLowerCase();
  return GOA_TERMS.some((term) => lower.includes(term));
}

function sanitizeDayPlan(plan: any[], totalDays: number) {
  return Array.from({ length: totalDays }).map((_, i) => {
    const existing = plan[i] || {};
    const defaultData = ANDAMAN_DAY_DEFAULTS[i % ANDAMAN_DAY_DEFAULTS.length];

    const rawAttractions = Array.isArray(existing.attractions) ? existing.attractions : [];
    const cleanAttractions = rawAttractions.filter((a: string) => !hasGoaTerm(a));
    const effectiveAttractions = cleanAttractions.length > 0 ? cleanAttractions : defaultData.attractions;

    const isGoaPrimary = hasGoaTerm(existing.primary_island || "");
    const candidatePrimary = isGoaPrimary ? "" : existing.primary_island;
    const cleanPrimary = resolvePrimaryIsland(
      { primary_island: candidatePrimary, attractions: effectiveAttractions, ferry: existing.ferry },
      i
    );

    return {
      day_number: i + 1,
      primary_island: cleanPrimary,
      attractions: effectiveAttractions,
      activities: (existing.activities || []).filter((a: string) => !hasGoaTerm(a)),
      hotel: existing.hotel || "",
      transfer_type: existing.transfer_type || "Private Cab",
      ferry: existing.ferry || "None",
      ferry_timing: existing.ferry_timing || "",
    };
  });
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
          const newData = { ...state.formData, ...data };
          
          if (newData.number_of_days !== undefined) {
            const numDays = Number(newData.number_of_days) || 0;
            const currentPlan = newData.daily_island_plan || [];
            
            if (currentPlan.length < numDays) {
              const toAdd = numDays - currentPlan.length;
              const newDays = Array.from({ length: toAdd }).map((_, i) => {
                const dayIdx = currentPlan.length + i;
                const def = ANDAMAN_DAY_DEFAULTS[dayIdx % ANDAMAN_DAY_DEFAULTS.length];
                return {
                  day_number: dayIdx + 1,
                  primary_island: resolvePrimaryIsland({ attractions: def.attractions }, dayIdx),
                  attractions: def.attractions,
                  activities: [],
                  hotel: "",
                  transfer_type: "Private Cab",
                  ferry: "None",
                  ferry_timing: ""
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
          // Sanitize any legacy Goa data from previous storage
          if (hydratedState.formData) {
            if (hydratedState.formData.destination !== "Andaman Islands") {
              hydratedState.formData.destination = "Andaman Islands";
            }
            const numDays = Number(hydratedState.formData.number_of_days) || 2;
            const plan = hydratedState.formData.daily_island_plan || [];
            const hasLegacyGoa = plan.some((p: any) =>
              hasGoaTerm(p.primary_island) || (p.attractions || []).some(hasGoaTerm)
            );
            if (hasLegacyGoa || plan.length === 0) {
              hydratedState.formData.daily_island_plan = sanitizeDayPlan(plan, numDays);
            }
          }
        }
      },
    }
  )
);

