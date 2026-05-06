# Firebase Authentication Setup Guide

This project now includes a complete authentication system with Firebase and Google Sign-In integration.

## Features

✨ **Modern Authentication System**
- Email/Password sign-up and sign-in
- Google OAuth 2.0 integration
- Persistent authentication state
- Responsive mobile-friendly UI
- Beautiful Tailwind CSS design with animations
- Password validation and strength indicators

## Getting Started

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Create a new project"
3. Enter your project name (e.g., "G-Catch")
4. Follow the setup wizard
5. Enable Google Analytics (optional)

### 2. Set Up Authentication

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Enable **Email/Password**:
   - Click on "Email/Password"
   - Toggle **Enable**
   - Click **Save**

3. Enable **Google**:
   - Click on "Google"
   - Toggle **Enable**
   - Select your support email from dropdown
   - Add your project public name
   - Click **Save**

### 3. Get Your Firebase Credentials

1. Go to **Project Settings** (gear icon)
2. Click on **Your apps** or scroll to find your app
3. If no app exists, click **Add app** and select **Web** (`</>`))
4. Copy the Firebase config object
5. You'll see something like:

```javascript
{
  apiKey: "your_api_key",
  authDomain: "your_project.firebaseapp.com",
  projectId: "your_project_id",
  storageBucket: "your_project.appspot.com",
  messagingSenderId: "your_sender_id",
  appId: "your_app_id"
}
```

### 4. Configure Environment Variables

1. Open `.env.local` in the project root
2. Fill in the values from your Firebase config:

```
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

### 5. Configure Google OAuth Redirect URLs

1. In Firebase Console, go to **Authentication** → **Sign-in method** → **Google**
2. Under "Authorized domains", add:
   - `localhost` (for development)
   - Your production domain (when deployed)

## Running the Application

```bash
# Install dependencies (already done)
npm install

# Run development server
npm run dev

# Open in browser
# http://localhost:3000
```

## File Structure

```
app/
├── signin/
│   └── page.tsx          # Sign-in page
├── signup/
│   └── page.tsx          # Sign-up page
├── page.tsx              # Home page with nav integration
└── layout.tsx            # Root layout with AuthProvider

context/
└── AuthContext.tsx       # Auth state management

components/
└── Navigation.tsx        # Navigation bar with auth links

lib/
└── firebase.ts           # Firebase configuration

.env.local               # Environment variables (create this)
```

## Usage

### Access Authentication State

Use the `useAuth` hook in any component:

```typescript
'use client';

import { useAuth } from '@/context/AuthContext';

export default function MyComponent() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div>Loading...</div>;

  if (user) {
    return <div>Welcome, {user.email}!</div>;
  }

  return <div>Please sign in</div>;
}
```

### Authentication Methods

**Sign Up with Email:**
- Navigate to `/signup`
- Enter name, email, and password
- Form validates password strength

**Sign In with Email:**
- Navigate to `/signin`
- Enter email and password
- Click "Sign In"

**Sign In with Google:**
- Click "Continue with Google"
- Authenticate with your Google account
- Automatically redirected to home page

**Sign Out:**
- Click "Sign Out" in the navigation bar

## Security Notes

⚠️ **Important:**
- All Firebase API keys are prefixed with `NEXT_PUBLIC_`, which means they're safe to expose in the browser (Firebase uses security rules)
- Never expose your Firebase admin SDK keys
- Set up proper Firestore/Database rules in your Firebase Console
- Enable CORS properly for your domains

## Troubleshooting

### "Firebase configuration error"
- Check that all environment variables in `.env.local` are correct
- Restart the dev server after updating `.env.local`

### "Google authentication not working"
- Verify Google is enabled in Firebase Authentication settings
- Check that your domain is in the authorized domains list
- Clear browser cookies and try again

### "Email already in use"
- This Firebase error means the email is already registered
- Try signing in instead or use a different email

## Next Steps

1. ✅ Add Firebase authentication
2. ✅ Create sign-in/sign-up pages
3. ✅ Add Google OAuth integration
4. 📝 Consider adding:
   - User profile page
   - Password reset functionality
   - Email verification
   - Two-factor authentication
   - User profile in Firestore database

## Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Next.js Documentation](https://nextjs.org/docs)

---

Happy authenticating! 🔐
