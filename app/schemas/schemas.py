from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[dict] = None


# ─────────────────────────────────────────────────────────────────────────────
# MEDIA / UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

class MediaUploadResponse(BaseModel):
    """Returned by POST /api/media/upload for every image upload."""
    url: str           # publicly accessible URL (stored in entity document)
    media_id: str      # MongoDB _id of the media_assets document
    media_type: str    # always "image" for now
    entity_type: str   # user_avatar | venue | shop | tournament_banner | ad_banner | …
    entity_id: Optional[str] = None
    uploaded_by: str
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# AD BANNERS  (super_admin managed; Flutter carousel on RoleSelectionScreen)
# ─────────────────────────────────────────────────────────────────────────────

class AdBannerCreate(BaseModel):
    """
    image_url MUST come from a prior call to POST /api/media/upload with
    entity_type="ad_banner".  Never accept raw binary here.
    """
    image_url: str
    tap_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True

class AdBannerUpdate(BaseModel):
    image_url: Optional[str] = None
    tap_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class AdBannerResponse(BaseModel):
    id: str
    image_url: str
    tap_url: Optional[str]
    title: Optional[str]
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC FILTER CONFIG
# ─────────────────────────────────────────────────────────────────────────────

class FilterConfigResponse(BaseModel):
    page: str
    filters: List[dict]
    updated_at: datetime

class AppConfigResponse(BaseModel):
    key: str
    value: Any
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    professional_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = "Gujarat" 
    bio: Optional[str] = None
    avatar: Optional[str] = None          # URL from /api/media/upload
    sports_interests: Optional[List[str]] = None
    player_position: Optional[str] = None
    playing_style: Optional[str] = None
    certification: Optional[str] = None
    experience_years: Optional[int] = None
    children_count: Optional[int] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    professional_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None          # URL from /api/media/upload
    sports_interests: Optional[List[str]] = None
    player_position: Optional[str] = None
    playing_style: Optional[str] = None
    certification: Optional[str] = None
    experience_years: Optional[int] = None
    children_count: Optional[int] = None
    onboarding_completed: Optional[bool] = None

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class UserResponse(BaseModel):
    id: str
    phone: str
    name: Optional[str]
    email: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    role: Optional[str]
    roles: Optional[List[str]]
    professional_type: Optional[str]
    city: Optional[str]
    state: Optional[str]
    bio: Optional[str]
    avatar: Optional[str]                 # DB-stored URL
    sports_interests: Optional[List[str]]
    player_position: Optional[str]
    playing_style: Optional[str]
    certification: Optional[str]
    experience_years: Optional[int]
    children_count: Optional[int]
    organizer_status: Optional[str]
    professional_status: Optional[str]
    professional_fee_paid: Optional[bool]
    tournaments_organized: Optional[int]
    is_verified: bool
    onboarding_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PublicUserProfile(BaseModel):
    """Returned when any user views another user's profile."""
    id: str
    name: Optional[str]
    role: Optional[str]
    professional_type: Optional[str]
    city: Optional[str]
    state: Optional[str]
    bio: Optional[str]
    avatar: Optional[str]
    sports_interests: Optional[List[str]]
    player_position: Optional[str]
    playing_style: Optional[str]
    certification: Optional[str]
    experience_years: Optional[int]
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# SPORTS STATS
# ─────────────────────────────────────────────────────────────────────────────

class SportsStatsCreate(BaseModel):
    sport_type: str
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    detailed_stats: Optional[dict] = None
    rating: Optional[float] = 0.0
    achievements: Optional[List[dict]] = None

class SportsStatsResponse(BaseModel):
    id: str
    user_id: str
    sport_type: str
    matches_played: int
    wins: int
    losses: int
    draws: int
    detailed_stats: Optional[dict]
    rating: float
    achievements: Optional[List[dict]]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# VENUE
# ─────────────────────────────────────────────────────────────────────────────

class VenueBase(BaseModel):
    name: str
    description: Optional[str] = None
    venue_type: Optional[str] = None
    sports_available: List[str]
    amenities: Optional[List[str]] = None
    city: str
    state: str = "Gujarat"
    address: str
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_hour: float
    weekend_price: Optional[float] = None
    peak_hour_price: Optional[float] = None
    opening_time: str
    closing_time: str
    operating_days: List[str]
    capacity: Optional[int] = None
    surface_type: Optional[str] = None
    indoor_outdoor: Optional[str] = None
    # All image URLs from /api/media/upload (entity_type="venue")
    images: Optional[List[str]] = None
    contact_number: str
    email: Optional[EmailStr] = None
    website: Optional[str] = None

class VenueCreate(VenueBase):
    pass

class VenueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sports_available: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    price_per_hour: Optional[float] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None

class VenueResponse(VenueBase):
    id: str
    owner_id: Optional[str]
    rating: float
    total_reviews: int
    total_bookings: int
    is_verified: bool
    is_featured: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# BOOKING
# ─────────────────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    venue_id: str
    sport_type: str
    booking_date: str
    start_time: str
    end_time: str
    player_count: Optional[int] = None
    team_name: Optional[str] = None
    contact_person: str
    contact_number: str
    special_requests: Optional[str] = None

class SplitPaymentRequest(BaseModel):
    booking_id: str
    participants: List[dict]

class BookingResponse(BaseModel):
    id: str
    booking_number: str
    user_id: str
    venue_id: str
    sport_type: str
    booking_date: str
    start_time: str
    end_time: str
    duration_hours: Optional[float]
    player_count: Optional[int]
    team_name: Optional[str]
    base_price: float
    total_amount: float
    payment_status: str
    status: str
    is_split_payment: bool
    split_payment_data: Optional[List[dict]]
    split_payment_link: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# VENUE REVIEW
# ─────────────────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    venue_id: str
    booking_id: Optional[str] = None
    rating: int
    review_text: Optional[str] = None
    cleanliness_rating: Optional[int] = None
    facilities_rating: Optional[int] = None
    staff_rating: Optional[int] = None
    value_rating: Optional[int] = None

class ReviewResponse(BaseModel):
    id: str
    venue_id: str
    user_id: str
    rating: int
    review_text: Optional[str]
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# SHOP
# ─────────────────────────────────────────────────────────────────────────────

class ShopBase(BaseModel):
    name: str
    description: Optional[str] = None
    shop_type: Optional[str] = None
    category: Optional[str] = None
    products: Optional[List[dict]] = None
    specialization: Optional[List[str]] = None
    brands_available: Optional[List[str]] = None
    city: str
    state: str = "Gujarat"
    address: str
    landmark: Optional[str] = None
    contact_number: str
    whatsapp_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    operating_days: Optional[List[str]] = None
    home_delivery: bool = False
    online_payment: bool = False
    bulk_orders: bool = False
    custom_manufacturing: bool = False
    # Image URLs from /api/media/upload (entity_type="shop")
    images: Optional[List[str]] = None

class ShopCreate(ShopBase):
    pass

class ShopUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    products: Optional[List[dict]] = None
    contact_number: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ShopResponse(ShopBase):
    id: str
    owner_id: Optional[str]
    rating: float
    total_reviews: int
    total_enquiries: int
    is_featured: bool
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# JOB
# ─────────────────────────────────────────────────────────────────────────────

class JobBase(BaseModel):
    title: str
    job_type: str
    description: str
    sport_type: Optional[str] = None
    employment_type: str
    experience_required: Optional[str] = None
    certification_required: Optional[List[str]] = None
    city: str
    state: str = "Gujarat"
    location_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_type: Optional[str] = None
    currency: Optional[str] = "INR"
    other_benefits: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    language_required: Optional[List[str]] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    application_deadline: Optional[datetime] = None
    how_to_apply: Optional[str] = None
    application_email: Optional[str] = None
    application_phone: Optional[str] = None
    application_url: Optional[str] = None
    # Banner image URL from /api/media/upload (entity_type="job_banner")
    banner_image: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None
    sport_type: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    certification_required: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    location_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_type: Optional[str] = None
    other_benefits: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    language_required: Optional[List[str]] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    application_deadline: Optional[datetime] = None
    how_to_apply: Optional[str] = None
    application_email: Optional[str] = None
    application_phone: Optional[str] = None
    application_url: Optional[str] = None
    banner_image: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class JobResponse(JobBase):
    id: str
    posted_by: str
    views_count: int
    applications_count: int
    status: str
    is_featured: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# DICTIONARY
# ─────────────────────────────────────────────────────────────────────────────

class DictionaryBase(BaseModel):
    term: str
    sport: str
    category: Optional[str] = None
    definition: str
    explanation: Optional[str] = None
    examples: Optional[List[str]] = None
    related_terms: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    gujarati_term: Optional[str] = None
    hindi_term: Optional[str] = None
    difficulty_level: Optional[str] = None

class DictionaryCreate(DictionaryBase):
    pass

class DictionaryUpdate(BaseModel):
    definition: Optional[str] = None
    explanation: Optional[str] = None
    examples: Optional[List[str]] = None
    is_active: Optional[bool] = None

class DictionaryResponse(DictionaryBase):
    id: str
    slug: str
    views_count: int
    helpful_count: int
    is_featured: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# TOURNAMENT
# ─────────────────────────────────────────────────────────────────────────────

class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None
    sport_type: str
    tournament_type: Optional[str] = None
    format: Optional[str] = None
    team_size: Optional[int] = None
    max_teams: int
    min_teams: Optional[int] = None
    age_category: Optional[str] = None
    gender_category: Optional[str] = None
    skill_level: Optional[str] = None
    city: str
    state: str = "Gujarat"
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    registration_start: Optional[datetime] = None
    registration_deadline: datetime
    entry_fee: float = 0
    prize_pool: Optional[float] = None
    prize_distribution: Optional[List[dict]] = None
    documents_required: Optional[List[str]] = None
    rules: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    # Images uploaded by organiser via /api/media/upload
    banner_image: Optional[str] = None
    additional_images: Optional[List[str]] = None
    # Cancellation / postponement
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    postponed_reason: Optional[str] = None
    original_start_date: Optional[datetime] = None

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    entry_fee: Optional[float] = None
    max_teams: Optional[int] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    rules: Optional[str] = None
    banner_image: Optional[str] = None
    additional_images: Optional[List[str]] = None
    # Rescheduling (used by postpone flow)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    # Status — accepted values:
    #   upcoming | registration_closed | ongoing | completed | cancelled | postponed
    status: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    postponed_reason: Optional[str] = None
    original_start_date: Optional[datetime] = None
    current_teams: Optional[int] = None
    is_active: Optional[bool] = None

class TournamentResponse(TournamentBase):
    id: str
    organizer_id: str
    current_teams: int
    views_count: int
    status: str
    is_featured: bool
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# TEAM
# ─────────────────────────────────────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    sport_type: str
    city: str
    state: str = "Gujarat"
    home_ground: Optional[str] = None
    team_type: Optional[str] = None
    players: Optional[List[dict]] = None
    coach_name: Optional[str] = None
    manager_name: Optional[str] = None
    manager_contact: Optional[str] = None
    # Logo URL from /api/media/upload (entity_type="team_logo")
    logo_image: Optional[str] = None
    logo: Optional[str] = None          # alias accepted from Flutter clients

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    players: Optional[List[dict]] = None
    logo_image: Optional[str] = None
    logo: Optional[str] = None          # alias accepted from Flutter clients
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: str
    captain_id: str
    tournament_id: Optional[str]
    total_players: int
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_drawn: int
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZER MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class OrganizerManagerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    role_description: Optional[str] = None
    permissions: Optional[List[str]] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = "Gujarat"
    bio: Optional[str] = None
    sports_interests: Optional[List[str]] = None

class OrganizerManagerAddExisting(BaseModel):
    user_id: str
    role_description: Optional[str] = None
    permissions: List[str] = ["create_tournament", "edit_tournament", "view_registrations"]

class OrganizerManagerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class OrganizerManagerResponse(BaseModel):
    id: str
    organizer_id: str
    manager_user_id: Optional[str]
    name: str
    phone: str
    email: Optional[str]
    role_description: Optional[str]
    permissions: List[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# TOURNAMENT REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

class TournamentRegistrationCreate(BaseModel):
    tournament_id: str
    team_id: str
    team_roster: List[dict]
    captain_name: str
    captain_contact: str
    vice_captain_name: Optional[str] = None
    special_requests: Optional[str] = None

class TournamentRegistrationUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    documents_verified: Optional[bool] = None
    rejection_reason: Optional[str] = None

class TournamentRegistrationResponse(BaseModel):
    id: str
    registration_number: str
    tournament_id: str
    team_id: str
    registered_by: str
    captain_name: str
    captain_contact: str
    entry_fee: float
    payment_status: str
    status: str
    documents_verified: bool
    registration_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL AVAILABILITY
# ─────────────────────────────────────────────────────────────────────────────

class ProfessionalAvailabilityCreate(BaseModel):
    sport_type: str
    available_from_date: datetime
    available_to_date: Optional[datetime] = None
    available_days: Optional[List[str]] = None
    available_time_slots: Optional[List[dict]] = None
    specific_dates: Optional[List[str]] = None   # ISO strings e.g. ["2026-04-20T00:00:00"]
    per_match_fee: float
    match_types: Optional[List[str]] = None
    can_play: bool = True
    can_coach: bool = False
    can_umpire: bool = False
    min_notice_hours: int = 24
    max_bookings_per_week: Optional[int] = None

class ProfessionalAvailabilityUpdate(BaseModel):
    available_from_date: Optional[datetime] = None
    available_to_date: Optional[datetime] = None
    available_days: Optional[List[str]] = None
    available_time_slots: Optional[List[dict]] = None
    specific_dates: Optional[List[str]] = None
    per_match_fee: Optional[float] = None
    match_types: Optional[List[str]] = None
    can_play: Optional[bool] = None
    can_coach: Optional[bool] = None
    can_umpire: Optional[bool] = None
    min_notice_hours: Optional[int] = None
    max_bookings_per_week: Optional[int] = None
    is_active: Optional[bool] = None

class ProfessionalAvailabilityResponse(BaseModel):
    id: str
    professional_id: str
    professional_name: str
    professional_type: str
    sport_type: str
    city: str
    state: str
    available_from_date: datetime
    available_to_date: Optional[datetime]
    available_days: Optional[List[str]]
    available_time_slots: Optional[List[dict]]
    specific_dates: Optional[List[str]] = None
    per_match_fee: float
    currency: str
    match_types: Optional[List[str]]
    can_play: bool
    can_coach: bool
    can_umpire: bool
    min_notice_hours: int
    max_bookings_per_week: Optional[int]
    rating: float
    total_bookings: int
    total_reviews: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL BOOKING
# ─────────────────────────────────────────────────────────────────────────────

class ProfessionalBookingCreate(BaseModel):
    professional_id: str
    tournament_id: Optional[str] = None
    match_id: Optional[str] = None
    match_date: datetime
    match_start_time: str
    match_end_time: str
    sport_type: str
    match_type: str
    location: str
    venue_address: Optional[str] = None
    role: str
    special_requests: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None

class ProfessionalBookingUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    cancellation_reason: Optional[str] = None

class ProfessionalBookingResponse(BaseModel):
    id: str
    booking_number: str
    professional_id: str
    booked_by: str
    tournament_id: Optional[str]
    match_id: Optional[str]
    booking_date: datetime
    match_date: datetime
    match_start_time: str
    match_end_time: str
    sport_type: str
    match_type: str
    location: str
    role: str
    per_match_fee: float
    total_amount: float
    currency: str
    payment_status: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# ACADEMY
# Unified schema — matches both the old dictionary-seeded documents and new
# admin-created ones. All fields are optional except name, sport_type, city.
# ─────────────────────────────────────────────────────────────────────────────

class CoachingStaffMember(BaseModel):
    name: str
    role: Optional[str] = None
    experience: Optional[str] = None
    image_url: Optional[str] = None   # URL from POST /api/media/upload

class AcademyCreate(BaseModel):
    # Core identity
    term: str                                   # maps to "term" in old dictionary docs
    sport_type: str                             # maps to "sport" in old docs
    description: Optional[str] = None          # maps to "definition" / "explanation"
    category: Optional[str] = "Academy"

    # Location
    city: str
    state: str = "Gujarat"
    address: Optional[str] = None
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Contact
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None

    # Schedule & fees
    timing: Optional[str] = None               # e.g. "Mon-Sat: 6AM-9PM"
    fees: Optional[str] = None                 # e.g. "₹5,000-₹15,000 per month"
    fees_per_month: Optional[float] = None     # numeric version for filtering
    capacity: Optional[int] = None

    # Programs & structure
    programs: Optional[List[str]] = None       # list of programme names
    age_groups: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None     # alias for amenities

    # Coaching staff
    coaching_staff: List[CoachingStaffMember] = []

    # Media — all URLs from POST /api/media/upload (entity_type="academy")
    cover_image: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    images: Optional[List[str]] = None         # alias used by some clients

    # Extras (kept for forward compat)
    achievements: Optional[List[str]] = None
    examples: Optional[List[str]] = None

class AcademyUpdate(BaseModel):
    term: Optional[str] = None
    description: Optional[str] = None
    timing: Optional[str] = None
    fees: Optional[str] = None
    fees_per_month: Optional[float] = None
    capacity: Optional[int] = None
    programs: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    coaching_staff: Optional[List[CoachingStaffMember]] = None
    cover_image: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    images: Optional[List[str]] = None
    age_groups: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class AcademyResponse(AcademyCreate):
    id: str
    owner_id: Optional[str] = None
    rating: float = 0.0
    total_reviews: int = 0
    views_count: int = 0
    is_featured: bool = False
    is_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    distance_km: Optional[float] = None        # populated by nearby search

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# COMMUNITY
# ─────────────────────────────────────────────────────────────────────────────

class CommunityBase(BaseModel):
    name: str
    description: Optional[str] = None
    sport_type: str
    city: str
    state: str = "Gujarat"
    cover_image: Optional[str] = None   # URL from /api/media/upload (entity_type="community")

class CommunityCreate(CommunityBase):
    pass

class CommunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    is_active: Optional[bool] = None

class CommunityResponse(CommunityBase):
    id: str
    created_by: str
    members_count: int
    posts_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL OTP (new)
# ─────────────────────────────────────────────────────────────────────────────

class EmailOTPRequest(BaseModel):
    email: str

class EmailOTPVerify(BaseModel):
    email: str
    otp: str


# ─────────────────────────────────────────────────────────────────────────────
# ROLE REQUEST (new)
# ─────────────────────────────────────────────────────────────────────────────

class RoleRequest(BaseModel):
    role: Optional[str] = None
    professional_type: Optional[str] = None   # required for professional role


# ─────────────────────────────────────────────────────────────────────────────
# JOB APPLICATION (new)
# ─────────────────────────────────────────────────────────────────────────────

class JobApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None
    expected_salary: Optional[float] = None
    available_from: Optional[datetime] = None

class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None           # shortlisted | selected | rejected
    rejection_reason: Optional[str] = None
    organizer_notes: Optional[str] = None

class JobApplicationResponse(BaseModel):
    id: str
    job_id: str
    applicant_id: str
    applicant_name: str
    applicant_phone: str
    applicant_professional_type: Optional[str]
    cover_letter: Optional[str]
    experience_years: Optional[int]
    certification: Optional[str]
    expected_salary: Optional[float]
    available_from: Optional[datetime]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    organizer_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# MATCH / FIXTURE (new)
# ─────────────────────────────────────────────────────────────────────────────

class MatchCreate(BaseModel):
    round_number: int = 1
    match_number: int
    stage: Optional[str] = None
    team1_id: Optional[str] = None
    team1_name: Optional[str] = None
    team2_id: Optional[str] = None
    team2_name: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[str] = None
    venue: Optional[str] = None

class MatchUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[str] = None
    venue: Optional[str] = None
    team1_score: Optional[str] = None
    team2_score: Optional[str] = None
    winner_id: Optional[str] = None
    result_summary: Optional[str] = None
    status: Optional[str] = None     # scheduled | ongoing | completed | cancelled

class MatchResponse(BaseModel):
    id: str
    tournament_id: str
    round_number: int
    match_number: int
    stage: Optional[str]
    team1_id: Optional[str]
    team1_name: Optional[str]
    team2_id: Optional[str]
    team2_name: Optional[str]
    scheduled_date: Optional[datetime]
    scheduled_time: Optional[str]
    venue: Optional[str]
    winner_id: Optional[str]
    team1_score: Optional[str]
    team2_score: Optional[str]
    result_summary: Optional[str]
    status: str
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True