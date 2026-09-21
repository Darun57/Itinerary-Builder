"use client";

import React, { useMemo, useEffect } from "react";
import { useFormContext } from "react-hook-form";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { StepHeader } from "../StepHeader";
import { CheckboxList } from "../CheckboxList";
import { Calculator, Users, Sparkles, Plus, Trash2 } from "lucide-react";
import { TripRequestType, PricingTierType } from "../../schema";
import { useWizardStore } from "../../store";

const DIETS = ["Vegetarian", "Non-Vegetarian", "Jain", "Vegan", "Halal"];

export default function TransportMealsStep() {
  const { control, watch, setValue } = useFormContext<TripRequestType>();
  const updateStoreFormData = useWizardStore((s) => s.updateFormData);

  const numAdults = Number(watch("number_of_adults") || 2);
  const numChildren = Number(watch("number_of_children") || 0);
  const numInfants = Number(watch("number_of_infants") || 0);
  const numSeniors = Number(watch("number_of_senior_citizens") || 0);

  const adultCost = Number(watch("per_person_cost") || 0);
  const childCost = Number(watch("child_cost") || 0);
  const infantCost = Number(watch("infant_cost") || 0);
  const seniorCost = Number(watch("senior_cost") || 0);
  const flightRate = Number(watch("flight_per_person_rate") || 0);
  const flightOption = watch("flight_option") || "Excluded";
  const totalPackageCost = Number(watch("total_package_cost") || 0);
  const pricingTiers: PricingTierType[] = watch("pricing_tiers") || [];

  const hasNonAdults = numChildren > 0 || numInfants > 0 || numSeniors > 0;
  const totalPax = numAdults + numChildren + numInfants + numSeniors;

  // Category definitions for all 4 passenger types
  const categoryDefs = useMemo(() => [
    { key: "adult" as const, label: "Adults", singular: "Adult", pax: numAdults, costField: "per_person_cost" as const, costVal: adultCost, defaultCost: 20000 },
    { key: "child" as const, label: "Children", singular: "Child", pax: numChildren, costField: "child_cost" as const, costVal: childCost, defaultCost: 12500 },
    { key: "infant" as const, label: "Infants", singular: "Infant", pax: numInfants, costField: "infant_cost" as const, costVal: infantCost, defaultCost: 0 },
    { key: "senior" as const, label: "Seniors", singular: "Senior", pax: numSeniors, costField: "senior_cost" as const, costVal: seniorCost, defaultCost: 18000 },
  ], [numAdults, numChildren, numInfants, numSeniors, adultCost, childCost, infantCost, seniorCost]);

  // Initialize pricing_tiers if empty on first load
  useEffect(() => {
    if (!pricingTiers || pricingTiers.length === 0) {
      const initialTiers: PricingTierType[] = [];
      if (numAdults > 0) initialTiers.push({ category: "adult", label: "Adults", pax: numAdults, cost: adultCost });
      if (numChildren > 0) initialTiers.push({ category: "child", label: "Child", pax: numChildren, cost: childCost });
      if (numInfants > 0) initialTiers.push({ category: "infant", label: "Infant", pax: numInfants, cost: infantCost });
      if (numSeniors > 0) initialTiers.push({ category: "senior", label: "Senior", pax: numSeniors, cost: seniorCost });
      if (initialTiers.length > 0) {
        setValue("pricing_tiers", initialTiers, { shouldDirty: false });
      }
    }
  }, [numAdults, numChildren, numInfants, numSeniors]);

  // Keep single-tier pax in sync when passenger counts change from Step 2
  useEffect(() => {
    if (!pricingTiers || pricingTiers.length === 0) return;
    let changed = false;
    const updated = pricingTiers.map(t => {
      const catDef = categoryDefs.find(c => c.key === t.category);
      if (!catDef) return t;
      const countTiersInCat = pricingTiers.filter(x => x.category === t.category).length;
      if (countTiersInCat === 1 && t.pax !== catDef.pax && catDef.pax > 0) {
        changed = true;
        return { ...t, pax: catDef.pax };
      }
      return t;
    });
    if (changed) {
      setValue("pricing_tiers", updated, { shouldDirty: true });
    }
  }, [numAdults, numChildren, numInfants, numSeniors]);

  // Synchronize pricing_tiers into the persistent wizard store
  useEffect(() => {
    if (pricingTiers && pricingTiers.length > 0) {
      updateStoreFormData({ pricing_tiers: pricingTiers });
    }
  }, [pricingTiers, updateStoreFormData]);

  // Operations for multi-tier pricing across all 4 categories
  const handleSingleRateChange = (categoryKey: "adult" | "child" | "infant" | "senior", cost: number) => {
    if (categoryKey === "adult") setValue("per_person_cost", cost, { shouldDirty: true });
    else if (categoryKey === "child") setValue("child_cost", cost, { shouldDirty: true });
    else if (categoryKey === "infant") setValue("infant_cost", cost, { shouldDirty: true });
    else if (categoryKey === "senior") setValue("senior_cost", cost, { shouldDirty: true });

    const catDef = categoryDefs.find(c => c.key === categoryKey);
    const existing = [...pricingTiers];
    const catIndices = existing.map((t, i) => t.category === categoryKey ? i : -1).filter(i => i !== -1);
    if (catIndices.length <= 1) {
      if (catIndices.length === 1) {
        existing[catIndices[0]] = { ...existing[catIndices[0]], cost };
      } else {
        existing.push({ category: categoryKey, label: catDef?.singular || "", pax: catDef?.pax || 1, cost });
      }
      setValue("pricing_tiers", existing, { shouldDirty: true });
    }
  };

  const handleAddSplit = (categoryKey: "adult" | "child" | "infant" | "senior") => {
    const catDef = categoryDefs.find(c => c.key === categoryKey);
    if (!catDef) return;
    const totalPax = catDef.pax;
    const existing = [...pricingTiers];
    const catTiers = existing.filter(t => t.category === categoryKey);
    const currentAllocated = catTiers.reduce((s, t) => s + (Number(t.pax) || 0), 0);
    const currentCost = catTiers[0]?.cost || catDef.costVal || 0;

    if (catTiers.length <= 1) {
      const half = Math.max(1, Math.floor(totalPax / 2));
      const remainder = Math.max(1, totalPax - half);
      const firstIdx = existing.findIndex(t => t.category === categoryKey);
      if (firstIdx !== -1) {
        existing[firstIdx] = { ...existing[firstIdx], pax: half };
      } else {
        existing.push({ category: categoryKey, label: catDef.singular, pax: half, cost: currentCost });
      }
      existing.push({ category: categoryKey, label: catDef.singular, pax: remainder, cost: currentCost });
    } else {
      const remainingPax = Math.max(1, totalPax - currentAllocated);
      existing.push({ category: categoryKey, label: catDef.singular, pax: remainingPax, cost: currentCost });
    }
    setValue("pricing_tiers", existing, { shouldDirty: true, shouldValidate: true });
  };

  const handleTierChange = (globalIndex: number, updates: Partial<PricingTierType>) => {
    const updated = [...pricingTiers];
    if (!updated[globalIndex]) return;
    updated[globalIndex] = { ...updated[globalIndex], ...updates };
    setValue("pricing_tiers", updated, { shouldDirty: true, shouldValidate: true });

    // Sync primary cost field if it is the first tier for that category
    const t = updated[globalIndex];
    const firstIdx = updated.findIndex(x => x.category === t.category);
    if (globalIndex === firstIdx && updates.cost !== undefined) {
      if (t.category === "adult") setValue("per_person_cost", updates.cost, { shouldDirty: true });
      else if (t.category === "child") setValue("child_cost", updates.cost, { shouldDirty: true });
      else if (t.category === "infant") setValue("infant_cost", updates.cost, { shouldDirty: true });
      else if (t.category === "senior") setValue("senior_cost", updates.cost, { shouldDirty: true });
    }
  };

  const handleRemoveTier = (globalIndex: number) => {
    const tierToRemove = pricingTiers[globalIndex];
    if (!tierToRemove) return;
    const catKey = tierToRemove.category;
    const catDef = categoryDefs.find(c => c.key === catKey);
    const totalCatPax = catDef?.pax || 1;

    const updated = pricingTiers.filter((_, i) => i !== globalIndex);
    const remainingInCat = updated.filter(t => t.category === catKey);
    if (remainingInCat.length === 1) {
      const idx = updated.findIndex(t => t.category === catKey);
      updated[idx] = { ...updated[idx], pax: totalCatPax };
    }
    setValue("pricing_tiers", updated, { shouldDirty: true, shouldValidate: true });
  };

  const handleResetToSingleRate = (categoryKey: "adult" | "child" | "infant" | "senior") => {
    const catDef = categoryDefs.find(c => c.key === categoryKey);
    if (!catDef) return;
    const existing = [...pricingTiers];
    const catTiers = existing.filter(t => t.category === categoryKey);
    const cost = catTiers[0]?.cost || catDef.costVal || 0;
    const otherTiers = existing.filter(t => t.category !== categoryKey);
    otherTiers.push({ category: categoryKey, label: catDef.singular, pax: catDef.pax, cost });
    setValue("pricing_tiers", otherTiers, { shouldDirty: true, shouldValidate: true });
  };

  // Pure tour package sum (land services: hotels, transfers, sightseeing, activities)
  const packageSum = useMemo(() => {
    if (pricingTiers && pricingTiers.length > 0) {
      return pricingTiers.reduce((acc, t) => acc + ((Number(t.pax) || 0) * (Number(t.cost) || 0)), 0);
    }
    return (numAdults * adultCost) + (numChildren * childCost) + (numInfants * infantCost) + (numSeniors * seniorCost);
  }, [pricingTiers, numAdults, adultCost, numChildren, childCost, numInfants, infantCost, numSeniors, seniorCost]);

  // Air transportation sum
  const flightSum = useMemo(() => {
    return (flightOption === "Included" && flightRate > 0) ? (totalPax * flightRate) : 0;
  }, [flightOption, flightRate, totalPax]);

  // Total service subtotal (package + flights)
  const calculatedSum = useMemo(() => {
    return packageSum + flightSum;
  }, [packageSum, flightSum]);

  const prevCalculatedRef = React.useRef<number>(calculatedSum);

  // Keep total package cost in sync with calculatedSum as user types tiered rates
  useEffect(() => {
    const current = Number(watch("total_package_cost") || 0);
    if (current === 0 || current === prevCalculatedRef.current) {
      if (calculatedSum > 0) {
        setValue("total_package_cost", calculatedSum, { shouldDirty: true });
      }
    }
    prevCalculatedRef.current = calculatedSum;
  }, [calculatedSum, setValue, watch]);

  const handleApplyCalculated = () => {
    setValue("total_package_cost", calculatedSum, { shouldDirty: true, shouldValidate: true });
    prevCalculatedRef.current = calculatedSum;
  };

  const isAnyCategorySplit = categoryDefs.some(c => pricingTiers.filter(t => t.category === c.key).length > 1);
  const showTiered = hasNonAdults || isAnyCategorySplit;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader
        title="Transport & Meals"
        description="Configure transfers, flight rates, meal plans, and itemized passenger pricing."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          control={control}
          name="transfer_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Transfer Type *</FormLabel>
              <Select onValueChange={field.onChange} value={field.value || "Private"}>
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
              <Select onValueChange={field.onChange} value={field.value || "CP"}>
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

      <div className="pt-6 border-t border-border mt-8 space-y-6">
        <h3 className="text-lg font-medium flex items-center gap-2">
          <span>✈️</span> Flight Details & Package Pricing
        </h3>

        {/* Flight configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={control}
            name="flight_option"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Flight Status</FormLabel>
                <Select onValueChange={field.onChange} value={field.value || "Excluded"}>
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
        </div>

        {/* ── PRICING SECTION: Tiered vs Standard ── */}
        {showTiered ? (
          /* Tiered & Split Passenger Pricing Box */
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-4 shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-primary/20">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Users className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="font-semibold text-foreground text-sm flex items-center gap-2">
                    Tiered Passenger Pricing (Per-Category Rates)
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    Itemized pricing for {numAdults} Adults
                    {numChildren > 0 ? `, ${numChildren} Children` : ""}
                    {numInfants > 0 ? `, ${numInfants} Infants` : ""}
                    {numSeniors > 0 ? `, ${numSeniors} Seniors` : ""}. Add separate price splits for any category as needed.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20">
                Itemized in Billing
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {categoryDefs.map(cat => {
                const catTiersWithIdx = pricingTiers
                  .map((t, idx) => ({ ...t, globalIdx: idx }))
                  .filter(t => t.category === cat.key);

                if (cat.pax <= 0 && catTiersWithIdx.length === 0) return null;

                const isSplit = catTiersWithIdx.length > 1;
                const allocatedPax = catTiersWithIdx.reduce((s, t) => s + (Number(t.pax) || 0), 0);
                const catSubtotal = catTiersWithIdx.reduce((s, t) => s + (Number(t.pax || 0) * Number(t.cost || 0)), 0);
                const singleCost = catTiersWithIdx[0]?.cost ?? cat.costVal;

                if (!isSplit) {
                  return (
                    <div key={cat.key} className="rounded-lg border border-border/80 bg-background p-3 shadow-2xs space-y-1.5 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-foreground">
                            Per {cat.singular} Cost (₹) *
                          </span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[11px] font-normal text-muted-foreground">{cat.pax} Pax</span>
                            <button
                              type="button"
                              onClick={() => handleAddSplit(cat.key)}
                              className="text-[10px] text-primary hover:text-primary/80 font-medium flex items-center gap-0.5 bg-primary/10 hover:bg-primary/20 px-1.5 py-0.5 rounded transition-colors cursor-pointer"
                              title={`Add separate pricing split for ${cat.label}`}
                            >
                              <Plus className="h-2.5 w-2.5" /> Split
                            </button>
                          </div>
                        </div>
                        <Input
                          type="number"
                          min="0"
                          value={singleCost === 0 ? "" : singleCost}
                          placeholder={`e.g. ${cat.defaultCost}`}
                          className="bg-transparent font-medium text-sm mt-1"
                          onChange={e => handleSingleRateChange(cat.key, Number(e.target.value) || 0)}
                        />
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Subtotal: ₹{(cat.pax * singleCost).toLocaleString("en-IN")}
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={cat.key} className="rounded-lg border-2 border-primary/40 bg-background/95 p-3.5 shadow-xs col-span-1 sm:col-span-2 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border/60">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-foreground">{cat.label} Pricing (Split Rates)</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                          allocatedPax === cat.pax
                            ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                            : "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                        }`}>
                          {allocatedPax} of {cat.pax} Pax allocated
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleAddSplit(cat.key)}
                          className="text-[11px] font-semibold text-primary hover:underline flex items-center gap-1 cursor-pointer"
                        >
                          <Plus className="h-3 w-3" /> Add Split
                        </button>
                        <button
                          type="button"
                          onClick={() => handleResetToSingleRate(cat.key)}
                          className="text-[10px] text-muted-foreground hover:text-foreground underline cursor-pointer"
                        >
                          Reset to Single Rate
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      {catTiersWithIdx.map((tier, localIdx) => (
                        <div key={tier.globalIdx} className="flex flex-wrap items-center gap-2 bg-muted/40 p-2 rounded-md border border-border/60 text-xs">
                          <span className="font-semibold text-muted-foreground min-w-[52px]">
                            Split #{localIdx + 1}:
                          </span>
                          <div className="flex items-center gap-1">
                            <span className="text-muted-foreground text-[11px]">Pax:</span>
                            <Input
                              type="number"
                              min="1"
                              max={cat.pax}
                              value={tier.pax}
                              onChange={e => handleTierChange(tier.globalIdx, { pax: Math.max(1, Number(e.target.value) || 1) })}
                              className="w-16 h-7 text-xs bg-background"
                            />
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-muted-foreground text-[11px]">₹/Person:</span>
                            <Input
                              type="number"
                              min="0"
                              value={tier.cost === 0 ? "" : tier.cost}
                              placeholder="e.g. 12500"
                              onChange={e => handleTierChange(tier.globalIdx, { cost: Math.max(0, Number(e.target.value) || 0) })}
                              className="w-28 h-7 text-xs bg-background"
                            />
                          </div>
                          <div className="flex-1 text-right font-medium text-foreground min-w-[90px]">
                            = ₹{(Number(tier.pax || 0) * Number(tier.cost || 0)).toLocaleString("en-IN")}
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveTier(tier.globalIdx)}
                            className="text-muted-foreground hover:text-destructive p-1 rounded transition-colors cursor-pointer"
                            title="Remove this split"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs border-t border-border/40">
                      {allocatedPax !== cat.pax ? (
                        <span className="text-amber-500 font-medium text-[11px]">
                          ⚠️ Split pax ({allocatedPax}) does not equal {cat.pax} {cat.label}.
                        </span>
                      ) : (
                        <span className="text-emerald-500 font-medium text-[11px]">
                          ✓ All {cat.pax} {cat.label} accounted for.
                        </span>
                      )}
                      <span className="font-bold text-foreground">
                        {cat.label} Total: ₹{catSubtotal.toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Subtotal Calculation Strip & Quick Sync */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-primary/20 text-xs">
              <div className="flex flex-wrap items-center gap-1.5 text-muted-foreground">
                <span className="font-semibold text-foreground">Package Sum:</span>
                {categoryDefs.map((cat, i) => {
                  const catTiers = pricingTiers.filter(t => t.category === cat.key);
                  if (cat.pax <= 0 && catTiers.length === 0) return null;
                  const catSum = catTiers.length > 0
                    ? catTiers.reduce((s, t) => s + ((Number(t.pax) || 0) * (Number(t.cost) || 0)), 0)
                    : cat.pax * cat.costVal;
                  return (
                    <span key={cat.key} className="inline-flex items-center gap-1">
                      {i > 0 && <span>+</span>}
                      <span>{cat.label} ₹{catSum.toLocaleString("en-IN")}</span>
                      {catTiers.length > 1 && (
                        <span className="text-[10px] text-muted-foreground/80">
                          ({catTiers.map(t => `${t.pax}×₹${Number(t.cost || 0).toLocaleString("en-IN")}`).join(" + ")})
                        </span>
                      )}
                    </span>
                  );
                })}
                <span className="font-bold text-foreground ml-1">= ₹{calculatedSum.toLocaleString("en-IN")}</span>
              </div>

              {totalPackageCost !== calculatedSum && (
                <button
                  type="button"
                  onClick={handleApplyCalculated}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-primary text-primary-foreground font-semibold text-[11px] shadow-2xs hover:bg-primary/90 transition-all cursor-pointer"
                >
                  <Calculator className="h-3 w-3" />
                  Sync Total Package Cost (₹{calculatedSum.toLocaleString("en-IN")})
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Standard Single Per Person Cost for Adult-only trips */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormField
              control={control}
              name="per_person_cost"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center justify-between">
                    <FormLabel>Per Person Cost (₹)</FormLabel>
                    <button
                      type="button"
                      onClick={() => handleAddSplit("adult")}
                      className="text-[11px] text-primary hover:underline font-medium flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="h-3 w-3" /> Split Adult Rates
                    </button>
                  </div>
                  <FormControl>
                    <Input
                      type="number"
                      min="0"
                      placeholder="e.g. 30000"
                      className="bg-background/50"
                      {...field}
                      onChange={e => {
                        field.onChange(e);
                        handleSingleRateChange("adult", Number(e.target.value) || 0);
                      }}
                    />
                  </FormControl>
                  <FormDescription>Package cost per person.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        )}

        {/* Total Package Cost Field */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <FormField
            control={control}
            name="total_package_cost"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel className="font-semibold">Total Package Cost (₹) *</FormLabel>
                  {calculatedSum > 0 && totalPackageCost !== calculatedSum && (
                    <button
                      type="button"
                      onClick={handleApplyCalculated}
                      className="text-[11px] text-primary hover:underline font-medium flex items-center gap-1"
                    >
                      <Sparkles className="h-3 w-3" /> Use calculated: ₹{calculatedSum.toLocaleString("en-IN")}
                    </button>
                  )}
                </div>
                <FormControl>
                  <Input
                    type="number"
                    min="0"
                    placeholder="e.g. 85000"
                    className="bg-background/50 font-bold text-base"
                    {...field}
                  />
                </FormControl>
                <FormDescription className="text-xs space-y-0.5">
                  <span className="block text-muted-foreground">Package subtotal before statutory taxes.</span>
                  {Number(field.value || 0) > 0 && (
                    <span className="flex flex-wrap items-center gap-1.5 font-medium text-foreground pt-0.5">
                      <span>Subtotal: ₹{Number(field.value || 0).toLocaleString("en-IN")}</span>
                      {flightSum > 0 ? (
                        <>
                          <span className="text-muted-foreground/60">+</span>
                          <span>5% GST (Package only): ₹{Math.round(packageSum * 0.05).toLocaleString("en-IN")}</span>
                          <span className="text-muted-foreground/60">=</span>
                          <span className="font-bold text-primary">
                            Grand Total: ₹{(Number(field.value || 0) + Math.round(packageSum * 0.05)).toLocaleString("en-IN")}
                          </span>
                        </>
                      ) : (
                        <>
                          <span className="text-muted-foreground/60">+</span>
                          <span>5% GST: ₹{Math.round(Number(field.value || 0) * 0.05).toLocaleString("en-IN")}</span>
                          <span className="text-muted-foreground/60">=</span>
                          <span className="font-bold text-primary">
                            Grand Total: ₹{Math.round(Number(field.value || 0) * 1.05).toLocaleString("en-IN")}
                          </span>
                        </>
                      )}
                    </span>
                  )}
                </FormDescription>
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
