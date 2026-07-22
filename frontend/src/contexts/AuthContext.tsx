import React, { createContext, useState, useEffect, useCallback } from 'react';
import { verifyToken } from '../services/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => void;
  setAuthenticated: (value: boolean) => void;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  logout: () => {},
  setAuthenticated: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const token = localStorage.getItem('access_token');
    if (token) {
      verifyToken().then((valid) => {
        if (cancelled) return;
        setAuthenticated(valid);
        setIsLoading(false);
        if (!valid) localStorage.removeItem('access_token');
      });
    } else {
      setIsLoading(false);
    }
    return () => { cancelled = true; };
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, logout, setAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}
