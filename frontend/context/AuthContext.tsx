'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api, clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken } from '@/lib/api';
import type { AuthUser, LoginPayload, SignupPayload } from '@/lib/types';

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<AuthUser>;
  signup: (payload: SignupPayload) => Promise<AuthUser>;
  logout: () => void;
  refreshUser: () => Promise<AuthUser | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    clearStoredAccessToken();
    setToken(null);
    setUser(null);
  }, []);

  const applySession = useCallback((accessToken: string, nextUser: AuthUser) => {
    setStoredAccessToken(accessToken);
    setToken(accessToken);
    setUser(nextUser);
  }, []);

  const refreshUser = useCallback(async () => {
    const storedToken = getStoredAccessToken();
    if (!storedToken) {
      clearSession();
      return null;
    }

    setToken(storedToken);
    try {
      const nextUser = await api.getMe(storedToken);
      setUser(nextUser);
      return nextUser;
    } catch {
      clearSession();
      return null;
    }
  }, [clearSession]);

  useEffect(() => {
    let cancelled = false;

    const loadSession = async () => {
      try {
        const storedToken = getStoredAccessToken();
        if (!storedToken) {
          if (!cancelled) {
            setToken(null);
            setUser(null);
          }
          return;
        }

        if (!cancelled) {
          setToken(storedToken);
        }

        const nextUser = await api.getMe(storedToken);
        if (!cancelled) {
          setUser(nextUser);
        }
      } catch {
        if (!cancelled) {
          clearSession();
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const response = await api.login(payload);
      applySession(response.access_token, response.user);
      return response.user;
    },
    [applySession],
  );

  const signup = useCallback(
    async (payload: SignupPayload) => {
      const response = await api.signup(payload);
      applySession(response.access_token, response.user);
      return response.user;
    },
    [applySession],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      signup,
      logout,
      refreshUser,
    }),
    [user, token, isLoading, login, signup, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider.');
  }
  return context;
}
