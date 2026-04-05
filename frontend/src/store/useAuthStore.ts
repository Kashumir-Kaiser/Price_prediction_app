/**
 * Zustand store for authentication state management
 */
import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';

interface JWTPayload {
  sub: string;
  role: string;
  exp: number;
}

interface AuthState {
  token: string | null;
  role: string | null;
  username: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, role: string, username: string) => void;
  logout: () => void;
  checkAuth: () => boolean;
}

const STORAGE_KEY = 'auth_token';

const isTokenValid = (token: string | null): boolean => {
  if (!token) return false;
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    return decoded.exp * 1000 > Date.now();
  } catch {
    return false;
  }
};

// Load initial state from sessionStorage
const getInitialToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  const token = sessionStorage.getItem(STORAGE_KEY);
  return isTokenValid(token) ? token : null;
};

const getInitialRole = (): string | null => {
  if (typeof window === 'undefined') return null;
  const token = sessionStorage.getItem(STORAGE_KEY);
  if (!token || !isTokenValid(token)) return null;
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    return decoded.role;
  } catch {
    return null;
  }
};

const getInitialUsername = (): string | null => {
  if (typeof window === 'undefined') return null;
  const token = sessionStorage.getItem(STORAGE_KEY);
  if (!token || !isTokenValid(token)) return null;
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    return decoded.sub;
  } catch {
    return null;
  }
};

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getInitialToken(),
  role: getInitialRole(),
  username: getInitialUsername(),
  isAuthenticated: !!getInitialToken(),

  setAuth: (token: string, role: string, username: string) => {
    sessionStorage.setItem(STORAGE_KEY, token);
    set({ token, role, username, isAuthenticated: true });
  },

  logout: () => {
    sessionStorage.removeItem(STORAGE_KEY);
    set({ token: null, role: null, username: null, isAuthenticated: false });
  },

  checkAuth: () => {
    const { token } = get();
    const valid = isTokenValid(token);
    if (!valid && token) {
      // Token exists but is expired
      get().logout();
    }
    return valid;
  },
}));
