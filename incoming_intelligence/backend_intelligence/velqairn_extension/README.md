# Velqairn Destination Intelligence Extension

This is an **additive extension pack** for the existing Velqairn/Darun Tourism project.

## Protected rule

The existing Darun Tourism / Andaman implementation is not included here and must not be overwritten or refactored by installing this pack.

The extension introduces destination-scoped intelligence for:

- Rajasthan
- Jammu & Kashmir

It covers the backend knowledge categories needed for the planner:

- destinations / locations
- attractions
- activities / experiences
- movements
- day-plan templates
- destination configuration
- validation metadata

## Important data policy

This first pass is a **planning intelligence seed**, not a live booking inventory.

- Hotels, rooms, prices and availability are intentionally not fabricated.
- Movement times are planning ranges and must be live-verified before customer confirmation.
- Activity prices are marked supplier-required unless verified from an actual supplier.
- Seasonal/operational constraints are explicit so the LLM cannot treat the seed as unconditional truth.

## Installation

Copy the contents of this pack into the Velqairn project root, preserving the paths.

Do not replace existing files. The new Python files are isolated adapters and schemas.

Then integrate the registry at the application boundary after testing. Do not modify the existing Andaman loader unless separately approved.
