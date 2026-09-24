"""
Velqairn Canonical Proposal Document Schema
===========================================
Defines the authoritative intermediate representation (IR) between TripRequest/AI
and the PDF/Preview renderers.

Architectural Guarantees:
- Strict separation of AgencyContext from DestinationContext.
- Decoupling of Logical Sections from Physical PDF Pages (Pagination Abstraction).
- Provenance tracking (ProposalValue with source_type, source_ref, override_value).
- Explicit Content Classification (SYSTEM_LOCKED, DATA_DERIVED, USER_EDITABLE).
- Granular Change State (clean, locally_modified, dependency_modified, stale, validation_failed).
- Semantic Image Assets with verification status and destination boundary invariant.
- Computed Structured Pricing (never freeform typing).
- Dependency Graph for incremental invalidation.
"""
from datetime import datetime, date, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# 1. ENUMS & CLASSIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ContentClassification(str, Enum):
    """Governs editability and protection rules for content blocks."""
    SYSTEM_LOCKED = "system_locked"   # Legal terms, statutory bank info, immutable disclaimers
    DATA_DERIVED = "data_derived"     # Catalog hotels, pricing totals, calculated logistics
    USER_EDITABLE = "user_editable"   # Narratives, titles, bullet wording, presentation notes


class ChangeState(str, Enum):
    """Tracks document revision and dependency freshness."""
    CLEAN = "clean"
    LOCALLY_MODIFIED = "locally_modified"
    DEPENDENCY_MODIFIED = "dependency_modified"
    STALE = "stale"
    VALIDATION_FAILED = "validation_failed"


class SourceType(str, Enum):
    AI_GENERATED = "ai_generated"
    CATALOG_DEFAULT = "catalog_default"
    VERIFIED_CATALOG = "verified_catalog"
    USER_OVERRIDE = "user_override"
    SYSTEM_GENERATED = "system_generated"


class ImageSourceType(str, Enum):
    DESTINATION_CATALOG = "destination_catalog"
    HOTEL_CATALOG = "hotel_catalog"
    ACTIVITY_CATALOG = "activity_catalog"
    ATTRACTION_CATALOG = "attraction_catalog"
    USER_UPLOAD = "user_upload"
    GENERATED_VISUAL = "generated_visual"
    EXTERNAL_REFERENCE = "external_reference"


class ImageVerificationStatus(str, Enum):
    VERIFIED = "verified"                     # Verified in active destination catalog
    UNVERIFIED = "unverified"                 # Uploaded/external without catalog match
    MANUALLY_APPROVED = "manually_approved"   # Explicit user override with audit record
    REJECTED = "rejected"                     # Blocked cross-destination asset


class SectionType(str, Enum):
    COVER = "cover"
    TRIP_HIGHLIGHTS = "trip_highlights"
    LUXURY_STAYS = "luxury_stays"
    ITINERARY_DAY = "itinerary_day"
    INVOICE = "invoice"
    PAYMENT_DETAILS = "payment_details"
    INCLUSIONS_EXCLUSIONS = "inclusions_exclusions"
    CANCELLATION = "cancellation"
    PAYMENT_AGREEMENT = "payment_agreement"
    TERMS_CONDITIONS = "terms_conditions"
    CUSTOM_NOTE = "custom_note"
    CUSTOM_GALLERY = "custom_gallery"


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ─────────────────────────────────────────────────────────────────────────────
# 2. PROVENANCE & VALUES
# ─────────────────────────────────────────────────────────────────────────────

class ProposalValue(BaseModel):
    """
    Every editable field supports provenance, original vs override, and audit tracking.
    Guarantees master catalog is never mutated when an employee edits a proposal.
    """
    value: Any
    source_type: SourceType = SourceType.SYSTEM_GENERATED
    source_ref: Optional[str] = None       # e.g. "HOTEL-GOA-0092" or "attraction:candolim_beach"
    original_value: Optional[Any] = None  # Original AI or catalog value
    override_value: Optional[Any] = None  # Employee override
    is_overridden: bool = False
    last_modified_by: Optional[str] = "system"
    last_modified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_source(cls, value: Any, source_type: SourceType, source_ref: Optional[str] = None) -> "ProposalValue":
        return cls(
            value=value,
            source_type=source_type,
            source_ref=source_ref,
            original_value=value,
            override_value=None,
            is_overridden=False,
        )

    def set_override(self, new_value: Any, modifier: str = "employee") -> None:
        self.override_value = new_value
        self.value = new_value
        self.is_overridden = True
        self.last_modified_by = modifier
        self.last_modified_at = datetime.now(timezone.utc).isoformat()

    def revert_to_source(self) -> None:
        self.value = self.original_value
        self.override_value = None
        self.is_overridden = False
        self.last_modified_at = datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# 3. SEMANTIC IMAGE ASSETS & SLOTS
# ─────────────────────────────────────────────────────────────────────────────

class ImageCrop(BaseModel):
    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0


class ImageFocalPoint(BaseModel):
    x: float = 0.5
    y: float = 0.5


class ImageAsset(BaseModel):
    image_id: str
    source_type: ImageSourceType
    verification_status: ImageVerificationStatus
    destination_id: str                     # Must match proposal.destination_id for catalog images
    entity_type: Optional[str] = None       # "hotel", "attraction", "destination", "generic"
    entity_id: Optional[str] = None         # e.g. "goa:candolim" or "hotel:radisson_candolim"
    path_or_url: str
    alt_text: str = ""
    caption: str = ""
    crop: ImageCrop = Field(default_factory=ImageCrop)
    focal_point: ImageFocalPoint = Field(default_factory=ImageFocalPoint)
    fit_mode: str = "cover"                 # "cover" | "contain" | "fill"


class SemanticImageSlot(BaseModel):
    """
    Semantic binding for images (e.g. 'cover.hero', 'day.3.hero', 'hotel.TAJ-01.hero').
    Never tied to a physical page number.
    """
    slot_id: str
    label: str
    asset: Optional[ImageAsset] = None
    fallback_policy: str = "generic_abstract_or_none"  # NEVER cross-destination fallback


# ─────────────────────────────────────────────────────────────────────────────
# 4. DEPENDENCY GRAPH
# ─────────────────────────────────────────────────────────────────────────────

class DependencyNode(BaseModel):
    node_id: str
    depends_on: List[str] = Field(default_factory=list)
    invalidates: List[str] = Field(default_factory=list)


class DependencyGraph(BaseModel):
    nodes: Dict[str, DependencyNode] = Field(default_factory=dict)

    def register_dependency(self, source_id: str, dependent_id: str) -> None:
        if source_id not in self.nodes:
            self.nodes[source_id] = DependencyNode(node_id=source_id)
        if dependent_id not in self.nodes:
            self.nodes[dependent_id] = DependencyNode(node_id=dependent_id)

        if dependent_id not in self.nodes[source_id].invalidates:
            self.nodes[source_id].invalidates.append(dependent_id)
        if source_id not in self.nodes[dependent_id].depends_on:
            self.nodes[dependent_id].depends_on.append(source_id)

    def get_invalidated_targets(self, node_id: str) -> List[str]:
        """Breadth-first resolution of all dependent sections to invalidate."""
        visited = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            if curr in self.nodes:
                for target in self.nodes[curr].invalidates:
                    if target not in visited:
                        visited.add(target)
                        queue.append(target)
        return list(visited)


# ─────────────────────────────────────────────────────────────────────────────
# 5. STRUCTURED PRICING MODEL
# ─────────────────────────────────────────────────────────────────────────────

class PricingLineItem(BaseModel):
    item_id: str
    category: str  # "accommodation", "transfers", "activities", "taxes", "supplement"
    description: str
    quantity: int = 1
    unit_price: float = 0.0
    subtotal: float = 0.0
    is_taxable: bool = True


class StructuredPricing(BaseModel):
    """
    Calculated financial schedule. Grand total and tax are mathematical invariants,
    never arbitrary free-typed strings.
    """
    currency: str = "INR"
    line_items: List[PricingLineItem] = Field(default_factory=list)
    pure_package_cost: float = 0.0
    airfare_sum: float = 0.0
    subtotal: float = 0.0
    tax_rate: float = 0.05
    tax_amount: float = 0.0
    grand_total: float = 0.0
    pricing_note: Optional[str] = None
    is_per_person_mode: bool = False

    def recalculate(self) -> None:
        calc_sub = sum(item.subtotal for item in self.line_items)
        if calc_sub > 0:
            self.subtotal = calc_sub
        taxable_sum = sum(item.subtotal for item in self.line_items if item.is_taxable)
        if taxable_sum > 0:
            self.tax_amount = round(taxable_sum * self.tax_rate)
        elif self.pure_package_cost > 0:
            self.tax_amount = round(self.pure_package_cost * self.tax_rate)
        else:
            self.tax_amount = 0.0
        self.grand_total = self.subtotal + self.tax_amount


# ─────────────────────────────────────────────────────────────────────────────
# 6. SECTION CONTENT MODELS
# ─────────────────────────────────────────────────────────────────────────────

class CoverContent(BaseModel):
    proposal_title: ProposalValue
    proposal_subtitle: ProposalValue
    destination_display: str
    duration_text: str
    customer_name: str
    package_type: str = "Premium Luxury"


class HighlightCard(BaseModel):
    card_id: str
    title: str
    value: ProposalValue
    description: ProposalValue


class HighlightsContent(BaseModel):
    headline: str = "TRIP HIGHLIGHTS"
    subheadline: str = "A data-driven overview of the selected guest journey."
    cards: List[HighlightCard] = Field(default_factory=list)


class HotelStayItem(BaseModel):
    hotel_id: str
    hotel_name: ProposalValue
    location: ProposalValue
    star_category: ProposalValue
    room_type: ProposalValue
    nights: int
    description: ProposalValue
    image_slot: Optional[SemanticImageSlot] = None


class LuxuryStaysContent(BaseModel):
    headline: str = "YOUR LUXURY STAYS"
    subheadline: str = "Elegant stays selected from Darun Tourism inventory."
    stays: List[HotelStayItem] = Field(default_factory=list)


class DayScheduleBullet(BaseModel):
    bullet_id: str
    text: ProposalValue
    is_subitem: bool = False


class ItineraryDayContent(BaseModel):
    day_number: int
    date_str: str = ""
    location_title: str
    title: ProposalValue
    subtitle: ProposalValue
    hero_image: Optional[SemanticImageSlot] = None
    gallery_images: List[SemanticImageSlot] = Field(default_factory=list)
    visiting_places_story: ProposalValue
    todays_journey: ProposalValue
    schedule_bullets: List[DayScheduleBullet] = Field(default_factory=list)
    hotel_experience: ProposalValue
    is_departure_day: bool = False
    departure_narrative: Optional[ProposalValue] = None
    farewell_narrative: Optional[ProposalValue] = None
    attractions: List[str] = Field(default_factory=list)
    activities: List[str] = Field(default_factory=list)


class InvoiceContent(BaseModel):
    invoice_number: str
    invoice_date: str
    duration_text: str
    trip_type: str
    client_name: str
    client_email: str
    client_phone: str
    client_nationality: str
    pax_summary: str
    pricing: StructuredPricing


class BankAccountDetails(BaseModel):
    account_name: str
    bank_name: str
    account_number: str
    ifsc: str
    branch: str
    qr_image_url: Optional[str] = None
    proprietor: str
    phone_numbers: List[str]


class PaymentDetailsContent(BaseModel):
    headline: str = "PAYMENT DETAILS"
    subheadline: str = "Secure payment information for your confirmed booking."
    bank_details: BankAccountDetails


class InclusionsExclusionsContent(BaseModel):
    headline: str = "INCLUSIONS & EXCLUSIONS"
    subheadline: str = "A concise service summary for guest review and confirmation."
    inclusions: List[ProposalValue] = Field(default_factory=list)
    exclusions: List[ProposalValue] = Field(default_factory=list)


class PolicyClause(BaseModel):
    clause_id: str
    heading: str
    text: ProposalValue
    bullets: List[ProposalValue] = Field(default_factory=list)


class PolicyAgreementContent(BaseModel):
    agreement_title: str
    effective_date: str
    agency_legal_name: str
    agency_location: str
    client_name: str
    client_address: str
    preamble: str
    clauses: List[PolicyClause] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 7. PROPOSAL SECTION & PAGINATION ABSTRACTION
# ─────────────────────────────────────────────────────────────────────────────

class ProposalSection(BaseModel):
    id: str
    type: SectionType
    title: str
    display_title: str
    classification: ContentClassification
    change_state: ChangeState = ChangeState.CLEAN
    enabled: bool = True
    order: int
    content: Any  # Polymorphic content matching SectionType
    images: List[SemanticImageSlot] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    estimated_pages: int = 1


class LayoutBlock(BaseModel):
    block_id: str
    section_id: str
    block_type: str
    estimated_height_pt: float
    can_split: bool = False


class PhysicalPage(BaseModel):
    page_index: int                       # 1-indexed physical PDF page number
    section_ids: List[str]                # Sections present on this physical page
    blocks: List[LayoutBlock]
    estimated_height_pt: float
    is_full_page_break: bool = True


class PagePlan(BaseModel):
    """Authoritative physical page plan derived from layout measurement."""
    pages: List[PhysicalPage] = Field(default_factory=list)
    total_pages: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# 8. VALIDATION SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ProposalValidationIssue(BaseModel):
    code: str
    severity: ValidationSeverity
    section_id: Optional[str] = None
    field_name: Optional[str] = None
    message: str
    remediation_hint: Optional[str] = None


class ProposalValidationReport(BaseModel):
    is_valid: bool = True
    can_render_pdf: bool = True
    last_validated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    issues: List[ProposalValidationIssue] = Field(default_factory=list)

    def add_issue(
        self,
        code: str,
        severity: ValidationSeverity,
        message: str,
        section_id: Optional[str] = None,
        field_name: Optional[str] = None,
        field: Optional[str] = None,
        hint: Optional[str] = None,
        remediation_hint: Optional[str] = None,
    ) -> None:
        self.issues.append(ProposalValidationIssue(
            code=code,
            severity=severity,
            section_id=section_id,
            field_name=field_name or field,
            message=message,
            remediation_hint=remediation_hint or hint,
        ))
        if severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.is_valid = False
            self.can_render_pdf = False


# ─────────────────────────────────────────────────────────────────────────────
# 9. ROOT PROPOSAL DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

class AgencyContextData(BaseModel):
    brand_name: str
    legal_name: str
    location: str
    email: str
    website: str
    phone_numbers: List[str]
    bank_account_name: str
    bank_name: str
    account_number: str
    ifsc: str
    branch: str
    proprietor: str


class DestinationContextData(BaseModel):
    destination_id: str
    display_name: str
    is_andaman: bool
    has_verified_ferry_movement: bool
    entry_hub: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class ProposalDocument(BaseModel):
    """
    CANONICAL SINGLE SOURCE OF TRUTH (SSOT)
    Authoritative state for Proposal Studio UI, Preflight Validation, and PDF Rendering.
    """
    id: str
    version: str = "1.0.0"
    revision: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trip_id: Optional[str] = None
    destination_id: str
    destination_context: DestinationContextData
    agency_context: AgencyContextData
    day_wise_style: str = "luxury_narrative"
    customer: Dict[str, Any]
    duration: Dict[str, Any]
    sections: List[ProposalSection] = Field(default_factory=list)
    dependency_graph: DependencyGraph = Field(default_factory=DependencyGraph)
    pricing: StructuredPricing = Field(default_factory=StructuredPricing)
    page_plan: PagePlan = Field(default_factory=PagePlan)
    validation: ProposalValidationReport = Field(default_factory=ProposalValidationReport)

    def get_section(self, section_id: str) -> Optional[ProposalSection]:
        for sec in self.sections:
            if sec.id == section_id:
                return sec
        return None

    def get_enabled_sections(self) -> List[ProposalSection]:
        return sorted([s for s in self.sections if s.enabled], key=lambda x: x.order)
