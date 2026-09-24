import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { TripRequestType, defaultTripValues } from './schema';

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
          const newData = { ...state.formData, ...data };
          
          if (newData.number_of_days !== undefined) {
            const numDays = Number(newData.number_of_days) || 0;
            const currentPlan = newData.daily_island_plan || [];
            
            if (currentPlan.length < numDays) {
              const toAdd = numDays - currentPlan.length;
              const newDays = Array.from({ length: toAdd }).map((_, i) => ({
                day_number: currentPlan.length + i + 1,
                primary_island: "",
                attractions: [],
                activities: [],
                hotel: "",
                transfer_type: "",
                ferry: "",
                ferry_timing: ""
              }));
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
        }
      },
    }
  )
);
