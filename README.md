# Sports Diary — Flutter App

**Gujarat Sports Ecosystem Platform**

A full-featured Flutter app integrated with the deployed FastAPI + MongoDB backend.

---

## Architecture

```
lib/
├── main.dart                          # App entry point
├── core/
│   ├── constants/app_constants.dart   # API URLs, config
│   ├── network/dio_client.dart        # Dio + Auth interceptor
│   ├── providers/auth_provider.dart   # Global auth state (Riverpod)
│   ├── router/app_router.dart         # GoRouter + auth guards
│   └── theme/app_theme.dart           # Light & dark themes
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   ├── models/user_model.dart
│   │   │   └── repositories/auth_repository.dart
│   │   └── presentation/
│   │       ├── providers/auth_screen_provider.dart
│   │       └── screens/auth_screens.dart    # Splash, Onboarding, Phone, OTP,
│   │                                          # ProfileSetup, RoleSelection, CitySports
│   ├── venues/
│   │   ├── data/repositories/venue_repository.dart  # Model + Repo + Providers
│   │   └── presentation/screens/venues_screens.dart  # List, Detail, Booking
│   ├── tournaments/
│   │   └── presentation/screens/tournaments_screens.dart  # Model+Repo+List+Detail+Create
│   ├── marketplace/
│   │   └── presentation/screens/marketplace_screens.dart  # Shops+Jobs+Academies
│   ├── community/
│   │   └── presentation/screens/community_screens.dart    # List+Detail+CreatePost
│   └── profile/
│       └── presentation/screens/profile_screen.dart
└── shared/widgets/
    ├── shared_widgets.dart   # SdButton, SdTextField, SdChip, StarRating, LoadingShimmer
    └── main_shell.dart       # Bottom navigation shell
```

---

## State Management

All state is managed via **Riverpod**:

| Provider | Type | Purpose |
|---|---|---|
| `authStateProvider` | `StateNotifierProvider` | Global auth state (login, user, onboarding) |
| `themeModeProvider` | `StateNotifierProvider` | Light/dark/system theme |
| `routerProvider` | `Provider<GoRouter>` | GoRouter with auth redirect |
| `dioProvider` | `Provider<Dio>` | Dio client with auth interceptor |
| `venuesProvider` | `FutureProvider.family` | Venues list with filters |
| `venueDetailProvider` | `FutureProvider.family` | Single venue |
| `tournamentsProvider` | `FutureProvider.family` | Tournaments list |
| `tournamentDetailProvider` | `FutureProvider.family` | Single tournament |
| `shopsProvider` | `FutureProvider.family` | Shops list |
| `jobsProvider` | `FutureProvider.family` | Jobs list |
| `academiesProvider` | `FutureProvider.family` | Academies list |
| `communitiesProvider` | `FutureProvider.family` | Communities list |
| `communityDetailProvider` | `FutureProvider.family` | Single community |
| `communityPostsProvider` | `FutureProvider.family` | Posts in a community |

---

## ⚙️ Setup Instructions

### Prerequisites

1. **Flutter SDK** ≥ 3.13.0 — [Install Flutter](https://docs.flutter.dev/get-started/install)
2. **Dart SDK** ≥ 3.1.0 (bundled with Flutter)
3. **Android Studio** or **Xcode** for a device/emulator
4. Your backend must be deployed (already done on Render)

---

### Step 1 — Clone / Open the project

```bash
# If you received this as a zip, unzip it first
unzip sports_diary_flutter_integrated.zip
cd sports_diary
```

---

### Step 2 — Set the Backend URL

Open `lib/core/constants/app_constants.dart` and update the `baseUrl`:

```dart
// Find this line:
static const String baseUrl = 'https://sportsdiary-backend.onrender.com/api';

// Replace with your actual Render deployment URL, e.g.:
static const String baseUrl = 'https://YOUR-APP-NAME.onrender.com/api';
```

> **How to find your Render URL:**
> Go to [dashboard.render.com](https://dashboard.render.com) → your service → copy the URL shown at the top.
> Append `/api` to it.

---

### Step 3 — Install dependencies

```bash
flutter pub get
```

---

### Step 4 — Run on Android

```bash
# List available devices
flutter devices

# Run on a specific device (replace <device-id> with your device)
flutter run -d <device-id>

# Or simply (will pick the first available device)
flutter run
```

---

### Step 5 — Run on iOS (macOS only)

```bash
# Install pods first
cd ios && pod install && cd ..

# Run
flutter run -d iphone
```

---

### Step 6 — Run in Chrome (web preview)

```bash
flutter run -d chrome
```

> Note: `flutter_secure_storage` may not work perfectly on web. For production web use, swap it for `shared_preferences`.

---

## 🔑 Authentication Flow

The backend uses **OTP-based authentication** (no SMS — OTP is returned in the API response for development):

1. User enters phone number (+91XXXXXXXXXX)
2. App calls `POST /api/auth/send-otp`
3. Backend returns the OTP in the response (shown in a green box on screen for dev)
4. User enters OTP → `POST /api/auth/verify-otp`
5. Backend returns `access_token` + `user` object
6. Token is stored in **FlutterSecureStorage** (encrypted)
7. All subsequent requests automatically include `Authorization: Bearer <token>`
8. Token is valid for **7 days**

---

## 🌐 API Endpoints Used

| Feature | Method | Endpoint |
|---|---|---|
| Send OTP | POST | `/api/auth/send-otp` |
| Verify OTP | POST | `/api/auth/verify-otp` |
| Get current user | GET | `/api/auth/me` |
| Create profile | POST | `/api/auth/profile` |
| Update profile | PUT | `/api/auth/profile` |
| Update location | PUT | `/api/auth/location` |
| Logout | POST | `/api/auth/logout` |
| List venues | GET | `/api/venues` |
| Venue detail | GET | `/api/venues/{id}` |
| Book venue | POST | `/api/venues/{id}/bookings` |
| List tournaments | GET | `/api/tournaments` |
| Tournament detail | GET | `/api/tournaments/{id}` |
| Create team | POST | `/api/tournaments/{id}/teams` |
| Create tournament | POST | `/api/tournaments` |
| List shops | GET | `/api/marketplace/shops` |
| Shop detail | GET | `/api/marketplace/shops/{id}` |
| List jobs | GET | `/api/marketplace/jobs` |
| Job detail | GET | `/api/marketplace/jobs/{id}` |
| List academies | GET | `/api/marketplace/academies` |
| Academy detail | GET | `/api/marketplace/academies/{id}` |
| List communities | GET | `/api/community` |
| Community detail | GET | `/api/community/{id}` |
| Community posts | GET | `/api/community/{id}/posts` |
| Create post | POST | `/api/community/{id}/posts` |
| Join community | POST | `/api/community/{id}/join` |
| Leave community | DELETE | `/api/community/{id}/leave` |

---

## 🐛 Troubleshooting

### "Connection refused" / "Network error"
- Make sure your Render backend is running (it may sleep after inactivity on free tier)
- Visit `https://YOUR-APP-NAME.onrender.com/api/health` in a browser to wake it up
- Check that `baseUrl` in `app_constants.dart` ends with `/api` (no trailing slash)

### "Unauthorized" after login
- Token may have expired (7 days). Just log out and log in again.

### Flutter version mismatch
```bash
flutter upgrade
flutter pub get
```

### iOS build fails
```bash
cd ios
pod deintegrate
pod install
cd ..
flutter clean
flutter pub get
flutter run
```

### Android build fails
```bash
flutter clean
flutter pub get
flutter run
```

### Shimmer / cached_network_image issues
```bash
flutter pub upgrade
```

---

## 📱 Features

- **Venues** — Browse, filter by sport/city, view details, book time slots
- **Tournaments** — Browse by status (upcoming/ongoing/completed), register teams, create tournaments
- **Marketplace** — Sports shops, jobs for coaches/umpires/trainers, academies
- **Community** — Browse communities by sport, view & create posts
- **Profile** — View profile, change role/city/sports, logout
- **Auth** — Phone + OTP login, multi-step onboarding (profile → role → city+sports)
- **Dark/Light theme** — Persistent theme preference

---

## 🏗️ Adding New Features

To add a new feature:
1. Create `lib/features/<name>/data/` with model + repository
2. Create `lib/features/<name>/presentation/screens/` with UI
3. Add Riverpod providers in the repository file
4. Add route in `lib/core/router/app_router.dart`
5. Add bottom nav item in `lib/shared/widgets/main_shell.dart` if needed
