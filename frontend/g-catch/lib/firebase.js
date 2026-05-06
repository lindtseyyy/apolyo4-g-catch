import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Replace with your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyAqTepfIAagg1mKV6J-OHVrTcXd5vpTeyM",
  authDomain: "g-catch.firebaseapp.com",
  projectId: "g-catch",
  storageBucket: "g-catch.firebasestorage.app",
  messagingSenderId: "695822600606",
  appId: "1:695822600606:web:54a43737f5382fac6f2e8f",
  measurementId: "G-CWMJTDF58N"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

const authErrorMap = {
  'auth/invalid-credential': 'Incorrect email or password. Please try again.',
  'auth/user-not-found': 'No account found with this email address.',
  'auth/wrong-password': 'Incorrect password. Please try again.',
  'auth/invalid-email': 'Please enter a valid email address.',
  'auth/too-many-requests': 'Too many attempts. Please wait a moment and try again.',
  'auth/email-already-in-use': 'An account with this email already exists.',
  'auth/weak-password': 'Password is too weak. Please choose a stronger one.',
  'auth/network-request-failed': 'A network error occurred. Please check your connection.',
  'auth/popup-closed-by-user': 'Sign-in popup was closed. Please try again.',
  'auth/popup-blocked': 'Sign-in popup was blocked by your browser.',
  'auth/cancelled-popup-request': 'Sign-in was cancelled.',
  'auth/account-exists-with-different-credential': 'An account already exists with the same email using a different sign-in method.',
  'auth/user-disabled': 'This account has been disabled.',
};

export function getAuthErrorMessage(err) {
  if (err?.code && authErrorMap[err.code]) {
    return authErrorMap[err.code];
  }
  return err?.message || 'An unexpected error occurred. Please try again.';
}

export default app;
