# 🏗️ Authentication System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         G-Catch Application                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Root Layout (layout.tsx)                   │   │
│  │  - AuthProvider (wraps entire app)                      │   │
│  │  - Navigation component                                 │   │
│  └──────────────────┬──────────────────────────────────────┘   │
│                     │                                            │
│     ┌───────────────┼───────────────┬────────────────┐          │
│     │               │               │                │          │
│  ┌──▼──┐      ┌────▼────┐    ┌────▼────┐    ┌───▼──┐         │
│  │Home │      │Sign In  │    │Sign Up  │    │Profile           │
│  │Page │      │Page     │    │Page     │    │Page              │
│  └─────┘      └────┬────┘    └────┬────┘    └───┬──┘         │
│                    │               │            │              │
│                    └───────────────┼────────────┘              │
│                                    │                           │
│                    ┌───────────────▼────────────┐             │
│                    │   Protected Route Wrapper  │             │
│                    │  (redirect if not logged)  │             │
│                    └────────────────────────────┘             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
    ┌──────────────────────────────────────────┐
    │      Context Layer (AuthContext)         │
    ├──────────────────────────────────────────┤
    │                                          │
    │  - useAuth() Hook                        │
    │  - User state management                 │
    │  - Loading state                         │
    │  - Logout function                       │
    │                                          │
    └──────────────┬───────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────┐
    │    Firebase Authentication (lib/firebase)│
    ├──────────────────────────────────────────┤
    │                                          │
    │  - Firebase App Init                     │
    │  - Auth Module                           │
    │  - Firestore Database                    │
    │                                          │
    └──────────────┬───────────────────────────┘
                   │
                   ▼
          ┌────────────────────┐
          │   Firebase Cloud   │
          │   (Backend)        │
          │                    │
          │ - Authentication   │
          │ - Firestore DB     │
          │ - Google OAuth     │
          │                    │
          └────────────────────┘
```

## Data Flow

### Sign Up Flow
```
User Input (Sign Up Form)
        │
        ▼
Form Validation
        │
        ▼
createUserWithEmailAndPassword(auth, email, password)
        │
        ▼
Firebase Authentication Service
        │
        ▼
User Created ✓
        │
        ▼
Auto Sign-In (redirect to home)
        │
        ▼
AuthContext Updates (user state)
        │
        ▼
Navigation Re-renders (shows logged-in UI)
```

### Sign In Flow
```
User Input (Email + Password)
        │
        ▼
Form Validation
        │
        ▼
signInWithEmailAndPassword(auth, email, password)
        │
        ▼
Firebase Validates Credentials
        │
        ▼
Session Created ✓
        │
        ▼
AuthContext Updates
        │
        ▼
Redirect to Home
```

### Google OAuth Flow
```
User Clicks "Sign In with Google"
        │
        ▼
signInWithPopup(auth, GoogleAuthProvider)
        │
        ▼
Google Sign-In Popup Opens
        │
        ▼
User Authenticates with Google
        │
        ▼
Google Returns Auth Token
        │
        ▼
Firebase Creates/Links Account
        │
        ▼
Session Established ✓
        │
        ▼
onAuthStateChanged Fires
        │
        ▼
AuthContext Updates with User Data
        │
        ▼
UI Updates (shows logged-in state)
```

## Component Hierarchy

```
Root Layout
│
├── AuthProvider
│   │
│   ├── Navigation
│   │   ├── Sign In Link (if logged out)
│   │   ├── Sign Up Link (if logged out)
│   │   └── User Menu (if logged in)
│   │       ├── Profile Link
│   │       └── Sign Out Button
│   │
│   └── Page Routes
│       ├── Home Page (/)
│       │   └── Scanner Component
│       │
│       ├── Sign In Page (/signin)
│       │   ├── Email Input
│       │   ├── Password Input
│       │   ├── Sign In Button
│       │   ├── Google Sign In Button
│       │   └── Link to Sign Up
│       │
│       ├── Sign Up Page (/signup)
│       │   ├── Name Input
│       │   ├── Email Input
│       │   ├── Password Input
│       │   ├── Confirm Password Input
│       │   ├── Sign Up Button
│       │   ├── Google Sign Up Button
│       │   └── Link to Sign In
│       │
│       └── Profile Page (/profile)
│           └── ProtectedRoute
│               ├── User Info Display
│               ├── Email Display
│               ├── Account Status
│               └── Sign Out Button
```

## State Management Flow

```
Firebase Auth Service
        │
        │ onAuthStateChanged()
        │
        ▼
AuthContext Provider
        │
        ├─── user state
        ├─── loading state
        └─── logout function
        │
        │ Context.Provider
        │
        ▼
useAuth() Hook
        │
        │ Access from any component:
        │
        ├─── const { user, loading, logout } = useAuth()
        │
        ▼
Component Updates/Re-renders
```

## Security Architecture

```
┌─────────────────────────────────────┐
│    User Browser                     │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Next.js Client Components  │  │
│  │   (React Components)         │  │
│  │                              │  │
│  │  - Sign Up Form              │  │
│  │  - Sign In Form              │  │
│  │  - Navigation                │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │  Firebase Auth SDK (Public)  │  │
│  │                              │  │
│  │  - NEXT_PUBLIC_* config OK   │  │
│  │  - No sensitive keys here    │  │
│  └──────────┬───────────────────┘  │
└─────────────┼──────────────────────┘
              │
              │ HTTPS Encrypted
              │
              ▼
    ┌─────────────────────┐
    │  Firebase Services  │
    │  (Cloud Backend)    │
    │                     │
    │ - Auth Validation   │
    │ - User Database     │
    │ - Security Rules    │
    │ - Session Tokens    │
    │                     │
    └─────────────────────┘
```

## File Structure

```
g-catch/
│
├── app/                          # Next.js app directory
│   ├── layout.tsx               # Root layout with AuthProvider
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   │
│   ├── signin/
│   │   └── page.tsx             # Sign-in page
│   │
│   ├── signup/
│   │   └── page.tsx             # Sign-up page
│   │
│   └── profile/
│       └── page.tsx             # User profile page
│
├── components/                   # Reusable components
│   ├── Navigation.tsx           # Auth-aware navigation
│   └── ProtectedRoute.tsx       # Route protection wrapper
│
├── context/                      # React Context
│   └── AuthContext.tsx          # Authentication context
│
├── lib/                          # Utilities and configs
│   └── firebase.ts              # Firebase initialization
│
├── public/                       # Static files
│
├── .env.local                    # Firebase credentials
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
├── tailwind.config.js            # Tailwind CSS config
│
├── README.md                     # Main documentation
├── FIREBASE_SETUP.md            # Firebase setup guide
├── QUICK_START.md               # Quick start guide
├── AUTH_IMPLEMENTATION.md        # Implementation details
└── ARCHITECTURE.md              # This file
```

## Key Technologies

```
┌────────────────────────────────────────────────┐
│              Frontend Stack                     │
├────────────────────────────────────────────────┤
│ Next.js 16        - React framework            │
│ React 19          - UI library                 │
│ TypeScript        - Type safety                │
│ Tailwind CSS v4   - Styling                    │
│ Framer Motion     - Animations                 │
│ Lucide React      - Icons                      │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              Backend Stack                      │
├────────────────────────────────────────────────┤
│ Firebase Auth     - Authentication             │
│ Google OAuth 2.0  - Social login               │
│ Firestore         - Database                   │
│ Firebase Cloud    - Backend services           │
└────────────────────────────────────────────────┘
```

## Authentication Methods

```
┌─────────────────────────────────────────────┐
│   Firebase Authentication Methods            │
├─────────────────────────────────────────────┤
│                                             │
│ 1. Email/Password                          │
│    - createUserWithEmailAndPassword()       │
│    - signInWithEmailAndPassword()           │
│                                             │
│ 2. Google OAuth                            │
│    - signInWithPopup(auth, GoogleProvider) │
│    - Automatic account linking             │
│                                             │
│ 3. Session Management                      │
│    - onAuthStateChanged()                  │
│    - Firebase Auth tokens                  │
│    - Persistent sessions                   │
│                                             │
│ 4. Sign Out                                │
│    - signOut(auth)                         │
│    - Clears session                        │
│    - Clears local data                     │
│                                             │
└─────────────────────────────────────────────┘
```

## Environment Variables

```
.env.local
│
├── NEXT_PUBLIC_FIREBASE_API_KEY
│   └─ Safe to expose (public API key)
│
├── NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
│   └─ Safe to expose (domain identifier)
│
├── NEXT_PUBLIC_FIREBASE_PROJECT_ID
│   └─ Safe to expose (project identifier)
│
├── NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
│   └─ Safe to expose (storage bucket)
│
├── NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
│   └─ Safe to expose (messaging ID)
│
└── NEXT_PUBLIC_FIREBASE_APP_ID
    └─ Safe to expose (app identifier)

Note: All prefixed with NEXT_PUBLIC_ are safe for client-side code
```

---

## Quick Reference

| Component | Purpose | Location |
|-----------|---------|----------|
| AuthProvider | Wraps app with auth context | layout.tsx |
| useAuth() | Hook to access auth state | context/AuthContext.tsx |
| Navigation | Auth-aware navbar | components/Navigation.tsx |
| ProtectedRoute | Protects pages | components/ProtectedRoute.tsx |
| Firebase Config | SDK initialization | lib/firebase.ts |

---

This architecture provides:
✅ Secure authentication
✅ Global state management
✅ Protected routes
✅ Easy component integration
✅ Responsive UI
✅ Error handling
✅ Loading states
