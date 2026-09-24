"use client";

import React from "react";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { StepHeader } from "../StepHeader";
import { CheckboxList } from "../CheckboxList";

const DIETS = ["Vegetarian", "Non-Vegetarian", "Jain", "Vegan", "Halal"];

export default function TransportMealsStep() {
  const { control } = useFormContext<TripRequestType>();

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader title="Transport & Meals" description="Configure transfers, flight rates, meal plans, and dietary preferences." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          control={control}
          name="transfer_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Transfer Type *</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select transfer type" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Private">Private Cabs</SelectItem>
                  <SelectItem value="Shared">Shared Coaches</SelectItem>
                  <SelectItem value="Self-Drive">Self-Drive / Rental</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="meal_plan"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Meal Plan *</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select meal plan" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="CP">CP (Breakfast Only)</SelectItem>
                  <SelectItem value="MAP">MAP (Breakfast & Dinner)</SelectItem>
                  <SelectItem value="AP">AP (All Meals)</SelectItem>
                  <SelectItem value="EP">EP (Room Only)</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="pt-6 border-t border-border mt-8">
        <h3 className="mb-4 text-lg font-medium flex items-center gap-2">
          <span>✈️</span> Flight Details & Package Pricing
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FormField
            control={control}
            name="flight_option"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Flight Status</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value || "Excluded"}>
                  <FormControl>
                    <SelectTrigger className="bg-background/50">
                      <SelectValue placeholder="Select flight status" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="Included">Included</SelectItem>
                    <SelectItem value="Excluded">Excluded</SelectItem>
                    <SelectItem value="Optional">Optional / On Request</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>Inclusion status in final proposal.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="flight_per_person_rate"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Flight Rate per Person (Up & Down ₹)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min="0"
                    placeholder="e.g. 12000"
                    className="bg-background/50"
                    {...field}
                  />
                </FormControl>
                <FormDescription>Round-trip rate per person.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="per_person_cost"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Per Person Cost (₹)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min="0"
                    placeholder="e.g. 30000"
                    className="bg-background/50"
                    {...field}
                  />
                </FormControl>
                <FormDescription>Package cost per person.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="total_package_cost"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Total Package Cost (₹)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min="0"
                    placeholder="e.g. 85000"
                    className="bg-background/50"
                    {...field}
                  />
                </FormControl>
                <FormDescription>Overall total package price.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="pt-6 border-t border-border mt-8">
        <h3 className="mb-4 text-lg font-medium">Dietary Requirements</h3>
        <CheckboxList name="food_preferences" items={DIETS} />
      </div>
    </div>
  );
}
