/**
 * Velqairn Canonical Proposal Document TypeScript Types
 * ====================================================
 * Authoritative client-side interface mirroring apps/api/app/schemas/proposal.py
 * Ensures 100% Pydantic/TypeScript contract parity.
 */

// ─────────────────────────────────────────────────────────────────────────────
// 1. ENUMS & CLASSIFICATIONS
// ─────────────────────────────────────────────────────────────────────────────

export type ContentClassification = "system_locked" | "data_derived" | "user_editable";

export type ChangeState =
  | "clean"
  | "locally_modified"
  | "dependency_modified"
  | "stale"
  | "validation_failed";

export type SourceType =
  | "ai_generated"
  | "catalog_default"
  | "verified_catalog"
  | "user_override"
  | "system_generated";

export type ImageSourceType =
  | "destination_catalog"
  | "hotel_catalog"
  | "activity_catalog"
  | "attraction_catalog"
  | "user_upload"
  | "generated_visual"
  | "external_reference";

export type ImageVerificationStatus =
  | "verified"
  | "unverified"
  | "manually_approved"
  | "rejected";

export type SectionType =
  | "cover"
  | "trip_highlights"
  | "luxury_stays"
  | "itinerary_day"
  | "invoice"
  | "payment_details"
  | "inclusions_exclusions"
  | "cancellation"
  | "payment_agreement"
  | "terms_conditions"
  | "custom_note"
  | "custom_gallery";

export type ValidationSeverity = "info" | "warning" | "error" | "critical";

// ─────────────────────────────────────────────────────────────────────────────
// 2. PROVENANCE & VALUES
// ─────────────────────────────────────────────────────────────────────────────

export interface ProposalValue<T = any> {
  value: T;
  source_type: SourceType;
  source_ref?: string | null;
  original_value?: T | null;
  override_value?: T | null;
  is_overridden: boolean;
  last_modified_by?: string | null;
  last_modified_at: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. SEMANTIC IMAGE ASSETS & SLOTS
// ─────────────────────────────────────────────────────────────────────────────

export interface ImageCrop {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ImageFocalPoint {
  x: number;
  y: number;
}

export interface ImageAsset {
  image_id: string;
  source_type: ImageSourceType;
  verification_status: ImageVerificationStatus;
  destination_id: string;
  entity_type?: string | null;
  entity_id?: string | null;
  path_or_url: string;
  alt_text: string;
  caption: string;
  crop: ImageCrop;
  focal_point: ImageFocalPoint;
  fit_mode: "cover" | "contain" | "fill";
}

export interface SemanticImageSlot {
  slot_id: string;
  label: string;
  asset?: ImageAsset | null;
  fallback_policy: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. DEPENDENCY GRAPH
// ─────────────────────────────────────────────────────────────────────────────

export interface DependencyNode {
  node_id: string;
  depends_on: string[];
  invalidates: string[];
}

export interface DependencyGraph {
  nodes: Record<string, DependencyNode>;
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. STRUCTURED PRICING
// ─────────────────────────────────────────────────────────────────────────────

export interface PricingLineItem {
  item_id: string;
  category: "accommodation" | "transfers" | "activities" | "taxes" | "supplement" | string;
  description: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  is_taxable: boolean;
}

export interface StructuredPricing {
  currency: string;
  line_items: PricingLineItem[];
  pure_package_cost: number;
  airfare_sum: number;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  grand_total: number;
  pricing_note?: string | null;
  is_per_person_mode: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. SECTION CONTENT MODELS
// ─────────────────────────────────────────────────────────────────────────────

export interface CoverContent {
  proposal_title: ProposalValue<string>;
  proposal_subtitle: ProposalValue<string>;
  destination_display: string;
  duration_text: string;
  customer_name: string;
  package_type: string;
}

export interface HighlightCard {
  card_id: string;
  title: string;
  value: ProposalValue<string>;
  description: ProposalValue<string>;
}

export interface HighlightsContent {
  headline: string;
  subheadline: string;
  cards: HighlightCard[];
}

export interface HotelStayItem {
  hotel_id: string;
  hotel_name: ProposalValue<string>;
  location: ProposalValue<string>;
  star_category: ProposalValue<string>;
  room_type: ProposalValue<string>;
  nights: number;
  description: ProposalValue<string>;
  image_slot?: SemanticImageSlot | null;
}

export interface LuxuryStaysContent {
  headline: string;
  subheadline: string;
  stays: HotelStayItem[];
}

export interface DayScheduleBullet {
  bullet_id: string;
  text: ProposalValue<string>;
  is_subitem: boolean;
}

export interface ItineraryDayContent {
  day_number: number;
  date_str: string;
  location_title: string;
  title: ProposalValue<string>;
  subtitle: ProposalValue<string>;
  hero_image?: SemanticImageSlot | null;
  gallery_images: SemanticImageSlot[];
  visiting_places_story: ProposalValue<string>;
  todays_journey: ProposalValue<string>;
  schedule_bullets: DayScheduleBullet[];
  hotel_experience: ProposalValue<string>;
  is_departure_day: boolean;
  departure_narrative?: ProposalValue<string> | null;
  farewell_narrative?: ProposalValue<string> | null;
  attractions: string[];
  activities: string[];
}

export interface InvoiceContent {
  invoice_number: string;
  invoice_date: string;
  duration_text: string;
  trip_type: string;
  client_name: string;
  client_email: string;
  client_phone: string;
  client_nationality: string;
  pax_summary: string;
  pricing: StructuredPricing;
}

export interface BankAccountDetails {
  account_name: string;
  bank_name: string;
  account_number: string;
  ifsc: string;
  branch: string;
  qr_image_url?: string | null;
  proprietor: string;
  phone_numbers: string[];
}

export interface PaymentDetailsContent {
  headline: string;
  subheadline: string;
  bank_details: BankAccountDetails;
}

export interface InclusionsExclusionsContent {
  headline: string;
  subheadline: string;
  inclusions: ProposalValue<string>[];
  exclusions: ProposalValue<string>[];
}

export interface PolicyClause {
  clause_id: string;
  heading: string;
  text: ProposalValue<string>;
  bullets: ProposalValue<string>[];
}

export interface PolicyAgreementContent {
  agreement_title: string;
  effective_date: string;
  agency_legal_name: string;
  agency_location: string;
  client_name: string;
  client_address: string;
  preamble: string;
  clauses: PolicyClause[];
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. PROPOSAL SECTION & PAGINATION
// ─────────────────────────────────────────────────────────────────────────────

export interface ProposalSection<T = any> {
  id: string;
  type: SectionType;
  title: string;
  display_title: string;
  classification: ContentClassification;
  change_state: ChangeState;
  enabled: boolean;
  order: number;
  content: T;
  images: SemanticImageSlot[];
  dependencies: string[];
  estimated_pages: number;
}

export interface LayoutBlock {
  block_id: string;
  section_id: string;
  block_type: string;
  estimated_height_pt: number;
  can_split: boolean;
}

export interface PhysicalPage {
  page_index: number;
  section_ids: string[];
  blocks: LayoutBlock[];
  estimated_height_pt: number;
  is_full_page_break: boolean;
}

export interface PagePlan {
  pages: PhysicalPage[];
  total_pages: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// 8. VALIDATION
// ─────────────────────────────────────────────────────────────────────────────

export interface ProposalValidationIssue {
  code: string;
  severity: ValidationSeverity;
  section_id?: string | null;
  field_name?: string | null;
  message: string;
  remediation_hint?: string | null;
}

export interface ProposalValidationReport {
  is_valid: boolean;
  can_render_pdf: boolean;
  last_validated_at: string;
  issues: ProposalValidationIssue[];
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. ROOT PROPOSAL DOCUMENT
// ─────────────────────────────────────────────────────────────────────────────

export interface AgencyContextData {
  brand_name: string;
  legal_name: string;
  location: string;
  email: string;
  website: string;
  phone_numbers: string[];
  bank_account_name: string;
  bank_name: string;
  account_number: string;
  ifsc: string;
  branch: string;
  proprietor: string;
}

export interface DestinationContextData {
  destination_id: string;
  display_name: string;
  is_andaman: boolean;
  has_verified_ferry_movement: boolean;
  entry_hub?: string | null;
  capabilities: Record<string, any>;
}

export interface ProposalDocument {
  id: string;
  version: string;
  revision: number;
  created_at: string;
  updated_at: string;
  trip_id?: string | null;
  destination_id: string;
  destination_context: DestinationContextData;
  agency_context: AgencyContextData;
  day_wise_style: string;
  customer: Record<string, any>;
  duration: Record<string, any>;
  sections: ProposalSection[];
  dependency_graph: DependencyGraph;
  pricing: StructuredPricing;
  page_plan: PagePlan;
  validation: ProposalValidationReport;
}
