"use client";

import React from "react";
import { useWizardStore } from "../store";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../schema";

export function TripSummarySidebar() {
  const { step, formData } = useWizardStore();
  const { watch } = useFormContext<TripRequestType>();
  
  // Watch real-time form values to dynamically update the summary
  const customerName = watch("customer_name") || formData.customer_name;
  const arrival = watch("arrival_date") || formData.arrival_date;
  const departure = watch("departure_date") || formData.departure_date;
  const islands = watch("selected_destinations") || formData.selected_destinations;
  const hotels = watch("selected_hotels") || formData.selected_hotels;
  const activities = watch("preferred_activities") || formData.preferred_activities;
  const meals = watch("meal_plan") || formData.meal_plan;

  // Calculate progress percentage (steps 1-5)
  const progressPercent = Math.round((Math.min(step, 5) / 5) * 100);
  
  // Format dates
  const travelDates = arrival && departure ? `${arrival} to ${departure}` : 'Not set';

  return (
    <div className="summary-card">
      <div className="summary-title"><i className="ti ti-notebook"></i>Trip summary</div>
      
      <div className="sum-row">
        <span className="sum-label">Customer</span>
        <span className="sum-val">{customerName || "Not set"}</span>
      </div>
      
      <div className="sum-row">
        <span className="sum-label">Travel dates</span>
        <span className="sum-val">{travelDates}</span>
      </div>
      
      <div className="sum-row">
        <span className="sum-label">Destinations</span>
        <span className="sum-val">{islands?.length > 0 ? islands.join(", ") : "Not selected"}</span>
      </div>
      
      <div className="sum-row">
        <span className="sum-label">Hotels</span>
        <span className="sum-val">{hotels?.length > 0 ? `${hotels.length} selected` : "Not selected"}</span>
      </div>
      
      <div className="sum-row">
        <span className="sum-label">Activities</span>
        <span className="sum-val">{activities?.length > 0 ? `${activities.length} selected` : "Not selected"}</span>
      </div>
      
      <div className="sum-row">
        <span className="sum-label">Meal plan</span>
        <span className="sum-val">{meals || "Not selected"}</span>
      </div>
      
      <div className="progress-wrap">
        <div className="progress-label"><span>Build progress</span><span>{progressPercent}%</span></div>
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${progressPercent}%` }}></div></div>
      </div>
      
      <div className="ai-readiness">
        <i className="ti ti-sparkles"></i>
        {progressPercent === 100 ? "AI readiness: Ready to Generate!" : "AI readiness: gathering context"}
      </div>
    </div>
  );
}
