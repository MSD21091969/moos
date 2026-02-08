'use client';

/**
 * Auth Context
 *
 * Provides Firebase authentication state to the app.
 * Falls back to dev mode when Firebase is not configured.
 */
import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut as firebaseSignOut,
  GoogleAuthProvider,
  type User,
} from 'firebase/auth';
import { getFirebaseAuth, isFirebaseConfigured } from './firebase';
import { setAPIToken } from './api';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: Error | null;
  token: string | null;
  isDevMode: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps): React.ReactElement {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const isDevMode = !isFirebaseConfigured;

  useEffect(() => {
    // If Firebase is not configured, skip auth and use dev mode
    if (!isFirebaseConfigured) {
      console.log('[Auth] Running in dev mode - Firebase not configured');
      setLoading(false);
      // Use dev email as token (backend dev mode expects email format)
      const devToken = 'dev@localhost.test';
      setToken(devToken);
      setAPIToken(devToken);
      return;
    }

    const auth = getFirebaseAuth();
    if (!auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(
      auth,
      async (firebaseUser) => {
        setUser(firebaseUser);
        setLoading(false);

        if (firebaseUser) {
          try {
            const idToken = await firebaseUser.getIdToken();
            setToken(idToken);
            setAPIToken(idToken);
          } catch (err) {
            console.error('Failed to get ID token:', err);
            setToken(null);
            setAPIToken(undefined);
          }
        } else {
          setToken(null);
          setAPIToken(undefined);
        }
      },
      (err) => {
        setError(err);
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async (): Promise<void> => {
    if (isDevMode) {
      console.log('[Auth] Dev mode - skipping Google sign-in');
      return;
    }
    setError(null);
    const auth = getFirebaseAuth();
    if (!auth) return;
    const provider = new GoogleAuthProvider();

    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Sign-in failed'));
      throw err;
    }
  };

  const signOut = async (): Promise<void> => {
    if (isDevMode) {
      console.log('[Auth] Dev mode - skipping sign-out');
      return;
    }
    const auth = getFirebaseAuth();
    if (!auth) return;
    try {
      await firebaseSignOut(auth);
      setToken(null);
      setAPIToken(undefined);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Sign-out failed'));
      throw err;
    }
  };

  const value: AuthContextValue = {
    user,
    loading,
    error,
    token,
    isDevMode,
    signInWithGoogle,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
