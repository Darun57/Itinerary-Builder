"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useQuery } from "@tanstack/react-query";
import { fetchHotelRecommendations } from "@/lib/api";
import { useWizardStore } from "../../store";
import { StepHeader } from "../StepHeader";
import { HotelCarousel } from "../HotelCarousel";

export default function AccommodationStep() {
  const { control, getValues, setValue } = useFormContext<TripRequestType>();
  const formData = useWizardStore(state => state.formData);

  const watchedValues = useWatch({ control });
  const [searchQuery, setSearchQuery] = useState("");

  const currentRequestData = { ...formData, ...getValues(), ...watchedValues } as TripRequestType;

  const { data: recommendedHotels, isLoading, isError } = useQuery({
    queryKey: [
      "hotels",
      currentRequestData.destination,
      currentRequestData.budget_category,
      currentRequestData.hotel_category_preference,
      currentRequestData.hotel_selection_islands?.join(","),
    ],
    queryFn: () => fetchHotelRecommendations(currentRequestData),
    staleTime: 1000 * 60 * 5,
  });

  // Group hotels by location
  const hotelsByLocation = useMemo(() => {
    if (!recommendedHotels) return {};
    const filtered =
      searchQuery.trim() === ""
        ? recommendedHotels
        : recommendedHotels.filter(
            (h: any) =>
              h.hotel_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              (h.description && h.description.toLowerCase().includes(searchQuery.toLowerCase()))
          );
    return filtered.reduce((acc: Record<string, any[]>, hotel: any) => {
      const loc = hotel.location || "Other";
      if (!acc[loc]) acc[loc] = [];
      acc[loc].push(hotel);
      return acc;
    }, {});
  }, [recommendedHotels, searchQuery]);

  const selectedHotels: string[] = (watchedValues.selected_hotels as string[]) || [];
  const dailyPlan = watchedValues.daily_island_plan || [];

  // Auto-assign hotels to days when selection changes
  useEffect(() => {
    if (!selectedHotels.length || !dailyPlan.length || !recommendedHotels) return;

    const hotelLocationMap: Record<string, string> = {};
    for (const h of recommendedHotels) {
      if (selectedHotels.includes(h.hotel_name)) {
        const loc = (h.location || "").toLowerCase().trim();
        if (!hotelLocationMap[loc]) hotelLocationMap[loc] = h.hotel_name;
      }
    }

    const currentPlan = getValues("daily_island_plan") || [];
    let updated = false;
    const newPlan = currentPlan.map((day: any) => {
      if (day.hotel && selectedHotels.includes(day.hotel)) return day;
      const islandKey = (day.primary_island || "").toLowerCase().trim();
      let matched = "";
      for (const [loc, name] of Object.entries(hotelLocationMap)) {
        if (islandKey && (islandKey.includes(loc) || loc.includes(islandKey))) { matched = name; break; }
      }
      if (!matched && selectedHotels.length > 0) matched = selectedHotels[0];
      if (matched && matched !== day.hotel) { updated = true; return { ...day, hotel: matched }; }
      return day;
    });
    if (updated) setValue("daily_island_plan", newPlan, { shouldDirty: true });
  }, [selectedHotels.join(","), recommendedHotels]);

  const numberOfDays = Number(currentRequestData.number_of_days) || 0;
  const arrivalDate = currentRequestData.arrival_date || "";

  const getDayLabel = (index: number) => {
    if (arrivalDate) {
      const d = new Date(arrivalDate);
      if (!isNaN(d.getTime())) {
        d.setDate(d.getDate() + index);
        return `Day ${index + 1} — ${d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}`;
      }
    }
    return `Day ${index + 1}`;
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader title="Accommodation" description="Select hotel categories and assign hotels to each day." />

      {/* Category selector */}
      <div className="grid grid-cols-1 gap-6">
        <FormField
          control={control}
          name="hotel_category_preference"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Hotel Category *</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value} value={field.value}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="2 Star">2 Star (Budget)</SelectItem>
                  <SelectItem value="3 Star">3 Star (Standard)</SelectItem>
                  <SelectItem value="4 Star">4 Star (Premium)</SelectItem>
                  <SelectItem value="5 Star">5 Star (Luxury)</SelectItem>
                  <SelectItem value="Boutique">Boutique &amp; Heritage</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      {/* Hotel carousels */}
      <div className="pt-6 border-t border-border mt-8 space-y-4">
        <div>
          <h3 className="text-lg font-medium">Recommended Hotels</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Based on budget ({currentRequestData.budget_category}) and category ({currentRequestData.hotel_category_preference || "Standard"}).
            Click cards to select; use arrows or swipe to browse.
          </p>
        </div>

        {/* Search */}
        <Input
          placeholder="Search hotels by name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-md bg-background/50"
        />

        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground animate-pulse border border-dashed border-border rounded-lg bg-background/20">
            Fetching hotel recommendations...
          </div>
        ) : isError ? (
          <div className="p-4 text-sm text-destructive border border-destructive/20 rounded-md bg-destructive/10">
            Failed to load hotel recommendations. Ensure the backend is running.
          </div>
        ) : Object.keys(hotelsByLocation).length === 0 ? (
          <div className="p-8 text-center text-muted-foreground border border-dashed border-border rounded-lg bg-background/20">
            No hotels found for the selected criteria.
          </div>
        ) : (
          <div className="space-y-10">
            {Object.entries(hotelsByLocation).map(([location, hotels]) => (
              <HotelCarousel key={location} hotels={hotels as any[]} location={location} />
            ))}
          </div>
        )}
      </div>

      {/* Day-wise Hotel Assignment */}
      {numberOfDays > 0 && selectedHotels.length > 0 && (
        <div className="pt-6 border-t border-border mt-8">
          <h3 className="mb-1 text-lg font-medium">Assign Hotel per Day</h3>
          <p className="text-sm text-muted-foreground mb-5">
            Assign which hotel the guest stays at each night. Same hotels across multiple days are automatically merged in the PDF.
          </p>
          <div className="space-y-3">
            {Array.from({ length: numberOfDays }).map((_, index) => (
              <FormField
                key={index}
                control={control}
                name={`daily_island_plan.${index}.hotel` as any}
                render={({ field }) => (
                  <FormItem className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-lg border border-border bg-card/50">
                    <FormLabel className="min-w-[180px] text-sm font-medium text-foreground shrink-0">
                      {getDayLabel(index)}
                    </FormLabel>
                    <Select onValueChange={field.onChange} value={field.value || ""}>
                      <FormControl>
                        <SelectTrigger className="bg-background/50 flex-1">
                          <SelectValue placeholder="Select hotel for this day..." />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {selectedHotels.map((name: string) => (
                          <SelectItem key={name} value={name}>{name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            ))}
          </div>

          {/* Stay summary */}
          <div className="mt-5 p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-1">
            <p className="font-semibold text-foreground text-sm mb-3">Stay Summary (PDF Preview)</p>
            {(() => {
              const plan = ((watchedValues.daily_island_plan as any[]) || []).slice(0, numberOfDays);
              const nightsMap: Record<string, number> = {};
              plan.forEach((day: any) => { if (day?.hotel) nightsMap[day.hotel] = (nightsMap[day.hotel] || 0) + 1; });
              const entries = Object.entries(nightsMap);
              if (!entries.length) return <p className="text-xs text-muted-foreground">No hotels assigned yet.</p>;
              return entries.map(([hotel, nights]) => (
                <div key={hotel} className="flex justify-between items-center text-sm">
                  <span className="text-foreground">{hotel}</span>
                  <span className="text-primary font-semibold">{nights} Night{nights !== 1 ? "s" : ""}</span>
                </div>
              ));
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
