// Mock localStorage in Node environment before importing store
const storageMap = new Map<string, string>();
const localStorageMock = {
  getItem: (key: string) => storageMap.get(key) ?? null,
  setItem: (key: string, val: string) => storageMap.set(key, val),
  removeItem: (key: string) => storageMap.delete(key),
  clear: () => storageMap.clear(),
};
(globalThis as any).localStorage = localStorageMock;
(globalThis as any).window = globalThis;

import assert from "node:assert";
import { useWizardStore, sanitizeDestinationFormData } from "../store";
import { resolvePrimaryIsland } from "../utils";
import { getDestinationDayDefaults } from "../destinationDefaults";
import { TripRequestType } from "../schema";

function runTests() {
  console.log("=== RUNNING FRONTEND DESTINATION ISOLATION TEST SUITE ===\n");
  let passed = 0;
  let failed = 0;

  function test(name: string, fn: () => void) {
    try {
      fn();
      console.log(`[PASS] ${name}`);
      passed++;
    } catch (err: any) {
      console.error(`[FAIL] ${name}`);
      console.error(err);
      failed++;
    }
  }

  // 1. destination switch clears stale ferry selections
  test("1. destination switch clears stale ferry selections", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      preferred_ferries: ["Govt Ferry (DSS)", "Makruzz"],
    });

    assert.deepStrictEqual(useWizardStore.getState().formData.preferred_ferries, ["Govt Ferry (DSS)", "Makruzz"]);

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const ferries = useWizardStore.getState().formData.preferred_ferries;
    assert.deepStrictEqual(ferries, [], `Expected empty ferries for Goa, got ${JSON.stringify(ferries)}`);
  });

  // 2. destination switch clears stale activity selections
  test("2. destination switch clears stale activity selections", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      preferred_activities: ["ACT-034: Candlelight Beachfront Dinner Havelock", "Cellular Jail Light and Sound Show"],
      included_activities: [
        { activity_name: "Scuba Diving", quantity: 1, is_free: true, location: "Havelock", category: "Water Sports" },
      ],
    });

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const state = useWizardStore.getState().formData;
    assert.deepStrictEqual(state.preferred_activities, [], "preferred_activities must be cleared");
    assert.deepStrictEqual(state.included_activities, [], "included_activities must be cleared");
  });

  // 3. destination switch clears stale hotel selections
  test("3. destination switch clears stale hotel selections", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      selected_hotels: ["Symphony Palms Beach Resort", "Taj Exotica Havelock"],
      hotel_selection_islands: ["Havelock", "Port Blair"],
    });

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const state = useWizardStore.getState().formData;
    assert.deepStrictEqual(state.selected_hotels, [], "selected_hotels must be cleared");
    assert.deepStrictEqual(state.hotel_selection_islands, [], "hotel_selection_islands must be cleared");
  });

  // 4. destination switch resets daily plan
  test("4. destination switch resets daily plan", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      number_of_days: 3,
      daily_island_plan: [
        { day_number: 1, primary_island: "Port Blair", attractions: ["Cellular Jail"], activities: [], hotel: "", transfer_type: "Private Cab", ferry: "", ferry_timing: "" },
        { day_number: 2, primary_island: "Swaraj Dweep (Havelock)", attractions: ["Radhanagar Beach"], activities: [], hotel: "", transfer_type: "Private Cab", ferry: "Makruzz", ferry_timing: "08:00 AM" },
        { day_number: 3, primary_island: "Departure", attractions: ["Departure"], activities: [], hotel: "", transfer_type: "Private Cab", ferry: "", ferry_timing: "" },
      ],
    });

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const plan = useWizardStore.getState().formData.daily_island_plan || [];
    assert.strictEqual(plan.length, 3, "Plan must match day count");

    // Must be seeded with Goa regions, not Andaman
    assert.strictEqual(plan[0].primary_island, "Candolim");
    assert.ok(plan[0].attractions.includes("Fort Aguada") || plan[0].attractions.includes("Candolim Beach"));

    // Verify zero Andaman terms
    const allText = JSON.stringify(plan).toLowerCase();
    assert.ok(!allText.includes("port blair"), "Plan must not contain Port Blair");
    assert.ok(!allText.includes("havelock"), "Plan must not contain Havelock");
    assert.ok(!allText.includes("cellular"), "Plan must not contain Cellular Jail");
  });

  // 5. Andaman → Goa isolation
  test("5. Andaman → Goa isolation", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      number_of_days: 5,
      preferred_ferries: ["Govt Ferry (DSS)"],
      preferred_activities: ["ACT-034: Candlelight Beachfront Dinner Havelock"],
      selected_hotels: ["Symphony Palms Beach Resort"],
      selected_destinations: ["Port Blair", "Swaraj Dweep (Havelock)", "Shaheed Dweep (Neil)"],
    });

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const state = useWizardStore.getState().formData;

    assert.strictEqual(state.destination, "Goa");
    assert.deepStrictEqual(state.preferred_ferries, []);
    assert.deepStrictEqual(state.preferred_activities, []);
    assert.deepStrictEqual(state.selected_hotels, []);
    assert.deepStrictEqual(state.selected_destinations, []);

    const planText = JSON.stringify(state.daily_island_plan).toLowerCase();
    assert.ok(!planText.includes("port blair"), "No Port Blair in Goa plan");
    assert.ok(!planText.includes("havelock"), "No Havelock in Goa plan");
    assert.ok(!planText.includes("cellular"), "No Cellular Jail in Goa plan");
    assert.ok(!planText.includes("radhanagar"), "No Radhanagar in Goa plan");
  });

  // 6. Goa → Rajasthan isolation
  test("6. Goa → Rajasthan isolation", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Goa",
      number_of_days: 4,
      selected_hotels: ["Taj Exotica Resort & Spa, Goa"],
      selected_destinations: ["Candolim", "Panaji"],
      preferred_activities: ["Baga Beach Water Sports"],
    });

    // Switch to Rajasthan
    useWizardStore.getState().updateFormData({ destination: "Rajasthan" });
    const state = useWizardStore.getState().formData;

    assert.strictEqual(state.destination, "Rajasthan");
    assert.deepStrictEqual(state.selected_hotels, [], "Goa hotels must not survive");
    assert.deepStrictEqual(state.selected_destinations, [], "Goa locations must not survive");
    assert.deepStrictEqual(state.preferred_activities, [], "Goa activities must not survive");

    const plan = state.daily_island_plan || [];
    assert.strictEqual(plan[0].primary_island, "Jaipur");
    assert.ok(plan[0].attractions.includes("Amber Fort"));
  });

  // 7. Rajasthan → Kashmir isolation
  test("7. Rajasthan → Kashmir isolation", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Rajasthan",
      number_of_days: 3,
      selected_hotels: ["Umaid Bhawan Palace Jodhpur"],
      selected_destinations: ["Jaipur", "Jodhpur"],
      preferred_activities: ["Desert Safari Jaisalmer"],
    });

    // Switch to Jammu & Kashmir
    useWizardStore.getState().updateFormData({ destination: "Jammu & Kashmir" });
    const state = useWizardStore.getState().formData;

    assert.strictEqual(state.destination, "Jammu & Kashmir");
    assert.deepStrictEqual(state.selected_hotels, [], "Rajasthan hotels must not survive");
    assert.deepStrictEqual(state.selected_destinations, [], "Rajasthan locations must not survive");
    assert.deepStrictEqual(state.preferred_activities, [], "Rajasthan activities must not survive");

    const plan = state.daily_island_plan || [];
    assert.strictEqual(plan[0].primary_island, "Srinagar");
    assert.ok(plan[0].attractions.includes("Dal Lake Shikara"));
  });

  // 8. persisted stale Andaman state cannot contaminate Goa
  test("8. persisted stale Andaman state cannot contaminate Goa", () => {
    // Simulate raw contaminated object from old localStorage
    const stalePersistedFormData: Partial<TripRequestType> = {
      destination: "Goa",
      number_of_days: 5,
      preferred_ferries: ["Govt Ferry (DSS)", "Makruzz"],
      preferred_activities: ["ACT-034: Candlelight Beachfront Dinner Havelock"],
      selected_hotels: ["Symphony Palms Beach Resort"],
      selected_destinations: ["Port Blair", "Havelock"],
      daily_island_plan: [
        { day_number: 1, primary_island: "Port Blair", attractions: ["Cellular Jail"], activities: [], hotel: "Symphony Palms", transfer_type: "Private Cab", ferry: "", ferry_timing: "" },
        { day_number: 2, primary_island: "Swaraj Dweep (Havelock)", attractions: ["Radhanagar Beach"], activities: [], hotel: "", transfer_type: "Private Cab", ferry: "Makruzz", ferry_timing: "08:00 AM" },
      ],
    };

    const sanitized = sanitizeDestinationFormData(stalePersistedFormData);

    assert.deepStrictEqual(sanitized.preferred_ferries, [], "Sanitizer must remove ferries for Goa");
    assert.deepStrictEqual(sanitized.preferred_activities, [], "Sanitizer must remove Andaman activities");
    assert.deepStrictEqual(sanitized.selected_hotels, [], "Sanitizer must remove Andaman hotels");
    assert.deepStrictEqual(sanitized.selected_destinations, [], "Sanitizer must remove Andaman destinations");

    const plan = sanitized.daily_island_plan || [];
    assert.ok(plan.length >= 5, "Plan must be regenerated to 5 days");
    assert.strictEqual(plan[0].primary_island, "Candolim");
    const planText = JSON.stringify(plan).toLowerCase();
    assert.ok(!planText.includes("port blair"), "Sanitized plan must not contain Port Blair");
    assert.ok(!planText.includes("cellular"), "Sanitized plan must not contain Cellular Jail");
  });

  // 9. generic fields survive destination switch
  test("9. generic fields survive destination switch", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      customer_name: "Ananya Sharma",
      customer_email: "ananya@example.com",
      customer_phone_number: "+91 9876543210",
      customer_nationality: "Indian",
      customer_country: "India",
      number_of_days: 6,
      number_of_nights: 5,
      arrival_date: "2026-11-10",
      departure_date: "2026-11-15",
      trip_type: "Family Vacation",
      budget_category: "Luxury",
      travel_style: ["Bespoke Luxury", "Relaxed & Leisure"],
      trip_pace: "Slow",
      meal_plan: "MAP (Breakfast & Dinner)",
      food_preferences: ["Vegetarian", "Jain Food"],
      hotel_category_preference: "5 Star Luxury",
      day_wise_style: "luxury_narrative",
      // Stale destination-specific fields
      preferred_ferries: ["Govt Ferry (DSS)"],
      selected_hotels: ["Welcomhotel Port Blair"],
    });

    // Switch to Goa
    useWizardStore.getState().updateFormData({ destination: "Goa" });
    const state = useWizardStore.getState().formData;

    // Generic fields MUST survive
    assert.strictEqual(state.customer_name, "Ananya Sharma");
    assert.strictEqual(state.customer_email, "ananya@example.com");
    assert.strictEqual(state.customer_phone_number, "+91 9876543210");
    assert.strictEqual(state.customer_nationality, "Indian");
    assert.strictEqual(state.customer_country, "India");
    assert.strictEqual(state.number_of_days, 6);
    assert.strictEqual(state.number_of_nights, 5);
    assert.strictEqual(state.arrival_date, "2026-11-10");
    assert.strictEqual(state.departure_date, "2026-11-15");
    assert.strictEqual(state.trip_type, "Family Vacation");
    assert.strictEqual(state.budget_category, "Luxury");
    assert.deepStrictEqual(state.travel_style, ["Bespoke Luxury", "Relaxed & Leisure"]);
    assert.strictEqual(state.trip_pace, "Slow");
    assert.strictEqual(state.meal_plan, "MAP (Breakfast & Dinner)");
    assert.deepStrictEqual(state.food_preferences, ["Vegetarian", "Jain Food"]);
    assert.strictEqual(state.hotel_category_preference, "5 Star Luxury");
    assert.strictEqual(state.day_wise_style, "luxury_narrative");

    // Destination-specific fields MUST be cleared
    assert.deepStrictEqual(state.preferred_ferries, []);
    assert.deepStrictEqual(state.selected_hotels, []);
  });

  // 10. Andaman existing behavior remains intact
  test("10. Andaman existing behavior remains intact", () => {
    useWizardStore.getState().resetWizard();
    useWizardStore.getState().updateFormData({
      destination: "Andaman Islands",
      number_of_days: 4,
    });

    const state = useWizardStore.getState().formData;
    assert.strictEqual(state.destination, "Andaman Islands");
    const plan = state.daily_island_plan || [];
    assert.strictEqual(plan.length, 4);

    // Andaman defaults must be present
    assert.strictEqual(plan[0].primary_island, "Port Blair");
    assert.ok(plan[0].attractions.includes("Cellular Jail"));
    assert.strictEqual(plan[2].primary_island, "Swaraj Dweep (Havelock)");
    assert.ok(plan[2].attractions.includes("Radhanagar Beach"));

    // Test resolvePrimaryIsland backward compatibility for Andaman
    const resolvedDay0 = resolvePrimaryIsland({ attractions: [] }, 0, "Andaman Islands");
    assert.strictEqual(resolvedDay0, "Port Blair");

    const resolvedDay1 = resolvePrimaryIsland({ attractions: [] }, 1, "Andaman Islands");
    assert.strictEqual(resolvedDay1, "Swaraj Dweep (Havelock)");

    const resolvedAttraction = resolvePrimaryIsland({ attractions: ["Radhanagar Beach"] }, 0, "Andaman Islands");
    assert.strictEqual(resolvedAttraction, "Swaraj Dweep (Havelock)");

    // Non-Andaman resolution NEVER returns Port Blair/Havelock
    const resolvedGoa = resolvePrimaryIsland({ attractions: [] }, 0, "Goa");
    assert.strictEqual(resolvedGoa, "Candolim");

    const resolvedRajasthan = resolvePrimaryIsland({ attractions: [] }, 0, "Rajasthan");
    assert.strictEqual(resolvedRajasthan, "Jaipur");
  });

  console.log(`\n=== RESULTS: ${passed} PASSED, ${failed} FAILED ===`);
  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
