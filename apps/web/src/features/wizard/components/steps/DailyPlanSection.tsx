import React from "react";
import { useFieldArray, useFormContext, useWatch } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { fetchAllDestinations, fetchAllActivities, fetchAllFerries } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { MultiSelect } from "@/components/ui/multi-select";

export function DailyPlanSection({ numberOfDays }: { numberOfDays: number }) {
  const { control, getValues } = useFormContext<TripRequestType>();
  const arrivalDateStr = useWatch({ control, name: "arrival_date" });
  
  const { fields, append, remove } = useFieldArray({
    control,
    name: "daily_island_plan",
  });

  React.useEffect(() => {
    if (numberOfDays > 0) {
      const currentPlan = getValues("daily_island_plan") || [];
      if (currentPlan.length < numberOfDays) {
        for (let i = currentPlan.length; i < numberOfDays; i++) {
          append({
            day_number: i + 1,
            primary_island: "",
            attractions: [],
            activities: [],
            hotel: "",
            transfer_type: "",
            ferry: "",
            ferry_timing: ""
          });
        }
      } else if (currentPlan.length > numberOfDays) {
        for (let i = currentPlan.length - 1; i >= numberOfDays; i--) {
          remove(i);
        }
      }
    }
  }, [numberOfDays, append, remove, getValues]);

  const { data: destinations } = useQuery({
    queryKey: ["all_destinations_v2"],
    queryFn: () => fetchAllDestinations(),
  });

  const { data: activities } = useQuery({
    queryKey: ["all_activities_v2"],
    queryFn: () => fetchAllActivities(),
  });

  const { data: ferries } = useQuery({
    queryKey: ["all_ferries_v2"],
    queryFn: () => fetchAllFerries(),
  });

  if (numberOfDays <= 0) return null;

  return (
    <div className="space-y-6 pt-6 border-t border-border mt-8 animate-in fade-in duration-500">
      <div>
        <h3 className="text-xl font-medium tracking-tight">Daily Planned</h3>
        <p className="text-sm text-muted-foreground">Select recommended islands and activities for each day.</p>
      </div>
      
      <div className="space-y-4">
        {fields.slice(0, numberOfDays).map((field, index) => {
          let dateDisplay = "";
          if (arrivalDateStr) {
            const arrivalDate = new Date(arrivalDateStr);
            if (!isNaN(arrivalDate.getTime())) {
              const currentDate = new Date(arrivalDate);
              currentDate.setDate(arrivalDate.getDate() + index);
              dateDisplay = ` — ${currentDate.toLocaleDateString("en-US", { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}`;
            }
          }

          return (
            <div key={field.id} className="p-4 rounded-lg border border-border bg-card/50 space-y-4">
              <h4 className="font-semibold text-primary">Day {index + 1}{dateDisplay}</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={control}
                name={`daily_island_plan.${index}.attractions`}
                render={({ field }) => {
                  const options = destinations
                    ?.filter((d: any) => d.destination_name)
                    .map((d: any) => ({
                      label: d.destination_name,
                      value: d.destination_name,
                    })) || [];

                  return (
                    <FormItem>
                      <FormLabel>Islands / Locations</FormLabel>
                      <FormControl>
                        <MultiSelect
                          options={options}
                          selected={field.value || []}
                          onChange={field.onChange}
                          placeholder="Select locations..."
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  );
                }}
              />

              <FormField
                control={control}
                name={`daily_island_plan.${index}.activities`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Activities (Comma separated)</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="e.g. Scuba Diving, Beach Walk" 
                        value={field.value?.join(", ") || ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          field.onChange(val ? val.split(",").map(s => s.trim()) : []);
                        }}
                        className="bg-background/50" 
                      />
                    </FormControl>
                    <FormMessage />
                    {activities && activities.length > 0 && (
                      <div className="text-xs text-muted-foreground mt-1">
                        <span className="font-medium text-foreground">Suggestions:</span> {activities.slice(0, 5).map((a: any) => a.activity_name).join(", ")}
                      </div>
                    )}
                  </FormItem>
                )}
              />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={control}
                  name={`daily_island_plan.${index}.ferry`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Ferry</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value || ""} value={field.value || ""}>
                        <FormControl>
                          <SelectTrigger className="bg-background/50">
                            <SelectValue placeholder="Select ferry" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="None">None</SelectItem>
                          {ferries?.filter((f: any) => f.operator && f.ferry_id)?.map((f: any) => (
                            <SelectItem key={f.ferry_id} value={`${f.operator} (${f.from_location} to ${f.to_location})`}>
                              {f.operator} ({f.from_location} to {f.to_location})
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
                  name={`daily_island_plan.${index}.ferry_timing`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Ferry Timings</FormLabel>
                      <FormControl>
                        <Input 
                          placeholder="e.g. 08:00 AM" 
                          {...field} 
                          value={field.value || ""}
                          className="bg-background/50" 
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
        )})}
      </div>
    </div>
  );
}
