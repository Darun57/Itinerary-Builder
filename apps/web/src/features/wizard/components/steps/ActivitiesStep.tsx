"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useFormContext } from "react-hook-form";
import { TripRequestType, IncludedActivityType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { useQuery } from "@tanstack/react-query";
import { fetchAllActivities, fetchActivityRecommendations } from "@/lib/api";
import { useWizardStore } from "../../store";
import { resolvePrimaryIsland } from "../../utils";
import { StepHeader } from "../StepHeader";
import {
  Search,
  Gift,
  Plus,
  Minus,
  Sparkles,
  MapPin,
  Clock,
  CheckCircle2,
  X,
  Compass,
  Layers,
  Calendar,
  SunMedium,
  Check,
  Trash2,
  SlidersHorizontal,
  Users,
} from "lucide-react";

interface ActivityItem {
  activity_id: string;
  activity_name: string;
  location: string;
  price: string | number;
  duration: string;
  category: string;
  description: string;
}

const SPECIAL_OCCASIONS = [
  "Honeymoon / Anniversary",
  "Birthday",
  "Babymoon",
  "Pre-wedding Shoot",
  "Proposal",
  "Candlelight Beach Dinner",
];

const ISLAND_TABS = [
  { id: "all", label: "All Islands" },
  { id: "port_blair", label: "Port Blair", match: "Port Blair" },
  { id: "havelock", label: "Havelock (Swaraj Dweep)", match: "Havelock" },
  { id: "neil", label: "Neil (Shaheed Dweep)", match: "Neil" },
  { id: "baratang", label: "Baratang", match: "Baratang" },
  { id: "diglipur", label: "Diglipur & North", match: "Diglipur" },
  { id: "middle_little", label: "Middle & Little Andaman", match: ["Middle", "Little", "Rangat", "Mayabunder"] },
];

const CATEGORY_FILTERS = [
  "All Categories",
  "Diving",
  "Water Sports",
  "Adventure",
  "Heritage",
  "Nature",
  "Beach",
  "Trekking",
  "Cruises",
  "Culinary",
  "Cultural",
];

export default function ActivitiesStep() {
  const { control, watch, setValue, getValues } = useFormContext<TripRequestType>();
  const formData = useWizardStore((state) => state.formData);
  const currentRequestData = { ...formData, ...getValues() };

  // Watchers
  const preferredActivities = watch("preferred_activities") || [];
  const includedActivities = watch("included_activities") || [];
  const dailyPlan = watch("daily_island_plan") || [];
  const rawNumDays = Number(watch("number_of_days") || currentRequestData.number_of_days || 1);
  const numberOfDays = Math.max(1, isNaN(rawNumDays) ? 1 : rawNumDays);

  // Total tourists (adults + children + seniors + infants)
  const rawNumAdults = Number(watch("number_of_adults") ?? currentRequestData.number_of_adults ?? 2);
  const rawNumChildren = Number(watch("number_of_children") ?? currentRequestData.number_of_children ?? 0);
  const rawNumSeniors = Number(watch("number_of_senior_citizens") ?? currentRequestData.number_of_senior_citizens ?? 0);
  const rawNumInfants = Number(watch("number_of_infants") ?? currentRequestData.number_of_infants ?? 0);
  const totalTourists = Math.max(
    1,
    (isNaN(rawNumAdults) ? 2 : rawNumAdults) +
    (isNaN(rawNumChildren) ? 0 : rawNumChildren) +
    (isNaN(rawNumSeniors) ? 0 : rawNumSeniors) +
    (isNaN(rawNumInfants) ? 0 : rawNumInfants)
  );

  // Active Day view: null means "All Days / Global Catalog", number means Day index (0-based)
  const [activeDayIndex, setActiveDayIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"day_wise" | "catalog">("day_wise");

  // Local UI filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIsland, setSelectedIsland] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("All Categories");
  const [showOnlyIncluded, setShowOnlyIncluded] = useState(false);

  // Ensure daily_island_plan has entries for all days and accurate primary_island
  useEffect(() => {
    const current = getValues("daily_island_plan") || [];
    let changed = false;
    const updated = [...current];

    for (let i = updated.length; i < numberOfDays; i++) {
      changed = true;
      updated.push({
        day_number: i + 1,
        primary_island: resolvePrimaryIsland({}, i),
        attractions: [],
        activities: [],
        hotel: "",
        transfer_type: "Private",
      });
    }

    for (let i = 0; i < Math.min(updated.length, numberOfDays); i++) {
      const resolved = resolvePrimaryIsland(updated[i], i);
      if (updated[i].primary_island !== resolved) {
        updated[i] = { ...updated[i], primary_island: resolved };
        changed = true;
      }
    }

    if (changed) {
      setValue("daily_island_plan", updated, { shouldDirty: false });
    }
  }, [numberOfDays, setValue, getValues, dailyPlan]);

  // Fetch all activities
  const {
    data: allActivities = [],
    isLoading: isLoadingAll,
    isError: isErrorAll,
  } = useQuery<ActivityItem[]>({
    queryKey: ["all_activities"],
    queryFn: fetchAllActivities,
    staleTime: 1000 * 60 * 10,
  });

  // Fetch recommended activities for badge
  const { data: recommendedActivities = [] } = useQuery<ActivityItem[]>({
    queryKey: ["recommended_activities", currentRequestData.destination, currentRequestData.trip_type],
    queryFn: () => fetchActivityRecommendations(currentRequestData),
    staleTime: 1000 * 60 * 5,
  });

  const recommendedNames = useMemo(() => {
    return new Set(recommendedActivities.map((a: ActivityItem) => a.activity_name.toLowerCase()));
  }, [recommendedActivities]);

  // Map of activity name -> free quantity
  const includedMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of includedActivities) {
      if (item && item.activity_name) {
        map.set(item.activity_name, item.quantity || 0);
      }
    }
    return map;
  }, [includedActivities]);

  // Map of activity name -> Set of Day numbers (1-indexed) where it is scheduled
  const activityDayMap = useMemo(() => {
    const map = new Map<string, Set<number>>();
    dailyPlan.forEach((dp, idx) => {
      const acts = dp.activities || [];
      acts.forEach((actName) => {
        if (!map.has(actName)) {
          map.set(actName, new Set());
        }
        map.get(actName)!.add(dp.day_number || idx + 1);
      });
    });
    return map;
  }, [dailyPlan]);

  // Helper to re-synchronize preferred_activities array from all daily plans + free inclusions
  const syncPreferredActivities = (newPlan: typeof dailyPlan, newIncluded: typeof includedActivities) => {
    const actSet = new Set<string>();
    newPlan.forEach((dp) => {
      (dp.activities || []).forEach((a) => {
        if (a && a.trim()) actSet.add(a.trim());
      });
    });
    newIncluded.forEach((inc) => {
      if (inc && inc.activity_name && inc.quantity > 0) {
        actSet.add(inc.activity_name.trim());
      }
    });
    setValue("preferred_activities", Array.from(actSet), { shouldValidate: true, shouldDirty: true });
  };

  // Toggle activity on a specific day
  const toggleActivityOnDay = (dayIdx: number, activityName: string) => {
    const currentPlans = [...(getValues("daily_island_plan") || [])];
    while (currentPlans.length <= dayIdx) {
      currentPlans.push({
        day_number: currentPlans.length + 1,
        primary_island: resolvePrimaryIsland({}, currentPlans.length),
        attractions: [],
        activities: [],
        hotel: "",
        transfer_type: "Private",
      });
    }

    const targetDay = { ...currentPlans[dayIdx] };
    const currentActs = [...(targetDay.activities || [])];
    const exists = currentActs.includes(activityName);

    if (exists) {
      targetDay.activities = currentActs.filter((a) => a !== activityName);
    } else {
      targetDay.activities = [...currentActs, activityName];
    }

    currentPlans[dayIdx] = targetDay;
    setValue("daily_island_plan", currentPlans, { shouldDirty: true });
    syncPreferredActivities(currentPlans, includedActivities);
  };

  // Clear all activities for a specific day (Pure Leisure Day)
  const clearDayActivities = (dayIdx: number) => {
    const currentPlans = [...(getValues("daily_island_plan") || [])];
    if (currentPlans[dayIdx]) {
      currentPlans[dayIdx] = {
        ...currentPlans[dayIdx],
        activities: [],
      };
      setValue("daily_island_plan", currentPlans, { shouldDirty: true });
      syncPreferredActivities(currentPlans, includedActivities);
    }
  };

  // Complimentary / Free in package updater
  const updateFreeQuantity = (activity: ActivityItem, newQty: number) => {
    const clampedQty = Math.max(0, newQty);
    const actName = activity.activity_name;

    let nextIncluded = [...(includedActivities || [])];
    const existingIndex = nextIncluded.findIndex((i) => i.activity_name === actName);

    if (clampedQty === 0) {
      if (existingIndex >= 0) {
        nextIncluded.splice(existingIndex, 1);
      }
    } else {
      const entry: IncludedActivityType = {
        activity_name: actName,
        quantity: clampedQty,
        is_free: true,
        location: activity.location || "",
        category: activity.category || "",
      };
      if (existingIndex >= 0) {
        nextIncluded[existingIndex] = entry;
      } else {
        nextIncluded.push(entry);
      }
    }

    setValue("included_activities", nextIncluded, { shouldValidate: true, shouldDirty: true });
    syncPreferredActivities(dailyPlan, nextIncluded);
  };

  // Filter activities
  const filteredActivities = useMemo(() => {
    return allActivities.filter((act) => {
      // Free only filter
      if (showOnlyIncluded) {
        const qty = includedMap.get(act.activity_name) || 0;
        const isPref = preferredActivities.includes(act.activity_name);
        if (qty === 0 && !isPref) return false;
      }

      // Island filter
      if (selectedIsland !== "all") {
        const tab = ISLAND_TABS.find((t) => t.id === selectedIsland);
        if (tab?.match) {
          if (Array.isArray(tab.match)) {
            const matchesAny = tab.match.some((m) =>
              act.location.toLowerCase().includes(m.toLowerCase())
            );
            if (!matchesAny) return false;
          } else {
            if (!act.location.toLowerCase().includes(tab.match.toLowerCase())) {
              return false;
            }
          }
        }
      }

      // Category filter
      if (selectedCategory !== "All Categories") {
        if (!act.category.toLowerCase().includes(selectedCategory.toLowerCase())) {
          return false;
        }
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const inName = act.activity_name.toLowerCase().includes(q);
        const inLoc = act.location.toLowerCase().includes(q);
        const inCat = act.category.toLowerCase().includes(q);
        const inDesc = act.description.toLowerCase().includes(q);
        if (!inName && !inLoc && !inCat && !inDesc) return false;
      }

      return true;
    });
  }, [allActivities, selectedIsland, selectedCategory, searchQuery, showOnlyIncluded, includedMap, preferredActivities]);

  const totalFreeActivitiesCount = useMemo(() => {
    return includedActivities.reduce((acc, curr) => acc + (curr.quantity || 0), 0);
  }, [includedActivities]);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader
        title="Activities & Package Inclusions"
        description="Schedule activities day-by-day or configure complimentary package inclusions (e.g., 2 Free or complimentary for all tourists)."
      />

      {/* ── PACKAGE INCLUSIONS SUMMARY BANNER ── */}
      {totalFreeActivitiesCount > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-primary/5 to-amber-500/10 p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400">
                <Gift className="h-4 w-4" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground text-sm flex items-center gap-2">
                  Complimentary Package Inclusions
                  <span className="inline-flex items-center rounded-full bg-amber-500/20 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:text-amber-300">
                    {totalFreeActivitiesCount} Free {totalFreeActivitiesCount === 1 ? "Activity" : "Activities"}
                  </span>
                </h4>
                <p className="text-xs text-muted-foreground">
                  These activities will be featured as complimentary (₹0) in the client quotation, day narrative, and package invoice.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setValue("included_activities", [], { shouldDirty: true });
                syncPreferredActivities(dailyPlan, []);
              }}
              className="text-xs text-muted-foreground hover:text-destructive transition-colors underline"
            >
              Clear all free inclusions
            </button>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {includedActivities.map((inc) => (
              <div
                key={inc.activity_name}
                className="inline-flex items-center gap-2 rounded-lg border border-amber-500/30 bg-background/90 px-3 py-1.5 text-xs shadow-xs"
              >
                <Gift className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                <span className="font-medium text-foreground">{inc.activity_name}</span>
                <span className="inline-flex items-center justify-center rounded-full bg-amber-500/20 px-2 py-0.5 text-[11px] font-bold text-amber-700 dark:text-amber-300">
                  {inc.quantity} Free
                </span>
                <button
                  type="button"
                  title="Remove inclusion"
                  onClick={() => {
                    const match = allActivities.find((a) => a.activity_name === inc.activity_name);
                    if (match) updateFreeQuantity(match, 0);
                    else {
                      const next = includedActivities.filter((i) => i.activity_name !== inc.activity_name);
                      setValue("included_activities", next, { shouldDirty: true });
                      syncPreferredActivities(dailyPlan, next);
                    }
                  }}
                  className="rounded-full p-0.5 hover:bg-muted text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── DAY-BY-DAY ACTIVITY SCHEDULE & LEISURE CONTROL ── */}
      <div className="rounded-xl border border-border bg-card/70 p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/60">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                Day-Wise Activity Schedule
                <span className="text-xs font-normal text-muted-foreground">({numberOfDays} Days)</span>
              </h3>
              <p className="text-xs text-muted-foreground">
                Assign activities per day. If a day has no activity chosen, the proposal will completely remove the activity line for that day.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20 flex items-center gap-1.5">
              <Check className="h-3 w-3" /> Auto-clean: No activity line on leisure days
            </span>
          </div>
        </div>

        {/* Day Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: numberOfDays }).map((_, idx) => {
            const dayNum = idx + 1;
            const currentDayPlan = dailyPlan[idx] || {
              day_number: dayNum,
              primary_island: resolvePrimaryIsland({}, idx),
              activities: [],
            };
            const island = resolvePrimaryIsland(currentDayPlan, idx);
            const dayActivities = (currentDayPlan.activities || []).filter((a) => a && a.trim());
            const hasActivities = dayActivities.length > 0;
            const isActiveFilter = activeDayIndex === idx;

            return (
              <div
                key={dayNum}
                className={`relative flex flex-col justify-between rounded-xl border p-3.5 transition-all ${
                  isActiveFilter
                    ? "border-primary bg-primary/5 shadow-xs ring-1 ring-primary/30"
                    : hasActivities
                    ? "border-border/80 bg-background/80"
                    : "border-dashed border-border/70 bg-background/40 hover:bg-background/60"
                }`}
              >
                <div>
                  {/* Day Header */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center justify-center rounded-md bg-secondary px-2 py-0.5 text-xs font-bold text-secondary-foreground">
                        Day {dayNum}
                      </span>
                      <span className="text-xs font-semibold text-foreground truncate max-w-[140px]" title={island}>
                        {island}
                      </span>
                    </div>

                    {hasActivities ? (
                      <span className="text-[10px] font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                        {dayActivities.length} {dayActivities.length === 1 ? "Activity" : "Activities"}
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <SunMedium className="h-3 w-3" /> Leisure Day
                      </span>
                    )}
                  </div>

                  {/* Activity Pills for this day */}
                  <div className="min-h-[46px]">
                    {hasActivities ? (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {dayActivities.map((act) => (
                          <span
                            key={act}
                            className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2 py-1 text-[11px] text-foreground shadow-2xs group"
                          >
                            <span className="truncate max-w-[160px] font-medium">{act}</span>
                            <button
                              type="button"
                              onClick={() => toggleActivityOnDay(idx, act)}
                              className="text-muted-foreground hover:text-destructive rounded-full p-0.5 transition-colors"
                              title={`Remove from Day ${dayNum}`}
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] text-muted-foreground/80 italic pt-1 leading-relaxed">
                        No activity scheduled. Activity line will be completely omitted from this day.
                      </p>
                    )}
                  </div>
                </div>

                {/* Day Card Footer Actions */}
                <div className="mt-3 pt-2.5 border-t border-border/50 flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (activeDayIndex === idx) {
                        setActiveDayIndex(null);
                      } else {
                        setActiveDayIndex(idx);
                        // Auto-filter island if matching
                        const islandLower = island.toLowerCase();
                        if (islandLower.includes("havelock") || islandLower.includes("swaraj")) setSelectedIsland("havelock");
                        else if (islandLower.includes("neil") || islandLower.includes("shaheed")) setSelectedIsland("neil");
                        else if (islandLower.includes("port blair")) setSelectedIsland("port_blair");
                        else if (islandLower.includes("baratang")) setSelectedIsland("baratang");
                        else if (islandLower.includes("diglipur")) setSelectedIsland("diglipur");
                        else setSelectedIsland("all");
                      }
                    }}
                    className={`text-[11px] font-medium px-2.5 py-1 rounded-md border transition-all flex items-center gap-1 ${
                      isActiveFilter
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-background hover:bg-muted text-foreground"
                    }`}
                  >
                    {isActiveFilter ? (
                      <>
                        <Check className="h-3 w-3" /> Selected Day
                      </>
                    ) : (
                      <>
                        <Plus className="h-3 w-3" /> Add to Day {dayNum}
                      </>
                    )}
                  </button>

                  {hasActivities && (
                    <button
                      type="button"
                      onClick={() => clearDayActivities(idx)}
                      className="text-[11px] text-muted-foreground hover:text-destructive transition-colors flex items-center gap-1 px-1.5 py-1"
                      title="Clear activities and make this day pure leisure"
                    >
                      <Trash2 className="h-3 w-3" /> Clear
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── SEARCH & FILTER CONTROLS ── */}
      <div className="space-y-4 rounded-xl border border-border bg-card/60 p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <Compass className="h-4 w-4 text-primary" />
              Andaman Activities Catalog
            </h3>
            {activeDayIndex !== null && (
              <span className="text-xs bg-primary/10 text-primary font-medium px-2.5 py-0.5 rounded-full border border-primary/20">
                Scheduling for Day {activeDayIndex + 1}
              </span>
            )}
          </div>

          {activeDayIndex !== null && (
            <button
              type="button"
              onClick={() => setActiveDayIndex(null)}
              className="text-xs text-muted-foreground hover:text-foreground underline flex items-center gap-1"
            >
              <X className="h-3.5 w-3.5" /> View all days
            </button>
          )}
        </div>

        {/* Search Bar & Quick Toggles */}
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by activity, island, or keyword..."
              className="pl-9 h-10 bg-background/80"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto justify-between md:justify-end">
            <button
              type="button"
              onClick={() => setShowOnlyIncluded(!showOnlyIncluded)}
              className={`text-xs px-3 py-2 rounded-lg border transition-all flex items-center gap-1.5 font-medium ${
                showOnlyIncluded
                  ? "border-primary bg-primary text-primary-foreground shadow-xs"
                  : "border-border bg-background/80 hover:bg-accent text-muted-foreground"
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              {showOnlyIncluded
                ? `Showing Selected (${preferredActivities.length})`
                : `Show Selected Only (${preferredActivities.length})`}
            </button>

            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {filteredActivities.length} {filteredActivities.length === 1 ? "activity" : "activities"}
            </span>
          </div>
        </div>

        {/* Island Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mr-1" />
          {ISLAND_TABS.map((tab) => {
            const isActive = selectedIsland === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setSelectedIsland(tab.id)}
                className={`text-xs px-3 py-1.5 rounded-full border whitespace-nowrap transition-all font-medium ${
                  isActive
                    ? "border-primary bg-primary text-primary-foreground shadow-xs"
                    : "border-border/60 bg-background/70 hover:bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          <Layers className="h-3.5 w-3.5 text-muted-foreground shrink-0 mr-1" />
          {CATEGORY_FILTERS.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`text-[11px] px-2.5 py-1 rounded-md border whitespace-nowrap transition-all ${
                  isActive
                    ? "border-secondary bg-secondary text-secondary-foreground font-semibold"
                    : "border-border/40 bg-background/50 hover:bg-muted/60 text-muted-foreground"
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── ACTIVITIES GRID ── */}
      <div>
        {isLoadingAll ? (
          <div className="p-12 text-center text-muted-foreground animate-pulse border border-dashed border-border rounded-xl bg-background/30">
            <Compass className="h-8 w-8 mx-auto mb-2 animate-spin text-primary/60" />
            Loading complete Andaman activities database...
          </div>
        ) : isErrorAll ? (
          <div className="p-4 text-sm text-destructive border border-destructive/20 rounded-md bg-destructive/10">
            Failed to load activities catalog. Please check that the backend server is active.
          </div>
        ) : filteredActivities.length === 0 ? (
          <div className="p-10 text-center text-muted-foreground border border-dashed border-border rounded-xl bg-background/20 space-y-2">
            <p className="text-sm font-medium">No activities match your current filters.</p>
            <p className="text-xs text-muted-foreground">Try clearing your search query or selecting &quot;All Islands&quot; / &quot;All Categories&quot;.</p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setSelectedIsland("all");
                setSelectedCategory("All Categories");
                setShowOnlyIncluded(false);
              }}
              className="mt-2 text-xs px-3 py-1.5 rounded-md border border-border bg-background hover:bg-muted text-foreground"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredActivities.map((activity) => {
              const actName = activity.activity_name;
              const scheduledDays = activityDayMap.get(actName) || new Set<number>();
              const isScheduledAnywhere = scheduledDays.size > 0;
              const isScheduledOnActiveDay = activeDayIndex !== null && scheduledDays.has(activeDayIndex + 1);
              const freeQty = includedMap.get(actName) || 0;
              const hasFreeInclusion = freeQty > 0;
              const isRecommended = recommendedNames.has(actName.toLowerCase());

              return (
                <div
                  key={actName}
                  className={`relative flex flex-col justify-between rounded-xl border p-4 transition-all ${
                    hasFreeInclusion
                      ? "border-amber-500/50 bg-gradient-to-br from-amber-500/5 via-card to-background shadow-xs ring-1 ring-amber-500/20"
                      : isScheduledAnywhere
                      ? "border-primary/50 bg-card/90 shadow-xs"
                      : "border-border/70 bg-card/40 hover:border-border hover:bg-card/70"
                  }`}
                >
                  {/* Card Top: Name, Badges, Description */}
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-sm font-semibold text-foreground hover:text-primary transition-colors">
                            {actName}
                          </span>
                          {isRecommended && (
                            <span
                              title="Recommended for this trip profile"
                              className="inline-flex items-center gap-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded-full"
                            >
                              <Sparkles className="h-3 w-3" /> Recommended
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-muted-foreground/80" />
                            {activity.location}
                          </span>
                          <span>•</span>
                          <span className="rounded bg-muted/60 px-1.5 py-0.5 text-[11px]">
                            {activity.category}
                          </span>
                          {activity.duration && (
                            <>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3 text-muted-foreground/80" />
                                {activity.duration}
                              </span>
                            </>
                          )}
                          <span>•</span>
                          <span className="font-semibold text-foreground">
                            {activity.price === "0" || activity.price === 0
                              ? "Free / Public"
                              : `₹${Number(activity.price).toLocaleString("en-IN")}`}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    {activity.description && (
                      <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
                        {activity.description}
                      </p>
                    )}
                  </div>

                  {/* Card Bottom: Day Assignment & Complimentary Stepper */}
                  <div className="mt-4 pt-3 border-t border-border/50 space-y-2.5">
                    {/* Day Assignment Row */}
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs font-medium text-foreground">
                          {activeDayIndex !== null ? `Day ${activeDayIndex + 1}:` : "Schedule Day:"}
                        </span>
                      </div>

                      {activeDayIndex !== null ? (
                        <button
                          type="button"
                          onClick={() => toggleActivityOnDay(activeDayIndex, actName)}
                          className={`text-xs px-3 py-1 rounded-md border font-medium transition-all flex items-center gap-1.5 ${
                            isScheduledOnActiveDay
                              ? "border-primary bg-primary text-primary-foreground shadow-2xs"
                              : "border-border bg-background hover:bg-primary/10 hover:border-primary/50 text-foreground"
                          }`}
                        >
                          {isScheduledOnActiveDay ? (
                            <>
                              <Check className="h-3 w-3" /> Scheduled on Day {activeDayIndex + 1}
                            </>
                          ) : (
                            <>
                              <Plus className="h-3 w-3" /> Add to Day {activeDayIndex + 1}
                            </>
                          )}
                        </button>
                      ) : (
                        <div className="flex flex-wrap items-center gap-1">
                          {Array.from({ length: numberOfDays }).map((_, dIdx) => {
                            const dNum = dIdx + 1;
                            const isAssigned = scheduledDays.has(dNum);
                            return (
                              <button
                                key={dNum}
                                type="button"
                                onClick={() => toggleActivityOnDay(dIdx, actName)}
                                title={isAssigned ? `Remove from Day ${dNum}` : `Assign to Day ${dNum}`}
                                className={`text-[11px] px-2 py-0.5 rounded-md border transition-all font-medium ${
                                  isAssigned
                                    ? "border-primary bg-primary text-primary-foreground shadow-2xs"
                                    : "border-border/60 bg-background/60 hover:bg-muted text-muted-foreground hover:text-foreground"
                                }`}
                              >
                                {isAssigned ? `✓ D${dNum}` : `D${dNum}`}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Complimentary Free In Package Row */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/30">
                      <div className="flex items-center gap-1.5">
                        <Gift
                          className={`h-3.5 w-3.5 ${
                            hasFreeInclusion
                              ? "text-amber-600 dark:text-amber-400"
                              : "text-muted-foreground/60"
                          }`}
                        />
                        <span className="text-xs font-medium text-foreground">
                          Included in Package:
                        </span>
                      </div>

                      {hasFreeInclusion ? (
                        <div className="flex items-center gap-2">
                          <div className="flex items-center border border-amber-500/40 rounded-lg bg-background overflow-hidden shadow-2xs">
                            <button
                              type="button"
                              onClick={() => updateFreeQuantity(activity, freeQty - 1)}
                              className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                              title="Decrease free quantity"
                            >
                              <Minus className="h-3 w-3" />
                            </button>
                            <span className="px-2 text-xs font-bold text-amber-700 dark:text-amber-300 min-w-8 text-center">
                              {freeQty} Free
                            </span>
                            <button
                              type="button"
                              onClick={() => updateFreeQuantity(activity, freeQty + 1)}
                              className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                              title="Increase free quantity"
                            >
                              <Plus className="h-3 w-3" />
                            </button>
                          </div>
                          {freeQty !== totalTourists && (
                            <button
                              type="button"
                              onClick={() => updateFreeQuantity(activity, totalTourists)}
                              className="text-[11px] font-medium px-2 py-1 rounded-md border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 transition-all flex items-center gap-1"
                              title={`Set complimentary for all ${totalTourists} tourists`}
                            >
                              <Users className="h-3 w-3" />
                              All ({totalTourists})
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => updateFreeQuantity(activity, 0)}
                            className="p-1 text-muted-foreground hover:text-destructive transition-colors rounded-full"
                            title="Remove free inclusion"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => updateFreeQuantity(activity, 1)}
                            className="text-[11px] font-medium px-2 py-0.5 rounded-md border border-border/80 bg-background/80 hover:bg-amber-500/10 hover:border-amber-500/40 hover:text-amber-700 dark:hover:text-amber-300 transition-all flex items-center gap-1 text-muted-foreground"
                          >
                            <Plus className="h-3 w-3" /> 1 Free
                          </button>
                          <button
                            type="button"
                            onClick={() => updateFreeQuantity(activity, 2)}
                            className="text-[11px] font-medium px-2 py-0.5 rounded-md border border-border/80 bg-background/80 hover:bg-amber-500/10 hover:border-amber-500/40 hover:text-amber-700 dark:hover:text-amber-300 transition-all flex items-center gap-1 text-muted-foreground"
                          >
                            <Plus className="h-3 w-3" /> 2 Free
                          </button>
                          <button
                            type="button"
                            onClick={() => updateFreeQuantity(activity, totalTourists)}
                            className="text-[11px] font-semibold px-2 py-0.5 rounded-md border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 transition-all flex items-center gap-1 shadow-2xs"
                            title={`Make complimentary for all ${totalTourists} tourists`}
                          >
                            <Users className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                            All ({totalTourists} Free)
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── SPECIAL OCCASIONS ── */}
      <div className="pt-6 border-t border-border mt-8">
        <h3 className="mb-2 text-base font-semibold text-foreground">Special Occasions & Celebrations</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Select any celebrations to arrange complimentary cakes, flower bed decorations, or curated candlelight moments.
        </p>
        <FormField
          control={control}
          name="special_occasions"
          render={() => (
            <FormItem>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {SPECIAL_OCCASIONS.map((occasion) => (
                  <FormField
                    key={occasion}
                    control={control}
                    name="special_occasions"
                    render={({ field }) => {
                      const isChecked = field.value?.includes(occasion);
                      return (
                        <FormItem
                          key={occasion}
                          className={`flex flex-row items-center space-x-3 space-y-0 rounded-lg border p-3 transition-all ${
                            isChecked
                              ? "border-primary bg-primary/5 shadow-2xs"
                              : "border-border/60 bg-background/60 hover:bg-muted/40"
                          }`}
                        >
                          <FormControl>
                            <Checkbox
                              checked={isChecked}
                              onCheckedChange={(checked) => {
                                return checked
                                  ? field.onChange([...(field.value || []), occasion])
                                  : field.onChange(
                                      field.value?.filter((value: string) => value !== occasion)
                                    );
                              }}
                            />
                          </FormControl>
                          <FormLabel className="text-xs font-medium cursor-pointer text-foreground leading-normal">
                            {occasion}
                          </FormLabel>
                        </FormItem>
                      );
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
