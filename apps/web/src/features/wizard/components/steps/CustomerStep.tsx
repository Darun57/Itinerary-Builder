"use client";

import React from "react";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { StepHeader } from "../StepHeader";

export default function CustomerStep() {
  const { control } = useFormContext<TripRequestType>();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <StepHeader title="Customer Details" description="Enter the lead traveler's contact information." />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FormField
          control={control}
          name="customer_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">Full Name *</FormLabel>
              <FormControl>
                <Input placeholder="John Doe" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="customer_email"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">Email Address *</FormLabel>
              <FormControl>
                <Input type="email" placeholder="john@example.com" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="customer_phone_number"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">Phone Number *</FormLabel>
              <FormControl>
                <Input type="tel" placeholder="+91 9876543210" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="lead_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">CRM Lead ID</FormLabel>
              <FormControl>
                <Input placeholder="L-12345 (Optional)" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="customer_nationality"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">Nationality *</FormLabel>
              <FormControl>
                <Input placeholder="Indian" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="customer_country"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-foreground">Country of Residence *</FormLabel>
              <FormControl>
                <Input placeholder="India" className="bg-background/50" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </div>
  );
}
