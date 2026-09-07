# AI Career Coach — Mobile App (Jetpack Compose)

Android front-end for the AI Career Coaching Chatbot final year project. Built with
**Kotlin + Jetpack Compose + Material 3**.

## Status

All 8 screens are built and linked with Navigation Compose. After login, students
use a bottom bar (Home, Coach, Resources, Profile). Admins land on the admin dashboard.

## Screens

| Screen | File |
|--------|------|
| Landing Page | `ui/screens/LandingScreen.kt` |
| Login & Registration | `ui/screens/LoginRegisterScreen.kt` |
| Student Dashboard | `ui/screens/StudentDashboardScreen.kt` |
| AI Career Chat | `ui/screens/AICareerChatScreen.kt` |
| Career Resources | `ui/screens/CareerResourcesScreen.kt` |
| Student Profile | `ui/screens/StudentProfileScreen.kt` |
| Feedback | `ui/screens/FeedbackScreen.kt` |
| Admin Dashboard | `ui/screens/AdminDashboardScreen.kt` |

## Getting started

1. Open this folder in **Android Studio** (Koala or newer).
2. Let Gradle sync.
3. Run on an emulator or device (minSdk 26 / Android 8.0+).

**Try the flow:** Landing → Get Started or Log In → student home tabs. On the login
screen, use **Sign in as administrator** (with any filled email/password) for the
admin dashboard. Profile → Send Feedback, then back. Log Out returns to Landing.

## Project structure

```
app/src/main/java/com/aicareercoach/mobile/
├── MainActivity.kt
└── ui/
    ├── navigation/              # NavHost, routes, student bottom bar
    ├── theme/
    ├── components/
    └── screens/
```
