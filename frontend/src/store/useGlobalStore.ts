/**
 * Global state management with Zustand.
 */
import { create } from "zustand";
import type { User, Toast, ToastType } from "../types";

interface GlobalState {
  // Auth state
  user: User | null;
  token: string | null;
  role: string | null;
  isLoggedIn: boolean;

  // Toast notifications
  toasts: Toast[];

  // Watchlist
  watchlist: string[];

  // Actions
  login: (user: User, token: string) => void;
  logout: () => void;
  addToast: (type: ToastType, title: string, message: string) => void;
  removeToast: (id: string) => void;
  setWatchlist: (symbols: string[]) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
}

let toastIdCounter = 0;

export const useGlobalStore = create<GlobalState>((set) => ({
  // Initial state
  user: null,
  token: localStorage.getItem("token"),
  role: null,
  isLoggedIn: false,
  toasts: [],
  watchlist: ["BTC/USD", "ETH/USD", "SOL/USD", "VNM", "FPT"],

  // Auth actions
  login: (user, token) => {
    localStorage.setItem("token", token);
    set({
      user,
      token,
      role: user.role,
      isLoggedIn: true,
    });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({
      user: null,
      token: null,
      role: null,
      isLoggedIn: false,
      toasts: [],
    });
  },

  // Toast actions
  addToast: (type, title, message) => {
    const id = `toast-${++toastIdCounter}-${Date.now()}`;
    set((state) => ({
      toasts: [...state.toasts, { id, type, title, message }],
    }));

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 5000);
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  // Watchlist actions
  setWatchlist: (symbols) => set({ watchlist: symbols }),

  addToWatchlist: (symbol) =>
    set((state) => ({
      watchlist: state.watchlist.includes(symbol)
        ? state.watchlist
        : [...state.watchlist, symbol],
    })),

  removeFromWatchlist: (symbol) =>
    set((state) => ({
      watchlist: state.watchlist.filter((s) => s !== symbol),
    })),
}));
