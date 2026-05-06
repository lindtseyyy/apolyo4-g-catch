import { db, auth } from '@/lib/firebase';
import {
  collection,
  addDoc,
  getDocs,
  query,
  where,
  orderBy,
  serverTimestamp,
  doc,
  deleteDoc,
} from 'firebase/firestore';

const COLLECTION = 'scans';

function userId() {
  const user = auth.currentUser;
  if (!user) throw new Error('User must be signed in to save scans');
  return user.uid;
}

export async function saveScan({ referenceNumber }) {
  const docRef = await addDoc(collection(db, COLLECTION), {
    userId: userId(),
    referenceNumber,
    createdAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function getScans() {
  const q = query(
    collection(db, COLLECTION),
    where('userId', '==', userId()),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
    createdAt: doc.data().createdAt?.toDate?.()?.toISOString() || null,
  }));
}

export async function checkReferenceExists(referenceNumber) {
  const q = query(
    collection(db, COLLECTION),
    where('referenceNumber', '==', referenceNumber)
  );
  const snapshot = await getDocs(q);
  return !snapshot.empty;
}

export async function deleteScan(id) {
  await deleteDoc(doc(db, COLLECTION, id));
}
