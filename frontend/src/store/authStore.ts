// Zustand-стор аутентификации: токены, пользователь, действия.

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import * as authApi from '../api/auth';
import type { LoginRequest, RegisterRequest, UserResponse } from '../types';

const ACCESS_KEY = 'aliaz_access_token';
const REFRESH_KEY = 'aliaz_refresh_token';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
  setTokens: (access: string, refresh: string) => void;
  fetchMe: () => Promise<void>;
}

function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: readStored(ACCESS_KEY),
      refreshToken: readStored(REFRESH_KEY),
      user: null,
      isAuthenticated: Boolean(readStored(ACCESS_KEY)),

      login: async (payload) => {
        const tokens = await authApi.login(payload);
        get().setTokens(tokens.access_token, tokens.refresh_token);
        await get().fetchMe();
      },

      register: async (payload) => {
        const tokens = await authApi.register(payload);
        get().setTokens(tokens.access_token, tokens.refresh_token);
        await get().fetchMe();
      },

      logout: () => {
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
      },

      setTokens: (access, refresh) => {
        localStorage.setItem(ACCESS_KEY, access);
        localStorage.setItem(REFRESH_KEY, refresh);
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
      },

      fetchMe: async () => {
        const user = await authApi.me();
        set({ user });
      },
    }),
    {
      name: 'aliaz-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);