"use client";

import WizardForm from "@/features/wizard/components/WizardForm";
import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/features/dashboard/Dashboard";
import { useWizardStore } from "@/features/wizard/store";

export default function Home() {
  const { activeView } = useWizardStore();

  return (
    <AppLayout>
      {activeView === "dashboard" ? (
        <Dashboard />
      ) : (
        <div className="page active animate-in fade-in slide-in-from-bottom-4 duration-500">
          <WizardForm />
        </div>
      )}
    </AppLayout>
  );
}
