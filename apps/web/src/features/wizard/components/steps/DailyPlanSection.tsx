import React from "react";
import { useFieldArray, useFormContext, useWatch } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { fetchAllDestinations, fetchAllFerries } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { MultiSelect } from "@/components/ui/multi-select";
import { Ship, Clock, MapPin } from "lucide-react";
import { resolvePrimaryIsland, CANONICAL_ISLANDS } from "../../utils";

const ANDAMAN_DAY_DEFAULTS = [
  { region: "Port Blair", attractions: ["Cellular Jail", "Corbyn's Cove Beach", "Marina Park and Flag Point"] },
  { region: "Port Blair", attractions: ["Ross Island (NSCB Island)", "North Bay Island", "Chidiya Tapu"] },
  { region: "Swaraj Dweep (Havelock)", attractions: ["Radhanagar Beach", "Elephant Beach", "Kalapathar Beach"] },
  { region: "Shaheed Dweep (Neil)", attractions: ["Bharatpur Beach", "Natural Bridge", "Laxmanpur Beach"] },
  { region: "Baratang", attractions: ["Limestone Caves", "Mud Volcano", "Jolly Buoy Island"] },
  { region: "Port Blair", attractions: ["Samudrika Naval Marine Museum", "Chatham Saw Mill", "Anthropological Museum"] },
];

export function DailyPlanSection({ numberOfDays }: { numberOfDays: number }) {
  const { control, getValues, setValue } = useFormContext<TripRequestType>();
  const arrivalDateStr = useWatch({ control, name: "arrival_date" });
  
  const { fields, append, remove } = useFieldArray({
    control,
    name: "daily_island_plan",
  });

  const { data: destinations } = useQuery({
    queryKey: ["all_destinations_v2"],
    queryFn: () => fetchAllDestinations(),
  });

  const { data: ferries } = useQuery({
    queryKey: ["all_ferries_v2"],
    queryFn: () => fetchAllFerries(),
  });

  const groupedFerries = React.useMemo(() => {
    if (!ferries || !Array.isArray(ferries)) return [];

    const categories: { label: string; items: any[] }[] = [
      { label: "Makruzz Cruise", items: [] },
      { label: "Nautika Cruise", items: [] },
      { label: "Green Ocean Cruise", items: [] },
      { label: "ITT Majestic Cruise", items: [] },
      { label: "Flexible / Unconfirmed (Makruzz / Nautika / Green Ocean)", items: [] },
      { label: "10+2 Seater Speed Boats", items: [] },
      { label: "Government Ferries", items: [] },
    ];

    ferries
      .filter((f: any) => f.operator && f.ferry_id)
      .forEach((f: any) => {
        const op = (f.operator || "").toLowerCase();
        if (op === "makruzz") {
          categories[0].items.push(f);
        } else if (op === "nautika") {
          categories[1].items.push(f);
        } else if (op === "green ocean") {
          categories[2].items.push(f);
        } else if (op === "itt majestic") {
          categories[3].items.push(f);
        } else if (op.includes(" or ") || op.includes(" / ")) {
          categories[4].items.push(f);
        } else if (op.includes("speed boat") || op.includes("10+2")) {
          categories[5].items.push(f);
        } else if (op.includes("government") || op.includes("dss") || op.includes("vessel")) {
          categories[6].items.push(f);
        } else {
          categories[4].items.push(f);
        }
      });

    return categories.filter((g) => g.items.length > 0);
  }, [ferries]);

  const validDestinations = React.useMemo(() => {
    return (destinations || [])
      .filter((d: any) => d.destination_name)
      .map((d: any) => ({
        label: d.destination_name,
        value: d.destination_name,
      }));
  }, [destinations]);

  React.useEffect(() => {
    if (numberOfDays > 0) {
      const currentPlan = getValues("daily_island_plan") || [];
      if (currentPlan.length < numberOfDays) {
        for (let i = currentPlan.length; i < numberOfDays; i++) {
          const def = ANDAMAN_DAY_DEFAULTS[i % ANDAMAN_DAY_DEFAULTS.length];
          const resolvedIsland = resolvePrimaryIsland({ attractions: def.attractions }, i);
          append({
            day_number: i + 1,
            primary_island: resolvedIsland,
            attractions: def.attractions,
            activities: [],
            hotel: "",
            transfer_type: "Private Cab",
            ferry: "None",
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

  if (numberOfDays <= 0) return null;

  return (
    <div className="space-y-6 pt-6 border-t border-border mt-8 animate-in fade-in duration-500">
      <div>
        <h3 className="text-xl font-medium tracking-tight">Daily Planned</h3>
        <p className="text-sm text-muted-foreground">Select recommended destinations, locations, and inter-island cruise / boat transfers for each day.</p>
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
                {/* Column 1: Regions / Locations */}
                <FormField
                  control={control}
                  name={`daily_island_plan.${index}.attractions`}
                  render={({ field }) => {
                    const defaultAttractions = ANDAMAN_DAY_DEFAULTS[index % ANDAMAN_DAY_DEFAULTS.length].attractions;
                    const currentValues = field.value || [];
                    
                    // Filter valid destination names
                    const cleanValues = validDestinations.length > 0
                      ? currentValues.filter((v: string) =>
                          validDestinations.some((d: any) => d.value.toLowerCase() === v.toLowerCase())
                        )
                      : currentValues;

                    // If user has empty list, apply Andaman defaults
                    const effectiveValues = cleanValues.length > 0 ? cleanValues : defaultAttractions;

                    return (
                      <FormItem>
                        <FormLabel>Regions / Locations</FormLabel>
                        <FormControl>
                          <MultiSelect
                            options={validDestinations}
                            selected={effectiveValues}
                            onChange={(newVals) => {
                              field.onChange(newVals);
                              const currentFerry = getValues(`daily_island_plan.${index}.ferry` as any);
                              const resolved = resolvePrimaryIsland({ attractions: newVals, ferry: currentFerry }, index);
                              setValue(`daily_island_plan.${index}.primary_island` as any, resolved, { shouldDirty: true });
                            }}
                            placeholder="Select Andaman destinations..."
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    );
                  }}
                />

                {/* Column 2: Cruise / Boat Transfer (Takes the place of Activities) */}
                <FormField
                  control={control}
                  name={`daily_island_plan.${index}.ferry`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1.5">
                        <Ship className="h-3.5 w-3.5 text-primary" />
                        <span>Cruise / Boat Transfer</span>
                      </FormLabel>
                      <Select 
                        onValueChange={(val) => {
                          field.onChange(val);
                          const currentAttractions = getValues(`daily_island_plan.${index}.attractions` as any);
                          const resolved = resolvePrimaryIsland({ attractions: currentAttractions, ferry: val }, index);
                          setValue(`daily_island_plan.${index}.primary_island` as any, resolved, { shouldDirty: true });
                        }} 
                        value={field.value || "None"}
                      >
                        <FormControl>
                          <SelectTrigger className="bg-background/50 w-full">
                            <SelectValue placeholder="Select cruise or boat transfer" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent className="max-h-80 w-[440px]">
                          <SelectItem value="None">None (Road / No Water Transfer)</SelectItem>
                          {groupedFerries.map((group) => (
                            <SelectGroup key={group.label}>
                              <SelectLabel className="font-semibold text-xs text-primary px-2 py-1 bg-muted/40 border-y border-border/40">
                                {group.label}
                              </SelectLabel>
                              {group.items.map((f: any) => (
                                <SelectItem key={f.ferry_id} value={`${f.operator} (${f.from_location} to ${f.to_location})`}>
                                  {f.operator} ({f.from_location} to {f.to_location})
                                </SelectItem>
                              ))}
                            </SelectGroup>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={control}
                  name={`daily_island_plan.${index}.ferry_timing`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>Transfer Timings</span>
                      </FormLabel>
                      <FormControl>
                        <Input 
                          placeholder="e.g. 08:00 AM or Morning Cruise" 
                          {...field} 
                          value={field.value || ""}
                          className="bg-background/50" 
                        />
                      </FormControl>
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] text-muted-foreground">Quick set:</span>
                        {["06:00 AM", "08:00 AM", "08:30 AM", "11:30 AM", "02:00 PM", "03:30 PM", "Flexible"].map((time) => (
                          <button
                            key={time}
                            type="button"
                            onClick={() => field.onChange(time)}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-muted/60 hover:bg-primary/20 hover:text-primary transition-colors cursor-pointer border border-border/50"
                          >
                            {time}
                          </button>
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Column 2: Island / Destination */}
                <FormField
                  control={control}
                  name={`daily_island_plan.${index}.primary_island`}
                  render={({ field: islandField }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-primary" />
                        <span>Island / Destination</span>
                      </FormLabel>
                      <Select 
                        onValueChange={islandField.onChange} 
                        value={islandField.value || resolvePrimaryIsland(getValues(`daily_island_plan.${index}` as any), index)}
                      >
                        <FormControl>
                          <SelectTrigger className="bg-background/50 w-full">
                            <SelectValue placeholder="Select island" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {CANONICAL_ISLANDS.map((isl) => (
                            <SelectItem key={isl} value={isl}>
                              {isl}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
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
