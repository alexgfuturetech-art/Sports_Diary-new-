from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}


class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


# ─── User Model ───────────────────────────────────────────────────────────────
# roles is now a LIST so users can hold multiple roles simultaneously.
# Primary role helpers: use roles[0] for display; permission checks use "in roles".
class User(MongoBaseModel):
    phone: str = Field(..., index=True)
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # Multi-role: list of role strings
    # Valid values: "player", "parent", "professional", "organizer", "admin", "super_admin"
    roles: List[str] = []
    # Kept for backwards compat / quick reads (always == roles[0] if roles else None)
    role: Optional[str] = None

    professional_type: Optional[str] = None

    # Organiser approval workflow
    organizer_status: Optional[str] = None   # "pending" | "approved" | "rejected"
    organizer_requested_at: Optional[datetime] = None
    organizer_approved_by: Optional[str] = None
    organizer_approved_at: Optional[datetime] = None
    organizer_rejection_reason: Optional[str] = None

    # Professional fee gate
    professional_status: Optional[str] = None  # "pending_payment" | "active"
    professional_fee_paid: bool = False
    professional_fee_paid_at: Optional[datetime] = None

    city: Optional[str] = None
    state: str = "Gujarat"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    bio: Optional[str] = None
    avatar: Optional[str] = None
    sports_interests: Optional[List[str]] = []
    player_position: Optional[str] = None
    playing_style: Optional[str] = None
    certification: Optional[str] = None
    experience_years: Optional[int] = None
    children_count: Optional[int] = None
    tournaments_organized: int = 0

    is_active: bool = True
    is_verified: bool = False
    onboarding_completed: bool = False


class SportsStats(MongoBaseModel):
    user_id: str = Field(..., index=True)
    sport_type: str
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    detailed_stats: Optional[dict] = {}
    rating: float = 0.0
    achievements: Optional[List[dict]] = []


class Venue(MongoBaseModel):
    owner_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    venue_type: Optional[str] = None
    sports_available: Optional[List[str]] = []
    amenities: Optional[List[str]] = []
    city: str = Field(..., index=True)
    state: str = "Gujarat"
    address: Optional[str] = None
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_hour: float
    weekend_price: Optional[float] = None
    peak_hour_price: Optional[float] = None
    currency: str = "INR"
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    operating_days: Optional[List[str]] = []
    capacity: Optional[int] = None
    surface_type: Optional[str] = None
    indoor_outdoor: Optional[str] = None
    images: Optional[List[str]] = []
    contact_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    rating: float = 0.0
    total_reviews: int = 0
    total_bookings: int = 0
    is_verified: bool = False
    is_featured: bool = False
    is_active: bool = True


class Booking(MongoBaseModel):
    booking_number: str = Field(..., index=True)
    user_id: str
    venue_id: str
    sport_type: Optional[str] = None
    booking_date: str
    start_time: str
    end_time: str
    duration_hours: Optional[float] = None
    player_count: Optional[int] = None
    team_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    base_price: float
    additional_charges: Optional[List[dict]] = []
    discount_amount: float = 0.0
    total_amount: float
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    paid_amount: float = 0.0
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None
    is_split_payment: bool = False
    split_payment_data: Optional[List[dict]] = []
    split_payment_link: Optional[str] = None
    status: str = "confirmed"
    booking_source: str = "app"
    special_requests: Optional[str] = None
    admin_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None


class VenueReview(MongoBaseModel):
    venue_id: str
    user_id: str
    booking_id: Optional[str] = None
    rating: int
    review_text: Optional[str] = None
    images: Optional[List[str]] = []
    cleanliness_rating: Optional[int] = None
    facilities_rating: Optional[int] = None
    staff_rating: Optional[int] = None
    value_rating: Optional[int] = None
    is_verified: bool = False
    helpful_count: int = 0


class VenueSlot(MongoBaseModel):
    venue_id: str
    date: str
    start_time: str
    end_time: str
    is_available: bool = True
    booking_id: Optional[str] = None
    price: Optional[float] = None
    blocked_reason: Optional[str] = None


class Shop(MongoBaseModel):
    owner_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    shop_type: Optional[str] = None
    category: Optional[str] = None
    products: Optional[List[dict]] = []
    specialization: Optional[List[str]] = []
    brands_available: Optional[List[str]] = []
    city: str = Field(..., index=True)
    state: str = "Gujarat"
    address: Optional[str] = None
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_number: str
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    established_year: Optional[int] = None
    gst_number: Optional[str] = None
    license_number: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    operating_days: Optional[List[str]] = []
    logo: Optional[str] = None
    images: Optional[List[str]] = []
    catalogue_pdf: Optional[str] = None
    rating: float = 0.0
    total_reviews: int = 0
    total_enquiries: int = 0
    home_delivery: bool = False
    online_payment: bool = False
    bulk_orders: bool = False
    custom_manufacturing: bool = False
    is_featured: bool = False
    is_verified: bool = False
    is_active: bool = True


class Job(MongoBaseModel):
    posted_by: str
    title: str
    job_type: str
    description: str
    sport_type: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    certification_required: Optional[List[str]] = []
    city: str = Field(..., index=True)
    state: str = "Gujarat"
    location_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_type: Optional[str] = None
    currency: str = "INR"
    other_benefits: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
    language_required: Optional[List[str]] = []
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    application_deadline: Optional[datetime] = None
    how_to_apply: Optional[str] = None
    application_email: Optional[str] = None
    application_phone: Optional[str] = None
    application_url: Optional[str] = None
    banner_image: Optional[str] = None
    views_count: int = 0
    applications_count: int = 0
    status: str = "active"
    is_featured: bool = False
    is_verified: bool = False
    expires_at: Optional[datetime] = None


# ─── Job Application Model (new) ──────────────────────────────────────────────
class JobApplication(MongoBaseModel):
    job_id: str = Field(..., index=True)
    applicant_id: str = Field(..., index=True)   # professional user id
    applicant_name: str
    applicant_phone: str
    applicant_professional_type: Optional[str] = None
    cover_letter: Optional[str] = None
    experience_years: Optional[int] = None
    certification: Optional[str] = None
    expected_salary: Optional[float] = None
    available_from: Optional[datetime] = None
    status: str = "applied"          # applied | shortlisted | selected | rejected
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    organizer_notes: Optional[str] = None


class Dictionary(MongoBaseModel):
    term: str
    sport: str
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    definition: str
    explanation: Optional[str] = None
    examples: Optional[List[str]] = []
    images: Optional[List[str]] = []
    video_url: Optional[str] = None
    diagram_url: Optional[str] = None
    related_terms: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    gujarati_term: Optional[str] = None
    hindi_term: Optional[str] = None
    views_count: int = 0
    helpful_count: int = 0
    slug: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True


class Tournament(MongoBaseModel):
    organizer_id: str
    name: str
    description: Optional[str] = None
    sport_type: str
    tournament_type: Optional[str] = None
    format: Optional[str] = None
    team_size: Optional[int] = None
    max_teams: int
    min_teams: Optional[int] = None
    current_teams: int = 0
    age_category: Optional[str] = None
    gender_category: Optional[str] = None
    skill_level: Optional[str] = None
    city: str = Field(..., index=True)
    state: str = "Gujarat"
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    venue_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    registration_start: Optional[datetime] = None
    registration_deadline: datetime
    entry_fee: float = 0
    currency: str = "INR"
    prize_pool: Optional[float] = None
    prize_distribution: Optional[List[dict]] = []
    documents_required: Optional[List[str]] = []
    team_composition_rules: Optional[dict] = {}
    rules: Optional[str] = None
    match_rules: Optional[dict] = {}
    ball_type: Optional[str] = None
    banner_image: Optional[str] = None
    logo: Optional[str] = None
    images: Optional[List[str]] = []
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    live_scoring: bool = False
    live_streaming: bool = False
    certificates_provided: bool = False
    views_count: int = 0
    status: str = "upcoming"
    is_featured: bool = False
    is_verified: bool = False
    is_active: bool = True


# ─── Match / Fixture Model (new) ──────────────────────────────────────────────
class Match(MongoBaseModel):
    tournament_id: str = Field(..., index=True)
    round_number: int = 1
    match_number: int
    stage: Optional[str] = None     # e.g. "Group Stage", "Quarter Final", "Semi Final", "Final"
    team1_id: Optional[str] = None
    team1_name: Optional[str] = None
    team2_id: Optional[str] = None
    team2_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[str] = None
    venue: Optional[str] = None
    # Result
    winner_id: Optional[str] = None
    team1_score: Optional[str] = None
    team2_score: Optional[str] = None
    result_summary: Optional[str] = None
    status: str = "scheduled"       # scheduled | ongoing | completed | cancelled
    completed_at: Optional[datetime] = None
    recorded_by: Optional[str] = None


class Team(MongoBaseModel):
    captain_id: str
    tournament_id: Optional[str] = None
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    sport_type: str
    city: str
    state: str = "Gujarat"
    home_ground: Optional[str] = None
    logo: Optional[str] = None
    jersey_color: Optional[str] = None
    founded_year: Optional[int] = None
    team_type: Optional[str] = None
    players: Optional[List[dict]] = []
    total_players: int = 0
    coach_name: Optional[str] = None
    manager_name: Optional[str] = None
    manager_contact: Optional[str] = None
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    matches_drawn: int = 0
    documents: Optional[List[dict]] = []
    is_verified: bool = False
    is_active: bool = True


class TournamentRegistration(MongoBaseModel):
    registration_number: str
    tournament_id: str
    team_id: str
    registered_by: str
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    team_roster: Optional[List[dict]] = []
    captain_name: Optional[str] = None
    captain_contact: Optional[str] = None
    vice_captain_name: Optional[str] = None
    entry_fee: float = 0
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None
    documents_submitted: Optional[List[dict]] = []
    documents_verified: bool = False
    status: str = "pending"
    approval_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    special_requests: Optional[str] = None
    admin_notes: Optional[str] = None


class ProfessionalAvailability(MongoBaseModel):
    professional_id: str = Field(..., index=True)
    professional_name: str
    professional_type: str
    sport_type: str
    city: str = Field(..., index=True)
    state: str = "Gujarat"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    available_from_date: datetime
    available_to_date: Optional[datetime] = None
    available_days: Optional[List[str]] = []
    available_time_slots: Optional[List[dict]] = []
    per_match_fee: float
    currency: str = "INR"
    match_types: Optional[List[str]] = []
    can_play: bool = True
    can_coach: bool = False
    can_umpire: bool = False
    min_notice_hours: int = 24
    max_bookings_per_week: Optional[int] = None
    rating: float = 0.0
    total_bookings: int = 0
    total_reviews: int = 0
    is_active: bool = True
    is_verified: bool = False


class ProfessionalBooking(MongoBaseModel):
    booking_number: str = Field(..., index=True)
    professional_id: str
    booked_by: str
    tournament_id: Optional[str] = None
    match_id: Optional[str] = None
    booking_date: datetime
    match_date: datetime
    match_start_time: str
    match_end_time: str
    sport_type: str
    match_type: str
    location: str
    venue_address: Optional[str] = None
    role: str
    per_match_fee: float
    total_amount: float
    currency: str = "INR"
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None
    status: str = "confirmed"
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    special_requests: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
