# Velqairn India Destination Scaffold

This folder is an ADDITIVE destination-data scaffold for the Velqairn project.

## Protected system

The existing Darun Tourism / Andaman implementation is the protected running reference.
Do not overwrite, rename, move, or merge its existing files merely to add new destinations.

## Namespace rule

Every destination must be isolated by its own state/UT folder and slug.

Use destination-scoped identifiers such as:

    rajasthan:jaipur
    rajasthan:udaipur
    jammu-and-kashmir:srinagar
    kashmir:gulmarg

Do not use globally ambiguous IDs such as:

    hotel_01
    image_01
    activity_01

unless they are prefixed/scoped by destination.

## Asset rule

New destination assets must remain inside their destination's `images/` directory.

Never place Rajasthan/Kashmir images into the existing Andaman image folders.

## Data rule

New destination data belongs in that destination's `data/`, `hotels/`, `activities/`, etc.

Do not overwrite the existing Andaman CSVs, JSON, images, PDFs, prompts, or configuration.

## Output rule

Itinerary generation, PDF generation, image resolution, hotel resolution, activity resolution and movement resolution must always resolve through the selected destination namespace.

A Rajasthan request must never resolve an Andaman asset.
A Kashmir request must never resolve a Rajasthan asset.
An Andaman request must continue resolving the existing Darun Tourism data exactly as before.

## Current scaffold

28 Indian States + 8 Union Territories are included.

The folders are intentionally empty scaffolds so destination data can be added progressively.
