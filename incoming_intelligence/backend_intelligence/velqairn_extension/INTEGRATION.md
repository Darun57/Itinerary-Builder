# Integration plan — Rajasthan + Jammu & Kashmir

## What this adds

1. `destination_registry.py` — isolated loader for destination-scoped intelligence.
2. `destination_intelligence.py` — Pydantic contracts for destinations, attractions, activities, movements and day plans.
3. `velqairn_destination_data/rajasthan/` — Rajasthan seed intelligence.
4. `velqairn_destination_data/jammu_and_kashmir/` — Jammu & Kashmir seed intelligence.

## What it does NOT change

- Existing `data/*.csv`
- Existing `data_loader.py`
- Existing Andaman itinerary behavior
- Existing PDF service
- Existing recommendation engine
- Existing CRM
- Existing WhatsApp services
- Existing frontend routes/components

## Safe integration sequence

### Phase 1 — Read-only registry

Use `build_destination_context(region)` only when a non-Andaman region is explicitly selected.

### Phase 2 — Employee destination selection

Map the employee's selected state/region to the registry namespace:

- Rajasthan → `rajasthan`
- Jammu & Kashmir → `jammu-and-kashmir`

### Phase 3 — Trip-state adapter

Translate the selected destination records into the existing `TripRequest` structure. Do not alter the existing Andaman `DayPlan` contract yet.

### Phase 4 — Planner

Generate a structured plan from the destination records first. The LLM may reorder, personalize or narrate the plan, but it must not create IDs that do not exist in the selected namespace.

### Phase 5 — Validation

Run destination validation before PDF generation. Any unresolved hotel, activity, movement, timing or price should be flagged instead of invented.

### Phase 6 — Hotels and rooms

Populate supplier-verified inventory later. Do not copy Andaman hotels into Rajasthan/Kashmir and do not create fake hotel inventory just to make the UI look complete.

## Important

This extension is a **knowledge layer**, not a booking engine. Live supplier/API integrations remain separate work.
