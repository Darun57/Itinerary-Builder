"use client";

import React from "react";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import { useQuery } from "@tanstack/react-query";
import { fetchActivityRecommendations } from "@/lib/api";
import { useWizardStore } from "../../store";
import { StepHeader } from "../StepHeader";

const SPECIAL_OCCASIONS = [
  "Honeymoon / Anniversary", "Birthday", "Babymoon", 
  "Pre-wedding Shoot", "Proposal"
];

export default function ActivitiesStep() {
  const { control, getValues } = useFormContext<TripRequestType>();
  const formData = useWizardStore(state => state.formData);
  const currentRequestData = { ...formData, ...getValues() };

  const { data: recommendedActivities, isLoading, isError } = useQuery({
    queryKey: ["activities", currentRequestData.destination, currentRequestData.trip_type],
    queryFn: () => fetchActivityRecommendations(currentRequestData),
    staleTime: 1000 * 60 * 5,
  });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader title="Activities & Sightseeing" description="Select the preferred activities and any special events." />

      <div>
        <h3 className="mb-4 text-lg font-medium">Recommended Activities</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Tailored for a {currentRequestData.trip_type} trip to {currentRequestData.destination}.
        </p>

        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground animate-pulse border border-dashed border-border rounded-lg bg-background/20">
            Curating activities...
          </div>
        ) : isError ? (
          <div className="p-4 text-sm text-destructive border border-destructive/20 rounded-md bg-destructive/10">
            Failed to load activity recommendations. Ensure the backend is running.
          </div>
        ) : (
          <FormField
            control={control}
            name="preferred_activities"
            render={() => (
              <FormItem>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendedActivities?.map((activity: any) => (
                    <FormField
                      key={activity.activity_name}
                      control={control}
                      name="preferred_activities"
                      render={({ field }) => {
                        return (
                          <FormItem
                            key={activity.activity_name}
                            className="flex flex-row items-start space-x-3 space-y-0 rounded-md border border-border p-4 bg-background/50"
                          >
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(activity.activity_name)}
                                onCheckedChange={(checked) => {
                                  return checked
                                    ? field.onChange([...(field.value || []), activity.activity_name])
                                    : field.onChange(
                                        field.value?.filter((value: string) => value !== activity.activity_name)
                                      )
                                }}
                              />
                            </FormControl>
                            <div className="space-y-1 leading-none">
                              <FormLabel className="font-medium cursor-pointer">
                                {activity.activity_name}
                              </FormLabel>
                              <FormDescription>
                                {activity.location} • {activity.category} • ₹{activity.price}
                              </FormDescription>
                            </div>
                          </FormItem>
                        )
                      }}
                    />
                  ))}
                  {recommendedActivities?.length === 0 && (
                    <div className="col-span-2 p-8 text-center text-muted-foreground border border-dashed border-border rounded-lg bg-background/20">
                      No activities found for the selected criteria.
                    </div>
                  )}
                </div>
                <FormMessage />
              </FormItem>
            )}
          />
        )}
      </div>

      <div className="pt-6 border-t border-border mt-8">
        <h3 className="mb-4 text-lg font-medium">Special Occasions</h3>
        <FormField
          control={control}
          name="special_occasions"
          render={() => (
            <FormItem>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {SPECIAL_OCCASIONS.map((occasion) => (
                  <FormField
                    key={occasion}
                    control={control}
                    name="special_occasions"
                    render={({ field }) => {
                      return (
                        <FormItem
                          key={occasion}
                          className="flex flex-row items-start space-x-3 space-y-0 rounded-md border border-border p-4 bg-background/50"
                        >
                          <FormControl>
                            <Checkbox
                              checked={field.value?.includes(occasion)}
                              onCheckedChange={(checked) => {
                                return checked
                                  ? field.onChange([...(field.value || []), occasion])
                                  : field.onChange(
                                      field.value?.filter((value: string) => value !== occasion)
                                    )
                              }}
                            />
                          </FormControl>
                          <FormLabel className="font-normal cursor-pointer">
                            {occasion}
                          </FormLabel>
                        </FormItem>
                      )
                    }}
                  />
                ))}
              </div>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </div>
  );
}
