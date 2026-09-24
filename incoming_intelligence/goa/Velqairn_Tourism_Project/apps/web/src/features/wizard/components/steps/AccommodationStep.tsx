"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchHotelRecommendations, fetchAllHotels, createHotel, NewHotelPayload } from "@/lib/api";
import { useWizardStore } from "../../store";
import { StepHeader } from "../StepHeader";
import { HotelCarousel } from "../HotelCarousel";

// ── Goa hotel locations available in the system ────────────────────────────────
const GOA_HOTEL_LOCATIONS = [
  "Panaji", "Candolim", "Calangute", "Baga", "Vagator", "Anjuna",
  "Arpora", "Old Goa", "Miramar", "Dona Paula", "Vasco da Gama",
  "Arossim", "Utorda", "Majorda", "Betalbatim", "Colva", "Benaulim",
  "Varca", "Cavelossim", "Mobor", "Palolem", "Patnem", "Canacona",
  "Bambolim", "Mapusa", "Fontainhas", "Saligao", "Assagao", "Siolim",
  "Bicholim", "Ponda",
];

const HOTEL_CATEGORIES = ["2 Star", "3 Star", "4 Star", "5 Star", "Boutique"];

const ROOM_TYPES = [
  "Standard Room",
  "Deluxe Room",
  "Superior Room",
  "Sea View Room",
  "Pool View Room",
  "Garden View Room",
  "Cottage",
  "Bungalow",
  "Suite",
  "Luxury Suite",
  "Family Room",
  "Connecting Rooms",
  "Beach Hut",
];

// ── Add Hotel Modal ──────────────────────────────────────────────────────────
interface AddHotelModalProps {
  onClose: () => void;
  onSaved: (hotelName: string) => void;
}

function AddHotelModal({ onClose, onSaved }: AddHotelModalProps) {
  const [form, setForm] = useState<NewHotelPayload>({
    hotel_name: "",
    location: "",
    category: "",
    room_type: "",
    description: "",
    availability_status: "Available",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (key: keyof NewHotelPayload, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.hotel_name.trim()) return setError("Hotel name is required.");
    if (!form.location) return setError("Location is required.");
    if (!form.category) return setError("Category is required.");
    setSaving(true);
    setError("");
    try {
      await createHotel(form);
      onSaved(form.hotel_name.trim());
    } catch (err: any) {
      setError(err.message || "Failed to save hotel. Try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-[#0E1117] border border-white/10 rounded-2xl w-full max-w-lg mx-4 shadow-2xl flex flex-col"
        style={{ animation: "slideUp 0.2s ease" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div>
            <h2 className="text-base font-semibold text-white">Add New Hotel</h2>
            <p className="text-xs text-white/50 mt-0.5">Saved permanently to the hotel database</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/40 hover:text-white hover:bg-white/10 rounded-lg w-8 h-8 flex items-center justify-center transition-all"
          >
            <i className="ti ti-x text-lg" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Hotel Name */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">
              Hotel Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Ocean Breeze Resort & Spa"
              value={form.hotel_name}
              onChange={(e) => handleChange("hotel_name", e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white placeholder-white/25 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
            />
          </div>

          {/* Location + Category row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">
                Location <span className="text-red-400">*</span>
              </label>
              <select
                value={form.location}
                onChange={(e) => handleChange("location", e.target.value)}
                className="w-full bg-white/5 border border-white/10 text-white rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
              >
                <option value="" className="bg-[#0E1117] text-white/40">Select location</option>
                {GOA_HOTEL_LOCATIONS.map((loc) => (
                  <option key={loc} value={loc} className="bg-[#0E1117] text-white">{loc}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">
                Category <span className="text-red-400">*</span>
              </label>
              <select
                value={form.category}
                onChange={(e) => handleChange("category", e.target.value)}
                className="w-full bg-white/5 border border-white/10 text-white rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
              >
                <option value="" className="bg-[#0E1117] text-white/40">Select category</option>
                {HOTEL_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat} className="bg-[#0E1117] text-white">{cat}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Room Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">Room Type</label>
            <select
              value={form.room_type}
              onChange={(e) => handleChange("room_type", e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
            >
              <option value="" className="bg-[#0E1117] text-white/40">Select room type</option>
              {ROOM_TYPES.map((rt) => (
                <option key={rt} value={rt} className="bg-[#0E1117] text-white">{rt}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">Description</label>
            <textarea
              placeholder="Short description of the hotel (optional)"
              value={form.description}
              onChange={(e) => handleChange("description", e.target.value)}
              rows={3}
              className="w-full bg-white/5 border border-white/10 text-white placeholder-white/25 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all resize-none"
            />
          </div>

          {/* Availability */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">Availability</label>
            <div className="flex gap-3">
              {["Available", "Limited Availability"].map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleChange("availability_status", opt)}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold border transition-all ${
                    form.availability_status === opt
                      ? "bg-primary/20 border-primary/60 text-primary"
                      : "bg-white/5 border-white/10 text-white/50 hover:border-white/20"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
              <i className="ti ti-alert-circle" />
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg text-sm font-medium border border-white/10 text-white/50 hover:text-white hover:bg-white/5 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <i className="ti ti-loader-2 animate-spin" />
                  Saving…
                </>
              ) : (
                <>
                  <i className="ti ti-building-store" />
                  Save Hotel
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <style>{`@keyframes slideUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }`}</style>
    </div>
  );
}

// ── Main AccommodationStep ───────────────────────────────────────────────────
export default function AccommodationStep() {
  const { control, getValues, setValue } = useFormContext<TripRequestType>();
  const formData = useWizardStore(state => state.formData);
  const queryClient = useQueryClient();

  const watchedValues = useWatch({ control });
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  const currentRequestData = { ...formData, ...getValues(), ...watchedValues } as TripRequestType;
  const selectedHotels: string[] = (watchedValues.selected_hotels as string[]) || [];
  const dailyPlan = watchedValues.daily_island_plan || [];

  // Query 1: Recommendations tailored for this itinerary
  const { data: recommendedHotels, isLoading, isError } = useQuery({
    queryKey: [
      "hotels",
      currentRequestData.destination,
      currentRequestData.budget_category,
      currentRequestData.hotel_category_preference,
      currentRequestData.hotel_selection_islands?.join(","),
      selectedHotels.join(","),
    ],
    queryFn: () => {
      const liveData = { ...formData, ...getValues(), ...watchedValues } as TripRequestType;
      return fetchHotelRecommendations(liveData);
    },
    staleTime: 0,
  });

  // Query 2: Full hotel catalog for instant global search across all Goa locations & categories
  const { data: allHotels } = useQuery({
    queryKey: ["all-hotels"],
    queryFn: fetchAllHotels,
    staleTime: 1000 * 60 * 5,
  });

  // Group hotels by location. When searching, search allHotels so newly added or any-category hotels are found instantly.
  const hotelsByLocation = useMemo(() => {
    const isSearching = searchQuery.trim() !== "";
    const sourceList = isSearching && allHotels && allHotels.length > 0
      ? allHotels
      : (recommendedHotels || []);

    if (!sourceList.length) return {};

    const filtered = !isSearching
      ? sourceList
      : sourceList.filter(
          (h: any) =>
            (h.hotel_name && h.hotel_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (h.description && h.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (h.room_type && h.room_type.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (h.category && h.category.toLowerCase().includes(searchQuery.toLowerCase()))
        );

    return filtered.reduce((acc: Record<string, any[]>, hotel: any) => {
      const loc = hotel.location || "Other";
      if (!acc[loc]) acc[loc] = [];
      acc[loc].push(hotel);
      return acc;
    }, {});
  }, [recommendedHotels, allHotels, searchQuery]);

  const isDepartureDay = (day: any) => {
    if (!day) return false;
    const location = (day.primary_island || "").toLowerCase().trim();
    const attractions = Array.isArray(day.attractions) ? day.attractions : [];
    return location === "departure" || attractions.some((a: string) => String(a).toLowerCase().trim() === "departure");
  };

  // Auto-assign hotels to days when selection changes
  useEffect(() => {
    if (!selectedHotels.length || !dailyPlan.length) return;
    const hotelPool = (recommendedHotels || []).concat(allHotels || []);

    const hotelLocationMap: Record<string, string> = {};
    for (const h of hotelPool) {
      if (selectedHotels.includes(h.hotel_name)) {
        const loc = (h.location || "").toLowerCase().trim();
        if (!hotelLocationMap[loc]) hotelLocationMap[loc] = h.hotel_name;
      }
    }

    const currentPlan = getValues("daily_island_plan") || [];
    let updated = false;
    const newPlan = currentPlan.map((day: any, idx: number) => {
      const isLast = idx === currentPlan.length - 1;
      if (isLast && isDepartureDay(day)) {
        if (day.hotel) { updated = true; return { ...day, hotel: "" }; }
        return day;
      }
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
  }, [selectedHotels.join(","), recommendedHotels, allHotels]);

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

  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  // Called when a new hotel is saved from the modal
  const handleHotelSaved = async (hotelName: string) => {
    setShowAddModal(false);
    setSearchQuery(""); // clear search so all hotels including new one are visible

    // Auto-select the new hotel FIRST so pinning logic in backend includes it on refetch
    const current: string[] = getValues("selected_hotels") || [];
    if (!current.includes(hotelName)) {
      setValue("selected_hotels", [...current, hotelName], { shouldDirty: true });
    }

    // Invalidate both recommended hotels and all hotels queries
    await queryClient.invalidateQueries({ queryKey: ["hotels"] });
    await queryClient.invalidateQueries({ queryKey: ["all-hotels"] });

    // Show a brief success notice
    setSavedNotice(`"${hotelName}" added and selected ✓`);
    setTimeout(() => setSavedNotice(null), 5000);
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

        {/* Search + Add Hotel button */}
        <div className="flex gap-3 items-center">
          <Input
            placeholder="Search hotels by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md bg-background/50"
          />
          <button
            type="button"
            id="add-hotel-btn"
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-primary/40 bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 hover:border-primary/70 transition-all whitespace-nowrap"
          >
            <i className="ti ti-plus text-base" />
            Add New Hotel
          </button>
        </div>

        {/* Success notice */}
        {savedNotice && (
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium animate-in fade-in slide-in-from-top-2 duration-300">
            <i className="ti ti-circle-check text-base" />
            {savedNotice} — scroll down to assign it to a day.
          </div>
        )}

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
            {Array.from({
              length: (numberOfDays > 0 && isDepartureDay(dailyPlan[numberOfDays - 1]))
                ? numberOfDays - 1
                : numberOfDays
            }).map((_, index) => (
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
              const isFinalDep = numberOfDays > 0 && isDepartureDay(dailyPlan[numberOfDays - 1]);
              const plan = ((watchedValues.daily_island_plan as any[]) || []).slice(0, isFinalDep ? numberOfDays - 1 : numberOfDays);
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

      {/* Add Hotel Modal */}
      {showAddModal && (
        <AddHotelModal
          onClose={() => setShowAddModal(false)}
          onSaved={handleHotelSaved}
        />
      )}
    </div>
  );
}
