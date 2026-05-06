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

export default app;
