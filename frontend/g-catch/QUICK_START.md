# 🚀 Quick Start Guide - Authentication System

## ⚡ 5-Minute Setup

### Step 1: Firebase Project Setup (2 min)
1. Go to https://console.firebase.google.com
2. Create a new project called "G-Catch"
3. When prompted, enable Google Analytics (optional)
4. Click "Continue"

### Step 2: Enable Authentication (1 min)
1. Go to **Build** → **Authentication** → **Get Started**
2. Click **Email/Password**
   - Toggle "Enable"
   - Click "Save"
3. Click **Google**
   - Toggle "Enable"
   - Select your email from dropdown
   - Click "Save"

### Step 3: Get Credentials (1 min)
1. Click the gear icon ⚙️ → **Project Settings**
2. Scroll to "Your apps" section
3. Click **</> (Web)** to add a web app
4. Name it "G-Catch" and click "Register app"
5. Copy the entire `firebaseConfig` object

### Step 4: Configure Environment (1 min)
1. In VS Code, open `.env.local` in the project root
2. Fill in your Firebase credentials:

```
NEXT_PUBLIC_FIREBASE_API_KEY=your_apiKey_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_authDomain_here
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_projectId_here
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_storageBucket_here
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_messagingSenderId_here
NEXT_PUBLIC_FIREBASE_APP_ID=your_appId_here
```

3. **Save the file**
4. **Restart the dev server** (`npm run dev`)

## 🎯 Testing the Authentication

### Start Development Server
```bash
npm run dev
```

Then open http://localhost:3000 in your browser.

### Test the Complete Flow

#### 1. Sign Up
- Click "Sign Up" button in top right
- Enter name, email, password
- Click "Create Account"
- Should redirect to home page

#### 2. Check Profile
- Click your name in top right → "Profile"
- See your email, UID, and account status
- Try signing out from the "Sign Out" button

#### 3. Sign In
- Click "Sign In" in top right
- Enter your email and password
- Click "Sign In"
- Should redirect to home page

#### 4. Google Sign-In (Optional)
- Go to `/signin` or `/signup`
- Click "Continue with Google"
- Choose your Google account
- Should sign in automatically

## 📱 Navigation Guide

| Page | URL | Description |
|------|-----|-------------|
| Home | `/` | Main scanner + auth nav |
| Sign In | `/signin` | Email/password or Google login |
| Sign Up | `/signup` | Create new account |
| Profile | `/profile` | View your information |

## 🔑 Key Features Implemented

✅ **Authentication**
- Email/password sign-up
- Email/password sign-in
- Google OAuth login
- Session persistence
- Sign out functionality

✅ **UI/UX**
- Modern dark theme
- Smooth animations
- Responsive design
- Form validation
- Error messages

✅ **Components**
- Navigation bar with auth status
- Protected route wrapper
- User profile page
- Authentication context hook

## 💻 Using Authentication in Your Code

### Check if User is Logged In
```typescript
'use client';
import { useAuth } from '@/context/AuthContext';

export default function MyComponent() {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <div>Please sign in</div>;

  return <div>Welcome, {user.email}!</div>;
}
```

### Protect a Page
```typescript
'use client';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function SecretPage() {
  return (
    <ProtectedRoute>
      <div>Only logged-in users see this</div>
    </ProtectedRoute>
  );
}
```

### Sign Out User
```typescript
'use client';
import { useAuth } from '@/context/AuthContext';

export default function SignOutButton() {
  const { logout } = useAuth();

  return (
    <button onClick={() => logout()}>
      Sign Out
    </button>
  );
}
```

## ❌ Troubleshooting

### "Cannot read properties of undefined"
**Problem**: Firebase is not initialized
**Fix**:
- Check `.env.local` has all Firebase credentials
- Restart dev server
- Clear `.next` folder: `rm -rf .next`
- Run `npm run dev` again

### Google sign-in not working
**Problem**: Unauthorized redirect URI
**Fix**:
1. Go to Firebase Console → Authentication
2. Click **Google** provider
3. Under "Authorized domains", add:
   - `localhost`
   - `localhost:3000`
4. Click Save

### "Email already in use"
**Problem**: Trying to sign up with existing email
**Fix**: Use a different email or sign in instead

### Page redirects to sign-in immediately
**Problem**: Protected page but not authenticated
**Fix**: Sign in first, then navigate to protected page

## 📚 Documentation Files

Read these for more details:
- **AUTH_IMPLEMENTATION.md** - Complete implementation details
- **FIREBASE_SETUP.md** - Detailed Firebase setup guide
- **README.md** - Full project documentation

## 🎨 Customization Ideas

Want to customize the auth system? Try:
- Change emerald accent color to blue/purple
- Add a remember me checkbox
- Add terms & conditions checkbox
- Add "forgot password" link
- Customize form validation rules
- Change the card styling

## 📞 Need Help?

1. Check `.env.local` is configured correctly
2. Make sure Firebase project is created
3. Check Firebase console for errors
4. Read FIREBASE_SETUP.md for detailed steps
5. Review browser console for JavaScript errors

## 🚀 Next Steps

1. ✅ Test the authentication system
2. ✅ Try all sign-in/sign-up flows
3. ✅ Visit your profile page
4. ✅ Test sign-out
5. 📝 Connect your main app to use authentication
6. 📝 Add more features (reset password, 2FA, etc.)

---

**Happy coding!** 🎉

If you have any issues, start with:
1. Check `.env.local`
2. Restart dev server
3. Clear browser cache
4. Read the error messages!
