# Sports Diary Backend v2 — Media & Dynamic Data Guide

## Core Principle
**All images, all filter options, all list data is stored in MongoDB and served dynamically.**  
Nothing is hard-coded in the backend or the Flutter app.

---

## 1. Image Upload Flow (Universal for ALL entity types)

Every image — whether it's an ad banner, venue photo, user avatar, tournament poster,
shop picture, academy gallery, team logo, or job banner — follows the same two-step flow:

### Step 1 — Upload the image
```
POST /api/media/upload
Content-Type: multipart/form-data

Fields:
  file         (binary)   The image file (JPEG / PNG / WEBP / GIF, max 10 MB)
  entity_type  (string)   One of the allowed types below
  entity_id    (string?)  Optional: ID of the entity this image belongs to

Allowed entity_types:
  user_avatar       → Profile pictures (all roles)
  venue             → Venue photos (owner / super_admin uploads)
  shop              → Shop photos (super_admin uploads)
  tournament_banner → Tournament main banner (organiser uploads)
  tournament_image  → Additional tournament images (organiser uploads)
  ad_banner         → Ad carousel images (super_admin ONLY)
  academy           → Academy cover + gallery (super_admin uploads)
  community         → Community cover image (admin / super_admin)
  team_logo         → Team logo (captain uploads)
  job_banner        → Job listing banner (organiser / admin)
  profile_image     → Alternative profile image

Response:
  {
    "url":         "http://<server>/uploads/venue/venue_abc123.jpg",
    "media_id":    "64f1a2b3c4d5e6f7a8b9c0d1",
    "entity_type": "venue",
    "entity_id":   null,
    "uploaded_by": "64e0...",
    "created_at":  "2025-01-01T00:00:00Z"
  }
```

### Step 2 — Save the URL in the entity
Use the returned `url` when creating or updating an entity:

| Entity          | Field(s)                          | Endpoint                                  |
|-----------------|-----------------------------------|-------------------------------------------|
| User avatar     | `avatar`                          | `PUT /api/auth/profile`                   |
| Venue           | `images` (list)                   | `POST /api/venues` or `PUT /api/venues/{id}` |
| Shop            | `images` (list)                   | `POST /api/admin/shops/create`            |
| Tournament      | `banner_image`, `additional_images`| `POST /api/tournaments`                  |
| Ad banner       | `image_url`                       | `POST /api/media/ad-banners`              |
| Academy         | `cover_image`, `gallery_images`   | `POST /api/admin/academies/create`        |
| Community       | `cover_image`                     | `POST /api/admin/communities/create`      |
| Team            | `logo_image`                      | `POST /api/tournaments/teams`             |
| Job listing     | `banner_image`                    | `POST /api/marketplace/jobs`              |

---

## 2. Ad Banners (Flutter RoleSelectionScreen Carousel)

Super admin manages the carousel that appears on the role-selection screen.

```
# 1. Upload the banner image
POST /api/media/upload
  entity_type = "ad_banner"
  → { "url": "http://…/uploads/ad_banner/ad_banner_xyz.jpg" }

# 2. Create the banner record
POST /api/media/ad-banners
  Authorization: Bearer <super_admin_token>
  Body: {
    "image_url":   "http://…/uploads/ad_banner/ad_banner_xyz.jpg",
    "tap_url":     "https://example.com/promo",   # optional deep-link
    "title":       "Summer Tournament",           # optional
    "description": "Register now!",               # optional
    "sort_order":  0,                             # lower = shown first
    "is_active":   true
  }

# Flutter reads banners
GET /api/media/ad-banners           → { banners: [...], count: N }
GET /api/media/ad-banners?active_only=false   → all banners including inactive

# Reorder
PUT /api/media/ad-banners/reorder
  Body: [{"id": "...", "sort_order": 0}, {"id": "...", "sort_order": 1}]

# Update / delete
PUT    /api/media/ad-banners/{id}
DELETE /api/media/ad-banners/{id}
```

---

## 3. Dynamic Filter Config (Venues, Tournaments, Jobs, etc.)

Flutter reads filter chips dynamically — no hard-coding of city names, sport types, etc.

```
GET /api/media/config/filters/venues
GET /api/media/config/filters/tournaments
GET /api/media/config/filters/jobs
GET /api/media/config/filters/professionals
GET /api/media/config/filters/shops
GET /api/media/config/filters/academies

Response shape:
{
  "page": "venues",
  "filters": [
    { "key": "city",    "label": "City",  "type": "single_select", "options": ["Ahmedabad", "Surat", …] },
    { "key": "sport",   "label": "Sport", "type": "single_select", "options": ["Cricket", "Football", …] },
    { "key": "min_price","label": "Min Price", "type": "number" },
    …
  ]
}

City and sport option lists are populated live from the actual DB documents —
if you add a new venue in a new city, that city appears in the filter automatically.

Super admin can customise / add filter chips:
PUT /api/media/config/filters/venues
  Authorization: Bearer <super_admin_token>
  Body: [ { "key": "surface_type", "label": "Surface", "type": "single_select", "options": ["Turf", "Clay"] }, … ]
```

---

## 4. Generic App Config

```
# Store any arbitrary config (sports list, feature flags, announcement text, etc.)
PUT /api/media/config/sports_list
  Body: { "value": ["Cricket", "Football", "Volleyball", "Basketball", …] }

GET /api/media/config/sports_list
  → { "key": "sports_list", "value": […], "updated_at": "…" }
```

---

## 5. Profile Pictures — Cross-user Visibility

When user A views user B's profile:
```
GET /api/auth/users/{user_b_id}
→ {
    "id":     "…",
    "name":   "Alex",
    "avatar": "http://<server>/uploads/user_avatar/user_avatar_abc.jpg",
    …
  }
```
Flutter renders `avatar` via `CachedNetworkImage(imageUrl: user.avatar)`.  
The avatar URL is stored in the `users` collection — fully persistent, retrievable by anyone.

---

## 6. Media Gallery (per entity)

```
GET /api/media/gallery/venue/{venue_id}
GET /api/media/gallery/tournament_banner/{tournament_id}
GET /api/media/gallery/shop/{shop_id}
→ { "assets": [ { "id": "…", "url": "…", "created_at": "…" }, … ], "count": N }
```

---

## 7. Who Uploads What

| Role          | Can upload for                                    |
|---------------|---------------------------------------------------|
| player        | user_avatar, team_logo                            |
| organiser     | user_avatar, tournament_banner, tournament_image  |
| professional  | user_avatar                                       |
| admin         | user_avatar, venue, shop, community, job_banner   |
| super_admin   | Everything including ad_banner                    |

---

## 8. MongoDB Collections (new / updated)

| Collection               | Purpose                                          |
|--------------------------|--------------------------------------------------|
| `users`                  | `avatar` field = URL from /api/media/upload      |
| `venues`                 | `images` field = list of URLs                    |
| `shops`                  | `images` field = list of URLs                    |
| `tournaments`            | `banner_image`, `additional_images` = URLs       |
| `academies`              | `cover_image`, `gallery_images` = URLs           |
| `communities`            | `cover_image` = URL                              |
| `teams`                  | `logo_image` = URL                               |
| `jobs`                   | `banner_image` = URL                             |
| `ad_banners`             | `image_url` = URL; managed by super_admin        |
| `media_assets`           | Metadata for every uploaded file                 |
| `filter_configs`         | Per-page filter definitions (super_admin editable)|
| `app_configs`            | Generic key-value app config                     |

---

## v3 Additions — New Features

### Email OTP Login (free, no SDK)
Two new endpoints for email-based authentication:
```
POST /api/auth/send-email-otp    { "email": "user@example.com" }
POST /api/auth/verify-email-otp  { "email": "user@example.com", "otp": "123456" }
```
Configure free SMTP via env vars (or OTP prints to console in dev):
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourapp@gmail.com
SMTP_PASSWORD=your-app-password    # Gmail → Account → App Passwords
SMTP_FROM=noreply@sportsdiary.app
```
No paid service required. Gmail, Brevo (300 emails/day free), Mailjet (200/day free) all work.

### Multi-Role Users
`role` is still returned for backwards compat. New `roles: []` array is the source of truth.
A user can hold: `player`, `parent`, `professional`, `organizer`, `admin`, `super_admin` simultaneously.

### Organiser Role Approval Workflow
```
User:  POST /api/auth/request-organizer-role
Admin: GET  /api/admin/pending-organizers
Admin: POST /api/admin/approve-organizer/{user_id}
Admin: POST /api/admin/reject-organizer/{user_id}?reason=...
```

### Professional ₹3000 Fee Gate
```
User:  POST /api/auth/request-professional-role  { "professional_type": "Coach" }
Admin: GET  /api/admin/pending-professionals
Admin: POST /api/admin/confirm-professional-fee/{user_id}?transaction_ref=TXN123
```
Fee amount is configurable in config.py → PROFESSIONAL_FEE_INR (default 3000).

### Job Applications Lifecycle
```
Professional: POST /api/marketplace/jobs/{id}/apply
Professional: GET  /api/marketplace/my-applications
Organiser:    GET  /api/marketplace/jobs/{id}/applications
Organiser:    PUT  /api/marketplace/applications/{application_id}
              Body: { "status": "shortlisted" | "selected" | "rejected" }
```
When status = "selected", the job is automatically marked "filled".

### Match Scheduling & Results
```
POST   /api/tournaments/{id}/matches           Create fixture
GET    /api/tournaments/{id}/matches           List fixtures (filter by round, status)
PUT    /api/tournaments/{id}/matches/{match_id} Update schedule or record result
DELETE /api/tournaments/{id}/matches/{match_id} Cancel match
GET    /api/tournaments/{id}/standings          Points table (W=3, D=1, L=0)
```
When a match is marked completed, team win/loss/draw stats update automatically.
