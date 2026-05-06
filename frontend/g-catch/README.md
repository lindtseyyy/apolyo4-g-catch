# G-Catch

**Forensic pixel analysis for GCash transaction verification** - Detect forged or anomalous receipt images with advanced AI-powered detection.

## 🎯 Features

### Core Features
- 📸 Upload receipt images for analysis
- 🔍 Real-time forensic pixel analysis
- ✅ Authentic/Forged detection results
- 🎨 Modern, sleek UI with Tailwind CSS
- ⚡ Smooth animations with Framer Motion

### Authentication Features
- 🔐 Secure Firebase authentication
- 📧 Email/Password sign-up and sign-in
- 🔑 Google OAuth 2.0 integration
- 👤 User profile management
- 🛡️ Session persistence
- 📱 Mobile-responsive design

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Firebase account

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd g-catch

# Install dependencies
npm install

# Set up Firebase (see FIREBASE_SETUP.md)
# Create .env.local with your Firebase credentials
```

### Firebase Configuration

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Email/Password and Google authentication
3. Copy your Firebase config
4. Create `.env.local` with:

```
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

See [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) for detailed setup instructions.

### Running the Application

```bash
# Development server
npm run dev

# Open http://localhost:3000 in your browser

# Production build
npm run build
npm start
```

## 📂 Project Structure

```
app/
├── layout.tsx              # Root layout with AuthProvider
├── page.tsx                # Home - main scanner
├── signin/
│   └── page.tsx            # Sign-in page
├── signup/
│   └── page.tsx            # Sign-up page
└── profile/
    └── page.tsx            # User profile page

components/
├── Navigation.tsx          # Top navigation bar
└── ProtectedRoute.tsx      # Protected page wrapper

context/
└── AuthContext.tsx         # Authentication state management

lib/
└── firebase.ts             # Firebase configuration

public/                     # Static assets
.env.local                 # Firebase credentials (create this)
```

## 🔑 Authentication System

### Sign Up
- Navigate to `/signup`
- Enter name, email, and password
- Password validation (minimum 6 characters)
- Automatic sign-in after account creation
- Google OAuth option available

### Sign In
- Navigate to `/signin`
- Email/password authentication
- "Show password" toggle for convenience
- Google OAuth option available
- Remember login session

### Profile
- View user information at `/profile`
- Display email and account status
- Sign out functionality
- View user UID

### Protected Pages
Use the `ProtectedRoute` component to protect pages:

```typescript
'use client';

import ProtectedRoute from '@/components/ProtectedRoute';

export default function SecurePage() {
  return (
    <ProtectedRoute>
      <div>This page is only visible to authenticated users</div>
    </ProtectedRoute>
  );
}
```

## 🎨 UI Components & Styling

- **Tailwind CSS v4** - Utility-first CSS framework
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icons
- **Dark Theme** - Modern dark mode design
- **Responsive** - Works on all devices

### Design Highlights
- Gradient backgrounds with glass morphism
- Smooth page transitions
- Interactive hover effects
- Loading states and skeletons
- Error message handling
- Form validation feedback

## 🛠️ Tech Stack

- **Framework**: Next.js 16
- **Runtime**: React 19
- **Styling**: Tailwind CSS v4
- **Authentication**: Firebase Auth
- **Database**: Firestore (optional)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Language**: TypeScript

## 📖 Usage Examples

### Using Authentication Hook

```typescript
'use client';

import { useAuth } from '@/context/AuthContext';

export default function MyComponent() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div>Loading...</div>;
  
  if (!user) return <div>Please sign in</div>;

  return (
    <div>
      <h1>Hello, {user.email}!</h1>
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

### Creating Protected Pages

```typescript
'use client';

import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      <div className="pt-24">
        <h1>Welcome to Dashboard</h1>
        <p>User: {user?.email}</p>
      </div>
    </ProtectedRoute>
  );
}
```

## 🔒 Security

- ✅ Firebase Security Rules configured
- ✅ CORS properly set up
- ✅ API keys are public but restricted
- ✅ No sensitive data in environment variables
- ✅ Password stored securely by Firebase
- ✅ Session tokens automatically managed

## 📱 Responsive Design

The app is fully responsive across:
- 📱 Mobile (320px+)
- 💻 Tablet (768px+)
- 🖥️ Desktop (1024px+)

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
# Follow prompts and add environment variables in dashboard
```

### Docker
```bash
docker build -t g-catch .
docker run -p 3000:3000 g-catch
```

### Firebase Hosting
```bash
npm install -g firebase-tools
firebase login
firebase deploy
```

## 🐛 Troubleshooting

**Q: Firebase config errors?**
- Verify all environment variables in `.env.local`
- Restart dev server after changes
- Check Firebase console for active project

**Q: Google Sign-In not working?**
- Ensure Google provider is enabled in Firebase
- Add localhost/your domain to authorized domains
- Clear browser cache and cookies

**Q: Forms not submitting?**
- Check browser console for error messages
- Verify Firebase credentials are correct
- Ensure email isn't already registered

**Q: Protected routes not working?**
- Make sure user is authenticated
- Check that ProtectedRoute is imported correctly
- Verify AuthProvider wraps the entire app

## 📚 Additional Resources

- [Firebase Docs](https://firebase.google.com/docs)
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [Framer Motion](https://www.framer.com/motion)
- [Lucide Icons](https://lucide.dev)

## 📝 Future Enhancements

- [ ] Email verification
- [ ] Password reset functionality
- [ ] Two-factor authentication
- [ ] User profile customization
- [ ] Admin dashboard
- [ ] Transaction history
- [ ] Advanced analytics
- [ ] Batch upload support

## 📄 License

This project is private and confidential.

## 👨‍💻 Support

For issues or questions, please check:
1. [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) - Firebase configuration guide
2. GitHub Issues
3. Firebase Console

---

**Last Updated**: May 6, 2026
