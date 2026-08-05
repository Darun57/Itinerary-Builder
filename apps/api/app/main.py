import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints, auth

load_dotenv(override=True)

app = FastAPI(
    title="Darun Tourism AI Itinerary API",
    description="Backend API for generating luxury travel itineraries.",
    version="1.0.0",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api", tags=["itinerary"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Darun Tourism API is running"}
