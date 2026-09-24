"use client";

import React from "react";
import { useWizardStore } from "../store";

const STEPS = [
  { id: 1, label: "Customer" },
  { id: 2, label: "Trip" },
  { id: 3, label: "Accommodation" },
  { id: 4, label: "Activities" },
  { id: 5, label: "Transport" },
  { id: 6, label: "Generate" },
];

export default function WizardStepper() {
  const { step } = useWizardStore();

  return (
    <div className="stepper">
      {STEPS.map((s, idx) => {
        const isDone = step > s.id;
        const isCurrent = step === s.id;
        
        let stateClass = "";
        if (isDone) stateClass = "done";
        if (isCurrent) stateClass = "current";

        return (
          <React.Fragment key={s.id}>
            <div className={`step ${stateClass}`}>
              <div className="step-circle">
                {isDone ? <i className="ti ti-check" style={{ fontSize: '14px' }}></i> : s.id}
              </div>
              <span className="step-label">{s.label}</span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className="step-connector"></div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
