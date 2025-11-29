'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, User, ApiError } from './api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refreshUser = async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch (error) {
      console.error('[v0] Failed to fetch user:', error);
      localStorage.removeItem('accessToken');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await api.login(username, password);
    const token = response.token || response.access_token;
    
    if (token) {
      localStorage.setItem('accessToken', token);
      await refreshUser();
      router.push('/catalogue');
    }
  };

  const signup = async (data: any) => {
    const response = await api.signup(data);
    const token = response.token || response.access_token;
    
    if (token) {
      localStorage.setItem('accessToken', token);
      await refreshUser();
      router.push('/catalogue');
    } else {
      // Auto-login after signup
      await login(data.username, data.password);
    }
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    setUser(null);
    router.push('/auth');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
