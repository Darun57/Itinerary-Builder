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

export default function TripDetailsStep() {
  const { control, setValue } = useFormContext<TripRequestType>();

  const arrivalDate = useWatch({ control, name: "arrival_date" });
  const departureDate = useWatch({ control, name: "departure_date" });

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
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select destination" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Goa">Goa</SelectItem>
                  <SelectItem value="Lakshadweep">Lakshadweep</SelectItem>
                  <SelectItem value="Maldives">Maldives</SelectItem>
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
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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

      <DailyPlanSection numberOfDays={useWatch({ control, name: "number_of_days" }) || 0} />
    </div>
  );
}
