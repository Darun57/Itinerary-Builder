# Goa Darun Tours and Travels — Tourism ERP & Proposal Engine

A full-stack, enterprise-grade tourism operating system tailored for Goa tourism operations. The platform combines an AI-assisted itinerary builder, a high-fidelity 13-page PDF proposal engine, an integrated CRM (Leads, Clients, Bookings, Staff, Tasks), revenue and profit pipeline analytics, a simplified WhatsApp automation hub, and a multi-channel marketing engine.

---

## System Explanation

### 1. Architecture Overview
The platform is organized as a decoupled monorepo comprising:
- **Frontend (`apps/web`)**: A modern web application built with **Next.js (App Router)**, **React**, and **TypeScript**. It offers an interactive multi-step travel wizard, dynamic itinerary preview, full CRM management dashboards, marketing campaign attribution, and WhatsApp reminder dispatchers.
- **Backend (`apps/api`)**: A high-performance **FastAPI** Python application responsible for business logic, catalog management, itinerary normalization, pricing and margin pipelines, WhatsApp client integration, and multi-page ReportLab PDF generation.
- **Data Catalog (`data/`)**: Structured CSV datasets providing localized Goa data across Panaji, North Goa, Old Goa, South Goa, and Dudhsagar (South Goa) for hotels, ferry schedules, activities, and destinations.
- **Assets Engine (`assets/`)**: High-resolution typography (Cinzel, Montserrat) and curated cover imagery for dynamic document rendering.

### 2. Core Functional Modules

#### AI & Itinerary Proposal Generator
- **Multi-Step Travel Wizard**: Captures traveler demographics, travel dates, pacing style, budget tiers, and activity preferences.
- **Goa Movement & Logistics Normalizer**: Automatically resolves ferry routes, timings, accommodation check-ins, and daily schedules across Goa regions and destinations.
- **ReportLab 13-Page PDF Engine**: Compiles branded luxury proposals including:
  1. Front Cover Page (Cinzel typography, metadata, client details)
  2. Trip Highlights & Experience Overview
  3. Day-by-Day Detailed Itinerary (Narrative, activity badges, meals, stay details)
  4. Accommodation & Hotel Showcase (Star ratings, meal plans, room categories)
  5. Ferry Transfers & Logistics Schedule
  6. Financial Breakdown & Invoice (`ADT-` format, pricing pipeline)
  7. Payment Details & Bank Transfer Methods
  8. Inclusions & Exclusions Specification
  9. Cancellation Agreement & Contract Terms
  10. Payment Agreement & Milestone Schedules
  11. Terms & Conditions Agreement
  12. Back Cover & Contact Reference

#### Comprehensive Tourism CRM
- **Leads & Pipeline**: Tracks traveler leads through qualification, quotation, follow-up, and booking stages.
- **Client Profiles**: Stores client travel history, contact numbers, and preferences.
- **Bookings & Profit Engine**: Computes package cost, selling price, profit margins, and payment collection statuses.
- **Revenue & Profit Charts**: Interactive visualizations displaying revenue pipelines and profit trends.
- **Team Management**: Staff allocation and task assignment boards.

#### WhatsApp Automation Hub
- **Traveler Updates**: One-click WhatsApp message dispatching with pre-filled dynamic templates.
- **Automated Scheduling**: Pre-trip reminders (3 days prior), payment alerts, and post-trip review requests.
- **Clean Action Center**: Direct WhatsApp Web/App launcher (`wa.me`), status completion tracker, and message history logs.

#### Marketing Hub
- **Campaign Tracker**: Tracks multi-channel marketing campaigns (Social Media, Google Ads, Partnerships).
- **Attribution & ROI**: Measures lead conversion rates and marketing cost efficiency.

---

## Folder Structure Design

```text
Darun tourism/
│
├── README.md                                # System overview, architecture, and directory structure design
├── requirements.txt                         # Top-level shared Python dependencies
├── .gitignore                               # Git exclusion rules (pycache, envs, dbs, logs)
│
├── apps/                                    # Application packages
│   │
│   ├── web/                                 # Frontend Application (Next.js, TypeScript, React)
│   │   ├── package.json                     # Frontend dependencies & scripts
│   │   ├── tsconfig.json                    # TypeScript configuration
│   │   ├── next.config.ts                   # Next.js settings & API proxy redirects
│   │   │
│   │   └── src/                             # Frontend source code
│   │       ├── app/                         # App Router root
│   │       │   ├── layout.tsx               # Global root layout and font definitions
│   │       │   ├── page.tsx                 # Main application view router (Wizard / CRM / Marketing / Dashboard)
│   │       │   └── globals.css              # Global styling, themes, and CSS variables
│   │       │
│   │       ├── components/                  # Shared UI components
│   │       │   ├── layout/                  # Shell components (Sidebar, Topbar, AppLayout)
│   │       │   └── Providers.tsx            # Global state providers and context wrappers
│   │       │
│   │       ├── features/                    # Feature-driven application modules
│   │       │   │
│   │       │   ├── wizard/                  # Itinerary creation wizard
│   │       │   │   ├── store.ts             # Zustand state management for itinerary wizard
│   │       │   │   ├── schema.ts            # Form validation schemas
│   │       │   │   └── components/          # Wizard form steps, accommodation cards, live previews
│   │       │   │
│   │       │   ├── crm/                     # Tourism CRM platform
│   │       │   │   ├── api.ts               # CRM and Reminder HTTP API client
│   │       │   │   ├── types.ts             # TypeScript definitions for CRM data models
│   │       │   │   └── components/          # CRM layouts and sub-pages:
│   │       │   │       ├── CRMLayout.tsx    # CRM navigation wrapper and sidebar
│   │       │   │       ├── leads/           # Leads tracking list and modal forms
│   │       │   │       ├── clients/         # Client profiles and contact registry
│   │       │   │       ├── bookings/        # Booking records, status tracking, profit breakdown modal
│   │       │   │       ├── reminders/       # WhatsApp Bot panel and message composer modal
│   │       │   │       ├── staff/           # Staff roster and internal role directory
│   │       │   │       └── tasks/           # Operational task management board
│   │       │   │
│   │       │   ├── dashboard/               # Operational dashboards
│   │       │   │   ├── Dashboard.tsx        # KPI metrics, quick actions, recent bookings
│   │       │   │   ├── RevenuePipelineChart.tsx # Financial revenue pipeline chart
│   │       │   │   └── ProfitPipelineChart.tsx  # Profit margin analytics chart
│   │       │   │
│   │       │   └── marketing/               # Marketing Hub
│   │       │       └── MarketingHub.tsx     # Campaign management, channel analytics, CAC metrics
│   │       │
│   │       └── lib/                         # Client utilities
│   │           └── api.ts                   # Backend API base endpoints and request helpers
│   │
│   └── api/                                 # Backend Application (FastAPI, Python)
│       ├── requirements.txt                 # Python dependencies (FastAPI, Uvicorn, ReportLab, Pydantic)
│       ├── .env                             # Environment configuration
│       │
│       └── app/                             # Python application package
│           ├── main.py                      # FastAPI application entry point, CORS, and route registration
│           │
│           ├── core/                        # Core application settings
│           │   ├── config.py                # Environment variable parsing and application settings
│           │   └── security.py              # Security and authentication helpers
│           │
│           ├── db/                          # Database connection and session management
│           │   └── database.py              # SQLite engine and session factory
│           │
│           ├── models/                      # SQLAlchemy ORM models
│           │   ├── crm.py                   # Lead, Client, Booking, Staff, and Task ORM models
│           │   ├── reminders.py             # WhatsApp Reminder and reminder log ORM models
│           │   └── user.py                  # User and agent account ORM models
│           │
│           ├── schemas/                     # Pydantic validation schemas
│           │   ├── trip.py                  # Itinerary request and response schemas
│           │   ├── crm.py                   # Lead, Client, and Booking request/response schemas
│           │   ├── reminders.py             # WhatsApp message request/response schemas
│           │   └── user.py                  # User validation schemas
│           │
│           ├── api/                         # REST API route endpoints
│           │   ├── endpoints.py             # Itinerary generation and PDF download routes
│           │   ├── crm.py                   # CRM CRUD endpoints (Leads, Bookings, Clients, Metrics)
│           │   └── reminders.py             # WhatsApp dispatch and scheduling endpoints
│           │
│           └── services/                    # Business logic and external service integrations
│               ├── data_loader.py           # CSV data parser for hotels, ferries, destinations
│               ├── recommendations.py       # Rule-based and AI itinerary compilation service
│               ├── google_service.py        # Gemini AI API integration for narrative enrichment
│               ├── prompts.py               # Prompt templates for narrative generation
│               ├── itinerary_normalizer.py  # Structure sanitization and itinerary validator
│               │
│               ├── whatsapp/                # WhatsApp messaging subsystem
│               │   ├── client.py            # WhatsApp dispatch client and message sender
│               │   └── templates.py         # Dynamic pre-trip, payment, and feedback templates
│               │
│               └── pdf/                     # ReportLab PDF Proposal Generator
│                   ├── builder.py           # Canvas orchestrator and multi-page compiler
│                   ├── constants.py         # Page geometry, brand color palette, and styling constants
│                   ├── fonts.py             # Custom TTF font registration (Cinzel, Montserrat)
│                   ├── day_parser.py        # Day-by-day narrative and activity parser
│                   ├── highlight_builder.py # Trip highlight and overview layout helper
│                   ├── image_resolver.py    # Local image loader and aspect ratio scaler
│                   ├── text_utils.py        # Typography wrapping and flowable text helpers
│                   │
│                   └── sections/            # Individual page rendering modules
│                       ├── cover.py         # Front cover page renderer
│                       ├── highlights.py    # Trip summary and highlight cards
│                       ├── day_page.py      # Individual day itinerary pages
│                       ├── hotels.py        # Accommodation showcase and star rating cards
│                       └── policies.py      # Invoice, Payment, Inclusions, and Agreement policy contracts
│
├── data/                                    # Goa Tourism Catalog Data (CSV)
│   ├── destinations.csv                     # Goa points of interest, descriptions, locations
│   ├── hotels.csv                           # Accommodation catalog, price bands, ratings, amenities
│   ├── ferries.csv                          # Goa river, boat, and ferry routes (Mandovi River Cruise, Goa River Ferry, Tiracol Ferry)
│   └── activities.csv                       # Water sports, scuba, trekking, and heritage tours
│
├── assets/                                  # Static binary design assets
│   ├── fonts/                               # TrueType Font files used for PDF rendering
│   │   ├── Cinzel-Bold.ttf                  # Luxury serif font for headings and titles
│   │   ├── Cinzel-Regular.ttf               # Luxury serif font for sub-headings
│   │   ├── Montserrat-Bold.ttf              # Sans-serif bold for metrics and labels
│   │   └── Montserrat-Regular.ttf           # Sans-serif regular for body text
│   │
│   └── images/                              # Visual assets for PDF covers and documents
│       └── default_cover/                   # Curated high-resolution Goa scenery images
│
└── docs/                                    # Project documentation
    └── PROJECT_HISTORY.md                   # Engineering change logs and milestone documentation
```


## Goa configuration
This variant uses Goa-specific destination, hotel, activity, and movement catalogs. The legacy `primary_island` and `daily_island_plan` field names remain in the API schema for compatibility, but the planner treats them as Goa destination regions/locations. Image mapping is intentionally unchanged in this pass.
