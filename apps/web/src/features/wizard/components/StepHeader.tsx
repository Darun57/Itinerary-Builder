"use client";

import React from "react";

interface StepHeaderProps {
  title: string;
  description: string;
}

export function StepHeader({ title, description }: StepHeaderProps) {
  return (
    <div className="mb-6 border-b border-border pb-4">
      <h2 className="text-2xl font-semibold tracking-tight text-primary">{title}</h2>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
