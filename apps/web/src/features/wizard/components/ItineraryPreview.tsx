"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useWizardStore } from "../store";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FileText, Edit2, Loader2 } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { generatePDF } from "@/lib/api";
import { TripRequestType } from "../schema";

export default function ItineraryPreview() {
  const { formData, generatedItinerary, setGeneratedItinerary } = useWizardStore();

  const pdfMutation = useMutation({
    mutationFn: generatePDF,
    onSuccess: (blob) => {
      // Create a blob URL and trigger an automatic secure download
      const url = window.URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Darun_Luxury_Itinerary_${formData.customer_name?.replace(/\s+/g, '_') || "Preview"}.pdf`);
      document.body.appendChild(link);
      link.click();
      
      // Cleanup the DOM
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
    onError: (error: any) => {
      console.error("PDF Generation failed:", error);
      alert(error?.message || "Failed to generate PDF. Ensure the FastAPI backend is running.");
    }
  });

  if (!generatedItinerary) return null;

  const handleDownloadPDF = () => {
    pdfMutation.mutate({
      request: formData as TripRequestType,
      itinerary_text: generatedItinerary
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-4 md:p-6 mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-primary">Your Generated Itinerary</h2>
          <p className="text-muted-foreground mt-1">Review the AI-crafted proposal before generating the final PDF.</p>
        </div>
        <div className="flex space-x-4">
          <Button variant="outline" onClick={() => setGeneratedItinerary(null)} disabled={pdfMutation.isPending}>
            <Edit2 className="w-4 h-4 mr-2" />
            Edit Wizard
          </Button>
          <Button 
            onClick={handleDownloadPDF} 
            disabled={pdfMutation.isPending}
            className="bg-accent text-accent-foreground hover:bg-accent/90 shadow-md shadow-accent/20 min-w-[160px]"
          >
            {pdfMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 mr-2" />
                Download PDF
              </>
            )}
          </Button>
        </div>
      </div>

      <Card className="border-border/50 shadow-lg bg-card/80 backdrop-blur-sm overflow-hidden">
        <CardContent className="p-6 md:p-10 space-y-8">
          {(() => {
            try {
              const data = JSON.parse(generatedItinerary);
              if (data && Array.isArray(data.days) && data.days.length > 0) {
                const sortedDays = [...data.days].sort((a, b) => (a.day_number || 0) - (b.day_number || 0));
                return (
                  <div className="space-y-12">
                    {sortedDays.map((day: any, idx: number) => (
                      <div key={idx} className="border-b border-border/40 pb-8 last:border-b-0 space-y-6">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-l-4 border-amber-500 pl-4 py-1 bg-amber-500/5 rounded-r-lg">
                          <div>
                            <span className="text-xs uppercase font-bold tracking-widest text-amber-500">Day {day.day_number || idx + 1}</span>
                            <h3 className="text-2xl font-bold text-foreground mt-0.5">{day.title || `Day ${day.day_number}: ${day.primary_island || ''}`}</h3>
                          </div>
                          {day.hotel && (
                            <span className="inline-flex items-center text-xs font-semibold px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full">
                              🏨 {day.hotel}
                            </span>
                          )}
                        </div>

                        {/* SECTION 1: DESTINATION STORY */}
                        {(day.destination_story || day.morning) && (
                          <div className="space-y-1 bg-card/40 p-4 rounded-lg border border-border/30">
                            <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                              📖 Destination Story
                            </h4>
                            <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-line">
                              {day.destination_story || day.morning}
                            </p>
                          </div>
                        )}

                        {/* SECTION 2: TODAY'S JOURNEY */}
                        {day.todays_journey && (
                          <div className="space-y-1 bg-card/40 p-4 rounded-lg border border-border/30">
                            <h4 className="text-sm font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-2">
                              🛥️ Today's Journey & Transfers
                            </h4>
                            <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-line">
                              {day.todays_journey}
                            </p>
                          </div>
                        )}

                        {/* SECTION 3: HOTEL EXPERIENCE */}
                        {(day.hotel_experience || day.overnight) && (
                          <div className="space-y-1 bg-card/40 p-4 rounded-lg border border-border/30">
                            <h4 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                              🏨 Hotel Experience
                            </h4>
                            <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-line">
                              {day.hotel_experience || day.overnight}
                            </p>
                          </div>
                        )}

                        {/* SECTION 4: CURATED EXPERIENCE */}
                        {(day.curated_experience || day.afternoon) && (
                          <div className="space-y-1 bg-card/40 p-4 rounded-lg border border-border/30">
                            <h4 className="text-sm font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-2">
                              ✨ Curated Luxury Experience
                            </h4>
                            <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-line">
                              {day.curated_experience || day.afternoon}
                            </p>
                          </div>
                        )}

                      </div>
                    ))}
                  </div>
                );
              }
            } catch (e) {
              // Fallback to Markdown
            }
            return (
              <div className="prose prose-invert prose-headings:text-primary prose-a:text-accent max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {generatedItinerary}
                </ReactMarkdown>
              </div>
            );
          })()}
        </CardContent>
      </Card>
      
    </div>
  );
}
