'use client';

import * as React from 'react';
import {
  type User,
  onAuthStateChanged,
  signInWithPopup,
  signOut as fbSignOut,
} from 'firebase/auth';
import { getFirebaseAuth, googleProvider, isFirebaseConfigured } from './firebase';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  configured: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);
  const configured = isFirebaseConfigured();

  React.useEffect(() => {
    if (!configured) {
      setLoading(false);
      return;
    }
    const unsub = onAuthStateChanged(getFirebaseAuth(), (u) => {
      setUser(u);
      setLoading(false);
    });
    return unsub;
  }, [configured]);

  const signInWithGoogle = React.useCallback(async () => {
    if (!configured) throw new Error('Firebase not configured.');
    await signInWithPopup(getFirebaseAuth(), googleProvider);
  }, [configured]);

  const signOut = React.useCallback(async () => {
    if (!configured) return;
    await fbSignOut(getFirebaseAuth());
  }, [configured]);

  const getIdToken = React.useCallback(async (): Promise<string | null> => {
    if (!configured) return null;
    const current = getFirebaseAuth().currentUser;
    return current ? current.getIdToken() : null;
  }, [configured]);

  const value: AuthContextValue = React.useMemo(
    () => ({ user, loading, configured, signInWithGoogle, signOut, getIdToken }),
    [user, loading, configured, signInWithGoogle, signOut, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
