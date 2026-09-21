"use client";

import React from "react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { tripRequestSchema, TripRequestType } from "../schema";
import { useWizardStore } from "../store";
import { useMutation } from "@tanstack/react-query";
import { generateAIItinerary } from "@/lib/api";
import { resolvePrimaryIsland } from "../utils";
import { Loader2 } from "lucide-react";

import CustomerStep from "./steps/CustomerStep";
import TripDetailsStep from "./steps/TripDetailsStep";
import AccommodationStep from "./steps/AccommodationStep";
import ActivitiesStep from "./steps/ActivitiesStep";
import TransportMealsStep from "./steps/TransportMealsStep";
import WizardStepper from "./WizardStepper";
import ItineraryPreview from "./ItineraryPreview";
import { TripSummarySidebar } from "./TripSummarySidebar";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function WizardForm() {
  const { step, formData, generatedItinerary, setStep, nextStep, prevStep, updateFormData, setGeneratedItinerary, apiKey } = useWizardStore();

  const methods = useForm<TripRequestType>({
    resolver: zodResolver(tripRequestSchema) as any,
    defaultValues: formData as TripRequestType,
    mode: "onTouched",
  });

  const { handleSubmit, trigger, formState: { errors } } = methods;

  const aiMutation = useMutation({
    mutationFn: (data: TripRequestType) => generateAIItinerary(data, apiKey),
    onSuccess: (data) => {
      setGeneratedItinerary(data.itinerary_text);
    },
    onError: (error) => {
      console.error("AI Generation failed:", error);
      alert(`Failed to generate itinerary: ${error.message || "The backend encountered an error or Gemini took too long. Please try again."}`);
    }
  });


  // Render the glowing loading screen while Gemini is thinking
  if (aiMutation.isPending) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center space-y-6 animate-in fade-in duration-500 mt-8">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
          <Loader2 className="w-16 h-16 text-primary animate-spin relative z-10" />
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">Consulting the Oracle...</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Gemini AI is currently processing your selections and drafting a highly personalized, luxury itinerary. This usually takes 10 to 20 seconds.
          </p>
        </div>
      </div>
    );
  }

  const handleNext = async () => {
    // Validate current step fields before proceeding
    let fieldsToValidate: (keyof TripRequestType)[] = [];

    switch (step) {
      case 1:
        fieldsToValidate = ['customer_name', 'customer_nationality', 'customer_country', 'customer_email', 'customer_phone_number'];
        break;
      case 2:
        fieldsToValidate = ['destination', 'arrival_date', 'departure_date', 'number_of_nights', 'number_of_days', 'trip_type', 'budget_category', 'number_of_adults', 'trip_pace'];
        break;
      case 3:
        fieldsToValidate = ['hotel_category_preference'];
        break;
      case 5:
        fieldsToValidate = ['transfer_type', 'meal_plan'];
        break;
    }

    const isStepValid = fieldsToValidate.length > 0 ? await trigger(fieldsToValidate) : true;

    if (isStepValid) {
      updateFormData(methods.getValues());
      nextStep();
    } else {
      alert("Validation failed! Check the red text under the fields or the debug box below.");
    }
  };

  const onSubmit = (data: any) => {
    if (step < 6) {
      handleNext();
      return;
    }
    if (data.daily_island_plan && data.number_of_days) {
      const plan = data.daily_island_plan.slice(0, data.number_of_days);
      
      data.daily_island_plan = plan.map((day: any, idx: number) => {
        const cleanAttractions = day.attractions || [];
        const primaryIsland = resolvePrimaryIsland(day, idx);
        const transferType = day.transfer_type || data.transfer_type || "Private Cab";
        const isLastDay = idx === plan.length - 1;
        const isDeparture = isLastDay && (
          primaryIsland.toLowerCase().trim() === "departure" ||
          cleanAttractions.some((a: string) => String(a).toLowerCase().trim() === "departure")
        );

        return {
          ...day,
          day_number: idx + 1,
          primary_island: primaryIsland,
          attractions: cleanAttractions.length > 0 ? cleanAttractions : (idx === 0 ? ["Cellular Jail", "Corbyn's Cove Beach"] : ["Radhanagar Beach", "Elephant Beach"]),
          transfer_type: transferType,
          ferry: day.ferry || "None",
          hotel: isDeparture ? "" : (day.hotel || ""),
        };
      });
    }
    updateFormData(data);
    aiMutation.mutate(data);
  };

  return (
    <div className="flex flex-col w-full min-w-0 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Welcome Header */}
      <div className="welcome">
        <div>
          <h1>Itinerary builder</h1>
          <p>Step {step} of 6 — capture the trip essentials.</p>
        </div>
      </div>

      <WizardStepper />

      {/* Render the glowing loading screen while Gemini is thinking */}
      {aiMutation.isPending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-md">
          <div className="flex flex-col items-center">
            <Loader2 className="w-16 h-16 animate-spin text-primary mb-4" />
            <h2 className="text-2xl font-bold tracking-tight text-primary">Consulting the Oracle...</h2>
            <p className="text-muted-foreground mt-2">Crafting a bespoke luxury itinerary...</p>
          </div>
        </div>
      )}

      {/* Render Itinerary Preview after successful generation */}
      {generatedItinerary ? (
        <ItineraryPreview />
      ) : (
        <FormProvider {...methods}>
          <form 
            onSubmit={handleSubmit(onSubmit)} 
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT") {
                e.preventDefault();
                if (step < 6) {
                  handleNext();
                }
              }
            }}
            className="builder-grid"
          >

            {/* LEFT SIDE: Active Form Step */}
            <div className="form-card">
              {step === 1 && <CustomerStep />}
              {step === 2 && <TripDetailsStep />}
              {step === 3 && <AccommodationStep />}
              {step === 4 && <ActivitiesStep />}
              {step === 5 && <TransportMealsStep />}
              {step === 6 && (
                <div>
                  <h2 style={{ fontFamily: "var(--font-heading, serif)", fontWeight: 700, fontSize: "22px", marginBottom: "6px" }}>Ready to Generate</h2>
                  <p className="sub">All details are captured. Click the button below to generate your AI-powered itinerary.</p>
                  <div style={{ marginTop: "28px", display: "flex", flexDirection: "column", gap: "14px" }}>
                    {[
                      { icon: "ti-user", label: "Customer", value: methods.getValues("customer_name") || "—" },
                      { icon: "ti-map-pin", label: "Destination", value: methods.getValues("destination") || "—" },
                      { icon: "ti-calendar", label: "Travel dates", value: `${methods.getValues("arrival_date") || "—"} → ${methods.getValues("departure_date") || "—"}` },
                      { icon: "ti-building", label: "Hotels", value: methods.getValues("hotel_category_preference") || "—" },
                      { icon: "ti-car", label: "Transfer", value: methods.getValues("transfer_type") || "—" },
                      { icon: "ti-tools-kitchen-2", label: "Meal Plan", value: methods.getValues("meal_plan") || "—" },
                      { icon: "ti-file-text", label: "Writing Style", value: methods.getValues("day_wise_style") === "simple_itinerary" ? "Simple Itinerary (Operational)" : "Luxury Narrative" },
                    ].map(item => (
                      <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px 16px", background: "#F9FAFB", borderRadius: "10px", border: "1px solid #E5E7EB" }}>
                        <div style={{ width: "34px", height: "34px", borderRadius: "9px", background: "rgba(20,33,61,0.07)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--navy)", flexShrink: 0 }}>
                          <i className={`ti ${item.icon}`} style={{ fontSize: "16px" }} />
                        </div>
                        <div>
                          <div style={{ fontSize: "11px", color: "#9CA3AF", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>{item.label}</div>
                          <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#111827", marginTop: "2px" }}>{item.value}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="builder-nav">
                {step > 1 ? (
                  <button type="button" onClick={() => { updateFormData(methods.getValues()); prevStep(); }} className="btn-ghost">
                    <i className="ti ti-arrow-left"></i>Back
                  </button>
                ) : (
                  <div />
                )}

                {step < 5 ? (
                  <button type="button" onClick={handleNext} className="btn-gold">
                    Next Step<i className="ti ti-arrow-right"></i>
                  </button>
                ) : step === 5 ? (
                  <button type="button" onClick={handleNext} className="btn-gold">
                    Review & Generate<i className="ti ti-arrow-right"></i>
                  </button>
                ) : (
                  <button type="submit" className="btn-gold" disabled={aiMutation.isPending}>
                    {aiMutation.isPending ? "Generating..." : "Generate Itinerary"}
                    <i className="ti ti-wand"></i>
                  </button>
                )}
              </div>

              {/* DEBUG BOX */}
              {Object.keys(errors).length > 0 && (
                <div className="mt-8 p-4 bg-destructive/10 text-destructive border border-destructive rounded text-xs overflow-auto">
                  <strong>Validation Errors (Debug):</strong>
                  <pre>{JSON.stringify(errors, null, 2)}</pre>
                </div>
              )}
            </div>

            {/* RIGHT SIDE: Sticky Summary */}
            <TripSummarySidebar />

          </form>
        </FormProvider>
      )}
    </div>
  );
}
