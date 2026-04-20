/**
 * AuthContext — manages user identity across the app.
 *
 * In Telegram Mini App mode: extracts user from initDataUnsafe.
 * In standalone browser mode: falls back to demo user (id=1).
 * Sets initData on the API client for authenticated requests.
 */

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react';

import { api } from '@/api/client';

interface TelegramUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
}

interface AuthContextValue {
  /** Database user id (Telegram user id or fallback). */
  userId: number;
  /** Telegram username (if available). */
  username: string;
  /** Whether running inside Telegram Mini App. */
  isTelegram: boolean;
  /** Whether the user is authenticated (always true for now). */
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  userId: 1,
  username: 'guest',
  isTelegram: false,
  isAuthenticated: false,
});

function getTelegramUser(): TelegramUser | null {
  try {
    const tg = window.Telegram?.WebApp;
    if (tg?.initDataUnsafe?.user?.id) {
      return tg.initDataUnsafe.user as TelegramUser;
    }
  } catch {
    // Not in Telegram context
  }
  return null;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const value = useMemo<AuthContextValue>(() => {
    const tgUser = getTelegramUser();

    if (tgUser) {
      return {
        userId: tgUser.id,
        username: tgUser.username ?? tgUser.first_name ?? `user_${tgUser.id}`,
        isTelegram: true,
        isAuthenticated: true,
      };
    }

    // Standalone browser mode — demo user
    return {
      userId: 1,
      username: 'demo',
      isTelegram: false,
      isAuthenticated: true,
    };
  }, []);

  // Set initData on API client for Telegram auth
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg?.initData) {
      api.setInitData(tg.initData);
    }
  }, []);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
