"use client";

import WizardForm from "@/features/wizard/components/WizardForm";
import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/features/dashboard/Dashboard";
import { CRMLayout } from "@/features/crm/components/CRMLayout";
import { MarketingHub } from "@/features/marketing/MarketingHub";
import { useWizardStore } from "@/features/wizard/store";

export default function Home() {
  const { activeView, setActiveView } = useWizardStore();

  if (activeView === "crm") {
    return <CRMLayout onBack={() => setActiveView("dashboard")} />;
  }

  return (
    <AppLayout>
      {activeView === "dashboard" && <Dashboard />}
      {activeView === "builder" && (
        <div className="page active animate-in fade-in slide-in-from-bottom-4 duration-500">
          <WizardForm />
        </div>
      )}
      {activeView === "marketing" && <MarketingHub />}
    </AppLayout>
  );
}
