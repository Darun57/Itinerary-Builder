"use client";

import React, { useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { StepHeader } from "../StepHeader";
import { DailyPlanSection } from "./DailyPlanSection";

import { useQuery } from "@tanstack/react-query";
import { fetchAvailableDestinations } from "@/lib/api";
import { useWizardStore } from "../../store";
import { getDestinationDayDefaults } from "../../destinationDefaults";

export default function TripDetailsStep() {
  const { control, setValue, getValues } = useFormContext<TripRequestType>();
  const updateFormData = useWizardStore((s) => s.updateFormData);

  const arrivalDate = useWatch({ control, name: "arrival_date" });
  const departureDate = useWatch({ control, name: "departure_date" });

  const { data: availableDestinations } = useQuery({
    queryKey: ["available_destinations"],
    queryFn: () => fetchAvailableDestinations(),
  });

  const destinationOptions = React.useMemo(() => {
    if (availableDestinations && Array.isArray(availableDestinations) && availableDestinations.length > 0) {
      return availableDestinations.map((d: any) => ({
        label: d.name,
        value: d.name,
      }));
    }
    return [
      { label: "Andaman Islands", value: "Andaman Islands" },
      { label: "Goa", value: "Goa" },
      { label: "Rajasthan", value: "Rajasthan" },
      { label: "Jammu & Kashmir", value: "Jammu & Kashmir" },
    ];
  }, [availableDestinations]);

  const handleDestinationChange = (newDest: string) => {
    const currentDest = getValues("destination");
    if (newDest === currentDest) return;

    const numDays = Math.max(1, Number(getValues("number_of_days")) || 5);
    const defaults = getDestinationDayDefaults(newDest);
    const newPlan = Array.from({ length: numDays }, (_, i) => {
      const def = defaults[i % defaults.length];
      return {
        day_number: i + 1,
        primary_island: def.region,
        attractions: [...def.attractions],
        activities: [] as string[],
        hotel: "",
        transfer_type: "Private Cab",
        ferry: "None",
        ferry_timing: "",
      };
    });

    // Reset RHF form values
    setValue("destination", newDest, { shouldDirty: true });
    setValue("selected_destinations", [], { shouldDirty: true });
    setValue("selected_hotels", [], { shouldDirty: true });
    setValue("preferred_activities", [], { shouldDirty: true });
    setValue("included_activities", [], { shouldDirty: true });
    setValue("hotel_selection_islands", [], { shouldDirty: true });
    setValue("preferred_ferries", [], { shouldDirty: true });
    setValue("daily_island_plan", newPlan, { shouldDirty: true });

    // Sync reset to Zustand store
    updateFormData({
      destination: newDest,
      selected_destinations: [],
      selected_hotels: [],
      preferred_activities: [],
      included_activities: [],
      hotel_selection_islands: [],
      preferred_ferries: [],
      daily_island_plan: newPlan,
    });
  };

  useEffect(() => {
    if (arrivalDate && departureDate) {
      const arrival = new Date(arrivalDate);
      const departure = new Date(departureDate);
      
      if (!isNaN(arrival.getTime()) && !isNaN(departure.getTime())) {
        const diffTime = departure.getTime() - arrival.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays >= 0) {
          setValue("number_of_nights", diffDays);
          setValue("number_of_days", diffDays + 1);
        }
      }
    }
  }, [arrivalDate, departureDate, setValue]);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader title="Trip Details" description="Configure the destination, dates, pacing, and passengers." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          control={control}
          name="destination"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Primary Destination *</FormLabel>
              <Select
                onValueChange={(val: any) => {
                  field.onChange(val);
                  handleDestinationChange(String(val || ""));
                }}
                value={field.value || "Andaman Islands"}
              >
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select destination" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {destinationOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />


        <FormField
          control={control}
          name="trip_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Trip Type *</FormLabel>
              <Select onValueChange={field.onChange} value={field.value || "Leisure"}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Honeymoon">Honeymoon</SelectItem>
                  <SelectItem value="Family Vacation">Family Vacation</SelectItem>
                  <SelectItem value="Adventure">Adventure</SelectItem>
                  <SelectItem value="Leisure">Leisure</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <FormField
          control={control}
          name="arrival_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Arrival Date *</FormLabel>
              <FormControl>
                <Input type="date" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="departure_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Departure Date *</FormLabel>
              <FormControl>
                <Input type="date" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="flexible_travel_dates"
          render={({ field }) => (
            <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border border-border p-4 shadow-sm bg-background/50">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>
                  Flexible Dates
                </FormLabel>
                <FormDescription>
                  Customer is open to date changes.
                </FormDescription>
              </div>
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <FormField
          control={control}
          name="number_of_adults"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Adults *</FormLabel>
              <FormControl>
                <Input type="number" min="1" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="number_of_children"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Children</FormLabel>
              <FormControl>
                <Input type="number" min="0" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="number_of_infants"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Infants</FormLabel>
              <FormControl>
                <Input type="number" min="0" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="number_of_senior_citizens"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Seniors</FormLabel>
              <FormControl>
                <Input type="number" min="0" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          control={control}
          name="budget_category"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Budget Category *</FormLabel>
              <Select onValueChange={field.onChange} value={field.value || "Standard"}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select budget" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Standard">Standard</SelectItem>
                  <SelectItem value="Premium">Premium</SelectItem>
                  <SelectItem value="Luxury">Luxury</SelectItem>
                  <SelectItem value="Ultra Luxury">Ultra Luxury</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="trip_pace"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Trip Pace *</FormLabel>
              <Select onValueChange={field.onChange} value={field.value || "Moderate"}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select pace" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Relaxed">Relaxed (1 activity/day)</SelectItem>
                  <SelectItem value="Moderate">Moderate (2 activities/day)</SelectItem>
                  <SelectItem value="Fast">Fast-Paced (Packed schedule)</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      {/* Day-wise Itinerary Style Selection */}
      <FormField
        control={control}
        name="day_wise_style"
        render={({ field }) => (
          <FormItem className="space-y-3">
            <div>
              <FormLabel className="text-base font-semibold">DAY-WISE ITINERARY STYLE</FormLabel>
              <FormDescription>
                Choose how the daily itinerary content is written and presented.
              </FormDescription>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Option 1: Luxury Narrative */}
              <div
                onClick={() => field.onChange("luxury_narrative")}
                className={`cursor-pointer rounded-xl p-4 border transition-all duration-200 flex flex-col justify-between ${
                  (field.value || "luxury_narrative") === "luxury_narrative"
                    ? "border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_15px_rgba(212,175,55,0.15)]"
                    : "border-border/60 bg-card/40 hover:border-border hover:bg-card/60"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <input
                      type="radio"
                      name="day_wise_style"
                      checked={(field.value || "luxury_narrative") === "luxury_narrative"}
                      onChange={() => field.onChange("luxury_narrative")}
                      className="accent-[#D4AF37] h-4 w-4"
                    />
                    <span className="font-semibold text-foreground text-sm">
                      Luxury Narrative
                    </span>
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-primary/10 text-primary">
                    Default
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                  Detailed, polished travel storytelling for premium proposals.
                </p>
              </div>

              {/* Option 2: Simple Itinerary */}
              <div
                onClick={() => field.onChange("simple_itinerary")}
                className={`cursor-pointer rounded-xl p-4 border transition-all duration-200 flex flex-col justify-between ${
                  field.value === "simple_itinerary"
                    ? "border-[#25D366] bg-[#25D366]/10 shadow-[0_0_15px_rgba(37,211,102,0.15)]"
                    : "border-border/60 bg-card/40 hover:border-border hover:bg-card/60"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <input
                      type="radio"
                      name="day_wise_style"
                      checked={field.value === "simple_itinerary"}
                      onChange={() => field.onChange("simple_itinerary")}
                      className="accent-[#25D366] h-4 w-4"
                    />
                    <span className="font-semibold text-foreground text-sm">
                      Simple Itinerary
                    </span>
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                    Operational
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                  Short, practical day-wise schedule for quick client reading.
                </p>
              </div>
            </div>
            <FormMessage />
          </FormItem>
        )}
      />

      <DailyPlanSection numberOfDays={useWatch({ control, name: "number_of_days" }) || 0} />
    </div>
  );
}
