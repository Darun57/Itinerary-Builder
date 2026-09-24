"use client";

/**
 * Proposal Studio — Step 6 UI
 * ============================
 * Renders AFTER itinerary generation. Provides:
 *  - Progress bar showing wizard steps + "Proposal Studio" as active step
 *  - Left sidebar: proposal structure (Cover, Highlights, Hotels, Day N, Pricing, Terms)
 *  - Center: Live A4 PDF preview (page N of total)
 *  - Right: Image change panel (upload / destination images)
 *  - Bottom: Validate → Generate Official PDF flow
 *
 * DOES NOT modify WizardForm, WizardStore, or any existing backend logic.
 * Image state is purely local (React useState) and passed to the PDF generator.
 */

import React, { useState, useMemo, useCallback, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Image as ImageIcon,
  Edit2,
  LayoutList,
} from "lucide-react";
import { useWizardStore } from "../../../wizard/store";
import ImageChangerPanel from "./ImageChangerPanel";
import { generatePDF } from "@/lib/api";
import { TripRequestType } from "../../../wizard/schema";
import { getDestinationImages } from "../destinationImages";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SectionDef {
  id: string;
  label: string;
  icon: React.ReactNode;
  pageRange: [number, number]; // [start, end] 1-based inclusive
  hasImage: boolean;
  imageKey: string;
}

interface ValidationIssue {
  severity: "error" | "warning";
  message: string;
}

type StudioPhase = "edit" | "validating" | "validated" | "generating" | "done";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildSections(numDays: number): SectionDef[] {
  const sections: SectionDef[] = [
    {
      id: "cover",
      label: "Cover",
      icon: <ImageIcon size={14} />,
      pageRange: [1, 1],
      hasImage: true,
      imageKey: "cover",
    },
    {
      id: "highlights",
      label: "Highlights",
      icon: <LayoutList size={14} />,
      pageRange: [2, 2],
      hasImage: true,
      imageKey: "highlights",
    },
    {
      id: "hotels",
      label: "Hotels / Stays",
      icon: <FileText size={14} />,
      pageRange: [3, 3],
      hasImage: true,
      imageKey: "hotels",
    },
  ];

  for (let d = 1; d <= numDays; d++) {
    sections.push({
      id: `day-${d}`,
      label: `Day ${d}`,
      icon: <span style={{ fontSize: 12, fontWeight: 700 }}>D{d}</span>,
      pageRange: [3 + d, 3 + d],
      hasImage: true,
      imageKey: `day_${d}`,
    });
  }

  sections.push(
    {
      id: "pricing",
      label: "Pricing",
      icon: <span style={{ fontSize: 12 }}>₹</span>,
      pageRange: [3 + numDays + 1, 3 + numDays + 1],
      hasImage: false,
      imageKey: "",
    },
    {
      id: "terms",
      label: "Terms",
      icon: <FileText size={14} />,
      pageRange: [3 + numDays + 2, 3 + numDays + 2],
      hasImage: false,
      imageKey: "",
    }
  );

  return sections;
}

function getThumbnailForSection(
  section: SectionDef,
  images: Record<string, string>,
  destination: string
): string {
  if (!section.hasImage) return "";
  if (images[section.imageKey]) return images[section.imageKey];
  const destImgs = getDestinationImages(destination);
  const idx = Math.abs(section.id.charCodeAt(0) + section.id.length) % destImgs.length;
  return destImgs[idx]?.url || destImgs[0]?.url || "";
}

// ─── A4 Preview ───────────────────────────────────────────────────────────────

interface A4PreviewProps {
  section: SectionDef;
  formData: Partial<TripRequestType>;
  itineraryText: string;
  images: Record<string, string>;
  destination: string;
  onChangeImage: (section: SectionDef) => void;
}

function A4Preview({ section, formData, itineraryText, images, destination, onChangeImage }: A4PreviewProps) {
  const imgUrl = getThumbnailForSection(section, images, destination);

  const destDisplay = formData.destination || "Unknown Destination";
  const customerName = formData.customer_name || "Valued Guest";
  const nights = formData.number_of_nights || 0;
  const days = formData.number_of_days || 0;
  const packageType = formData.budget_category || "Standard";
  const arrDate = formData.arrival_date || "";
  const depDate = formData.departure_date || "";

  let parsedDays: any[] = [];
  try {
    const parsed = JSON.parse(itineraryText);
    if (parsed?.days) parsedDays = parsed.days;
  } catch { /* markdown fallback */ }

  const renderCover = () => (
    <div className="ps-a4-cover">
      {imgUrl && (
        <div className="ps-a4-cover-img-wrap">
          <img src={imgUrl} alt="Cover" className="ps-a4-cover-img" />
          <div className="ps-a4-cover-overlay" />
        </div>
      )}
      <div className="ps-a4-cover-brand">
        <div className="ps-a4-brand-name">DARUN TOURISM</div>
        <div className="ps-a4-brand-sub">LUXURY TRAVEL</div>
      </div>
      <div className="ps-a4-cover-content">
        <h1 className="ps-a4-dest-title">{destDisplay}</h1>
        <p className="ps-a4-dest-subtitle">LUXURY {destDisplay.toUpperCase()} TRAVEL PROPOSAL</p>
        <div className="ps-a4-divider" />
        <div className="ps-a4-cover-meta">
          <div>
            <div className="ps-a4-meta-label">PREPARED FOR</div>
            <div className="ps-a4-meta-value">MR. {customerName.toUpperCase()}</div>
          </div>
          <div>
            <div className="ps-a4-meta-label">DESTINATION</div>
            <div className="ps-a4-meta-value">{destDisplay}</div>
          </div>
          <div>
            <div className="ps-a4-meta-label">DURATION</div>
            <div className="ps-a4-meta-value">{nights} Nights / {days} Days</div>
          </div>
          <div>
            <div className="ps-a4-meta-label">PACKAGE TYPE</div>
            <div className="ps-a4-meta-value">{packageType}</div>
          </div>
        </div>
      </div>
      <div className="ps-a4-footer">
        <span>Darun Tourism</span>
        <span>|</span>
        <span>{destDisplay} Specialist</span>
        <span>|</span>
        <span>Luxury Travel Specialists</span>
        <span className="ps-a4-page-num">Page 1</span>
      </div>
    </div>
  );

  const renderHighlights = () => (
    <div className="ps-a4-page">
      {imgUrl && (
        <div className="ps-a4-section-hero">
          <img src={imgUrl} alt="Highlights" className="ps-a4-section-hero-img" />
          <div className="ps-a4-section-hero-overlay" />
          <div className="ps-a4-section-hero-label">TRIP HIGHLIGHTS</div>
        </div>
      )}
      <div className="ps-a4-page-body">
        <h2 className="ps-a4-section-title">Why This Trip Is Special</h2>
        <div className="ps-a4-highlights-grid">
          {[
            { icon: "🏨", title: "Luxury Stays", value: `${nights} Nights Premium Hotels` },
            { icon: "🌴", title: "Destination", value: destDisplay },
            { icon: "📅", title: "Travel Dates", value: `${arrDate || "—"} to ${depDate || "—"}` },
            { icon: "👥", title: "Group Size", value: `${formData.number_of_adults || 2} Adults` },
            { icon: "🚗", title: "Transfer", value: formData.transfer_type || "Private Transfer" },
            { icon: "🍽️", title: "Meal Plan", value: formData.meal_plan || "As per itinerary" },
          ].map((h) => (
            <div key={h.title} className="ps-a4-highlight-card">
              <span className="ps-a4-highlight-icon">{h.icon}</span>
              <div>
                <div className="ps-a4-highlight-title">{h.title}</div>
                <div className="ps-a4-highlight-value">{h.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="ps-a4-footer">
        <span>Darun Tourism</span>
        <span>|</span>
        <span>{destDisplay} Specialist</span>
        <span className="ps-a4-page-num">Page 2</span>
      </div>
    </div>
  );

  const renderHotels = () => {
    const selectedHotels: string[] = formData.selected_hotels || [];
    return (
      <div className="ps-a4-page">
        {imgUrl && (
          <div className="ps-a4-section-hero">
            <img src={imgUrl} alt="Hotels" className="ps-a4-section-hero-img" />
            <div className="ps-a4-section-hero-overlay" />
            <div className="ps-a4-section-hero-label">HOTELS & STAYS</div>
          </div>
        )}
        <div className="ps-a4-page-body">
          <h2 className="ps-a4-section-title">Your Luxury Accommodations</h2>
          <div className="ps-a4-hotels-list">
            {selectedHotels.length > 0 ? (
              selectedHotels.map((hotel, i) => (
                <div key={i} className="ps-a4-hotel-item">
                  <div className="ps-a4-hotel-icon">🏨</div>
                  <div>
                    <div className="ps-a4-hotel-name">{hotel}</div>
                    <div className="ps-a4-hotel-meta">{formData.hotel_category_preference || "Premium"} Category</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="ps-a4-hotel-item">
                <div className="ps-a4-hotel-icon">🏨</div>
                <div>
                  <div className="ps-a4-hotel-name">Premium Hotels — {destDisplay}</div>
                  <div className="ps-a4-hotel-meta">{formData.hotel_category_preference || "Luxury"} Category</div>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="ps-a4-footer">
          <span>Darun Tourism</span>
          <span>|</span>
          <span>{destDisplay} Specialist</span>
          <span className="ps-a4-page-num">Page 3</span>
        </div>
      </div>
    );
  };

  const renderDay = (dayNum: number) => {
    const dayData = parsedDays.find((d: any) => d.day_number === dayNum) || parsedDays[dayNum - 1];
    const title = dayData?.title || `Day ${dayNum} — ${destDisplay}`;
    const story = dayData?.visiting_places || dayData?.curated_experience || dayData?.todays_journey || "Explore the wonders of " + destDisplay;
    const hotel = dayData?.hotel || "";
    return (
      <div className="ps-a4-page">
        {imgUrl && (
          <div className="ps-a4-section-hero">
            <img src={imgUrl} alt={`Day ${dayNum}`} className="ps-a4-section-hero-img" />
            <div className="ps-a4-section-hero-overlay" />
            <div className="ps-a4-section-hero-label">DAY {dayNum}</div>
          </div>
        )}
        <div className="ps-a4-page-body">
          <div className="ps-a4-day-badge">Day {dayNum}</div>
          <h2 className="ps-a4-section-title">{title}</h2>
          <p className="ps-a4-day-story">{story}</p>
          {hotel && (
            <div className="ps-a4-hotel-item" style={{ marginTop: 12 }}>
              <div className="ps-a4-hotel-icon">🏨</div>
              <div>
                <div className="ps-a4-hotel-name">{hotel}</div>
                <div className="ps-a4-hotel-meta">Overnight stay</div>
              </div>
            </div>
          )}
        </div>
        <div className="ps-a4-footer">
          <span>Darun Tourism</span>
          <span>|</span>
          <span>{destDisplay} Specialist</span>
          <span className="ps-a4-page-num">Page {3 + dayNum}</span>
        </div>
      </div>
    );
  };

  const renderPricing = () => {
    const perPerson = Number(formData.per_person_cost || 0);
    const adults = Number(formData.number_of_adults || 2);
    const flightCost = Number(formData.flight_per_person_rate || 0) * adults;
    const packageCost = perPerson * adults;
    const total = Number(formData.total_package_cost || packageCost);
    return (
      <div className="ps-a4-page">
        <div className="ps-a4-page-body">
          <h2 className="ps-a4-section-title">Package Pricing</h2>
          <div className="ps-a4-pricing-table">
            <div className="ps-a4-pricing-row ps-a4-pricing-header">
              <span>Description</span><span>Amount</span>
            </div>
            <div className="ps-a4-pricing-row">
              <span>Accommodation ({nights} nights)</span>
              <span>₹{(packageCost * 0.6).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
            </div>
            <div className="ps-a4-pricing-row">
              <span>Transfers & Sightseeing</span>
              <span>₹{(packageCost * 0.25).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
            </div>
            <div className="ps-a4-pricing-row">
              <span>Meals ({formData.meal_plan || "As specified"})</span>
              <span>₹{(packageCost * 0.15).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
            </div>
            {flightCost > 0 && (
              <div className="ps-a4-pricing-row">
                <span>Airfare ({adults} pax)</span>
                <span>₹{flightCost.toLocaleString("en-IN")}</span>
              </div>
            )}
            <div className="ps-a4-pricing-row ps-a4-pricing-total">
              <span>Grand Total</span>
              <span>₹{total > 0 ? total.toLocaleString("en-IN") : packageCost.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
            </div>
          </div>
        </div>
        <div className="ps-a4-footer">
          <span>Darun Tourism</span>
          <span>|</span>
          <span>{destDisplay} Specialist</span>
          <span className="ps-a4-page-num">Page {3 + days + 1}</span>
        </div>
      </div>
    );
  };

  const renderTerms = () => (
    <div className="ps-a4-page">
      <div className="ps-a4-page-body">
        <h2 className="ps-a4-section-title">Terms & Conditions</h2>
        <div className="ps-a4-terms-list">
          {[
            { heading: "Booking Confirmation", text: "30% advance payment required to confirm the booking. Balance 70% to be paid 30 days before travel." },
            { heading: "Cancellation Policy", text: "More than 45 days: 10% cancellation charge. 30–45 days: 25% charge. 15–30 days: 50% charge. Less than 15 days: No refund." },
            { heading: "Inclusions", text: "All inclusions as mentioned in the detailed itinerary. Darun Tourism is not responsible for services not listed herein." },
            { heading: "Force Majeure", text: "Darun Tourism is not liable for delays or cancellations caused by natural disasters, strikes, or government restrictions." },
          ].map((t) => (
            <div key={t.heading} className="ps-a4-term-item">
              <div className="ps-a4-term-heading">{t.heading}</div>
              <div className="ps-a4-term-text">{t.text}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="ps-a4-footer">
        <span>Darun Tourism</span>
        <span>|</span>
        <span>Luxury Travel Specialists</span>
        <span className="ps-a4-page-num">Page {3 + days + 2}</span>
      </div>
    </div>
  );

  const id = section.id;
  if (id === "cover") return renderCover();
  if (id === "highlights") return renderHighlights();
  if (id === "hotels") return renderHotels();
  if (id.startsWith("day-")) {
    const dayNum = parseInt(id.replace("day-", ""), 10);
    return renderDay(dayNum);
  }
  if (id === "pricing") return renderPricing();
  if (id === "terms") return renderTerms();
  return <div className="ps-a4-page"><div className="ps-a4-page-body"><p>Preview not available.</p></div></div>;
}

// ─── Main ProposalStudio ──────────────────────────────────────────────────────

interface ProposalStudioProps {
  onExit: () => void;
}

export default function ProposalStudio({ onExit }: ProposalStudioProps) {
  const { formData, generatedItinerary } = useWizardStore();

  const destination = formData.destination || "Andaman Islands";
  const numDays = Number(formData.number_of_days || 4);

  const sections = useMemo(() => buildSections(numDays), [numDays]);
  const totalPages = sections.length;

  const [activeSectionIdx, setActiveSectionIdx] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [images, setImages] = useState<Record<string, string>>({});
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelSection, setPanelSection] = useState<SectionDef | null>(null);
  const [phase, setPhase] = useState<StudioPhase>("edit");
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);

  const activeSection = sections[activeSectionIdx];
  const currentPage = activeSectionIdx + 1;

  const handleSectionClick = (idx: number) => {
    setActiveSectionIdx(idx);
    setPanelOpen(false);
  };

  const handleChangeImage = (section: SectionDef) => {
    setPanelSection(section);
    setPanelOpen(true);
  };

  const handleApplyImage = (url: string) => {
    if (!panelSection) return;
    setImages((prev) => ({ ...prev, [panelSection.imageKey]: url }));
    setPanelOpen(false);
  };

  const handleValidate = () => {
    setPhase("validating");
    setTimeout(() => {
      const issues: ValidationIssue[] = [];
      if (!formData.customer_name) issues.push({ severity: "warning", message: "Customer name not set" });
      if (!formData.arrival_date) issues.push({ severity: "warning", message: "Arrival date not set" });
      if (numDays < 1) issues.push({ severity: "error", message: "Number of days must be at least 1" });
      setValidationIssues(issues);
      setPhase("validated");
    }, 1200);
  };

  const handleGeneratePDF = async () => {
    setPhase("generating");
    try {
      const blob = await generatePDF({
        request: formData as TripRequestType,
        itinerary_text: generatedItinerary || "",
      });
      const url = window.URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Darun_${destination.replace(/\s+/g, "_")}_Proposal.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      setPhase("done");
    } catch (err: any) {
      alert(err?.message || "Failed to generate PDF. Ensure the backend is running.");
      setPhase("validated");
    }
  };

  const errCount = validationIssues.filter((i) => i.severity === "error").length;
  const canGeneratePDF = phase === "validated" && errCount === 0;
  const isValidating = phase === "validating";
  const isGenerating = (phase as string) === "generating";
  const isDone = (phase as string) === "done";

  return (
    <div className="ps-root">
      {/* ── Top Progress Bar ── */}
      <div className="ps-topbar">
        <div className="ps-steps-bar">
          {[
            { label: "Generate itinerary", icon: "ti-file-text", done: true, active: false },
            { label: "STEP 6 — PROPOSAL STUDIO", icon: "ti-layout", done: false, active: true },
            { label: "Validate", icon: "ti-circle-check", done: phase === "validated" || phase === "done", active: phase === "validating" },
            { label: "Generate Official PDF", icon: "ti-file-export", done: phase === "done", active: phase === "generating" },
          ].map((s, i) => (
            <React.Fragment key={i}>
              <div className={`ps-step ${s.active ? "ps-step--active" : ""} ${s.done ? "ps-step--done" : ""}`}>
                <i className={`ti ${s.icon} ps-step-icon`} />
                <div className="ps-step-label">{s.label}</div>
              </div>
              {i < 3 && <div className="ps-step-arrow">→</div>}
            </React.Fragment>
          ))}
        </div>
        <button className="ps-exit-btn" onClick={onExit} title="Back to itinerary preview">
          <Edit2 size={14} /> Back to Preview
        </button>
      </div>

      {/* ── Three-Column Layout ── */}
      <div className="ps-body">
        {/* LEFT: Proposal Structure */}
        <div className="ps-sidebar">
          <div className="ps-sidebar-heading">Proposal Structure</div>
          <div className="ps-sidebar-list">
            {sections.map((sec, idx) => {
              const thumb = getThumbnailForSection(sec, images, destination);
              return (
                <button
                  key={sec.id}
                  className={`ps-sidebar-item ${activeSectionIdx === idx ? "active" : ""}`}
                  onClick={() => handleSectionClick(idx)}
                >
                  <div className="ps-sidebar-thumb">
                    {thumb ? (
                      <img src={thumb} alt={sec.label} className="ps-sidebar-thumb-img" />
                    ) : (
                      <div className="ps-sidebar-thumb-placeholder">
                        {sec.icon}
                      </div>
                    )}
                  </div>
                  <span className="ps-sidebar-label">{sec.label}</span>
                  <ChevronRight size={14} className="ps-sidebar-arrow" />
                </button>
              );
            })}
          </div>
        </div>

        {/* CENTER: A4 Preview */}
        <div className="ps-preview-area">
          {/* Preview toolbar */}
          <div className="ps-preview-toolbar">
            <span className="ps-preview-title">Live A4 Proposal Preview</span>
            <div className="ps-preview-nav">
              <button
                className="ps-nav-btn"
                disabled={activeSectionIdx === 0}
                onClick={() => setActiveSectionIdx((p) => Math.max(0, p - 1))}
              >
                <ChevronLeft size={16} />
              </button>
              <span className="ps-page-indicator">{currentPage} / {totalPages}</span>
              <button
                className="ps-nav-btn"
                disabled={activeSectionIdx === sections.length - 1}
                onClick={() => setActiveSectionIdx((p) => Math.min(sections.length - 1, p + 1))}
              >
                <ChevronRight size={16} />
              </button>
            </div>
            <div className="ps-zoom-controls">
              <button className="ps-nav-btn" onClick={() => setZoom((z) => Math.max(60, z - 10))}>
                <ZoomOut size={14} />
              </button>
              <span className="ps-zoom-label">{zoom}%</span>
              <button className="ps-nav-btn" onClick={() => setZoom((z) => Math.min(150, z + 10))}>
                <ZoomIn size={14} />
              </button>
            </div>
            <button className="ps-nav-btn" title="Fullscreen preview (coming soon)">
              <Maximize2 size={14} />
            </button>
          </div>

          {/* A4 Canvas */}
          <div className="ps-a4-canvas-wrap">
            <div
              className="ps-a4-canvas"
              style={{ transform: `scale(${zoom / 100})`, transformOrigin: "top center" }}
            >
              {/* Change Image button overlay for sections with images */}
              {activeSection.hasImage && (
                <button
                  className="ps-change-img-btn"
                  onClick={() => handleChangeImage(activeSection)}
                >
                  <ImageIcon size={14} /> Change Image
                </button>
              )}
              <A4Preview
                section={activeSection}
                formData={formData}
                itineraryText={generatedItinerary || ""}
                images={images}
                destination={destination}
                onChangeImage={handleChangeImage}
              />
            </div>
          </div>
        </div>

        {/* RIGHT: Image Changer Panel (shown when panelOpen) */}
        {panelOpen && panelSection && (
          <div className="ps-right-panel">
            <ImageChangerPanel
              sectionLabel={panelSection.label}
              destination={destination}
              currentImage={images[panelSection.imageKey] || ""}
              onApply={handleApplyImage}
              onClose={() => setPanelOpen(false)}
            />
          </div>
        )}
      </div>

      {/* ── Bottom Action Bar ── */}
      <div className="ps-action-bar">
        <div className="ps-action-hint">
          <span className="ps-hint-icon">💡</span>
          <span>
            Click any section thumbnail on the left or the <strong>Change Image</strong> button on the preview to swap photos.
            Works for Cover, Highlights, Hotels, and every Day.
          </span>
        </div>

        <div className="ps-action-buttons">
          {/* Validation result */}
          {phase === "validated" && (
            <div className={`ps-validation-badge ${validationIssues.filter(i=>i.severity==="error").length > 0 ? "error" : "ok"}`}>
              {validationIssues.filter(i=>i.severity==="error").length > 0 ? (
                <><AlertTriangle size={14} /> {validationIssues.length} issue(s)</>
              ) : (
                <><CheckCircle2 size={14} /> Validation passed</>
              )}
            </div>
          )}

          <button
            className="ps-btn-validate"
            onClick={handleValidate}
            disabled={isValidating || isGenerating}
          >
            {isValidating ? (
              <><Loader2 size={14} className="ps-spin" /> Validating...</>
            ) : (
              <><CheckCircle2 size={14} /> Validate</>
            )}
          </button>

          <button
            className="ps-btn-pdf"
            onClick={handleGeneratePDF}
            disabled={!canGeneratePDF || isGenerating}
          >
            {isGenerating ? (
              <><Loader2 size={14} className="ps-spin" /> Generating...</>
            ) : isDone ? (
              <><CheckCircle2 size={14} /> PDF Downloaded!</>
            ) : (
              <><FileText size={14} /> Generate Official PDF</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
