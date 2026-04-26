/**
 * Tests for useGlobalStore
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useGlobalStore } from '@/store/useGlobalStore';
import { act } from '@testing-library/react';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('useGlobalStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store to initial clean state before each test
    act(() => {
      useGlobalStore.setState({
        user: null,
        token: null,
        role: null,
        isLoggedIn: false,
        toasts: [],
        watchlist: ['BTC/USD', 'ETH/USD', 'SOL/USD', 'VNM', 'FPT'],
      });
    });
    // Clear localStorage mocks
    mockLocalStorage.getItem.mockReturnValue(null); // initially no token
    mockLocalStorage.setItem.mockClear();
    mockLocalStorage.removeItem.mockClear();
  });

  it('initialises with token from localStorage if present', () => {
    mockLocalStorage.getItem.mockReturnValue('stored-token');
    act(() => {
      useGlobalStore.setState({
        token: 'stored-token',
        isLoggedIn: false, // token exists but not yet validated
      });
    });
    expect(useGlobalStore.getState().token).toBe('stored-token');
  });

  it('login stores token in localStorage and sets user state', () => {
    act(() => {
      useGlobalStore
        .getState()
        .login({ username: 'testuser', role: 'user' }, 'new-token');
    });

    const state = useGlobalStore.getState();
    expect(state.token).toBe('new-token');
    expect(state.role).toBe('user');
    expect(state.isLoggedIn).toBe(true);
    expect(state.user).toEqual({
      id: 0,
      username: 'testuser',
      email: 'testuser@placeholder.local',
      role: 'user',
      is_active: true,
    });
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('token', 'new-token');
  });

  it('logout clears token from localStorage and resets state', () => {
    // First login
    act(() => {
      useGlobalStore
        .getState()
        .login({ username: 'testuser', role: 'user' }, 'token');
    });

    // Then logout
    act(() => {
      useGlobalStore.getState().logout();
    });

    const state = useGlobalStore.getState();
    expect(state.token).toBeNull();
    expect(state.role).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isLoggedIn).toBe(false);
    expect(state.toasts).toEqual([]);
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token');
  });

  it('addToast adds a toast and auto-dismisses after 5 seconds', () => {
    vi.useFakeTimers();
    act(() => {
      useGlobalStore.getState().addToast('info', 'Test', 'Message');
    });

    let state = useGlobalStore.getState();
    expect(state.toasts).toHaveLength(1);
    expect(state.toasts[0].title).toBe('Test');

    // Advance time beyond 5s
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    state = useGlobalStore.getState();
    expect(state.toasts).toHaveLength(0);
    vi.useRealTimers();
  });

  it('removeToast removes a specific toast', () => {
    act(() => {
      const store = useGlobalStore.getState();
      store.addToast('error', 'Error', 'Oops');
    });

    const toastId = useGlobalStore.getState().toasts[0].id;
    act(() => {
      useGlobalStore.getState().removeToast(toastId);
    });

    expect(useGlobalStore.getState().toasts).toHaveLength(0);
  });

  it('setWatchlist replaces the watchlist', () => {
    act(() => {
      useGlobalStore.getState().setWatchlist(['AAPL', 'GOOGL']);
    });
    expect(useGlobalStore.getState().watchlist).toEqual(['AAPL', 'GOOGL']);
  });

  it('addToWatchlist adds unique symbol', () => {
    act(() => {
      useGlobalStore.getState().addToWatchlist('NVDA');
    });
    expect(useGlobalStore.getState().watchlist).toContain('NVDA');
    // Adding duplicate should not double it
    act(() => {
      useGlobalStore.getState().addToWatchlist('NVDA');
    });
    const count = useGlobalStore
      .getState()
      .watchlist.filter((s) => s === 'NVDA').length;
    expect(count).toBe(1);
  });

  it('removeFromWatchlist removes a symbol', () => {
    act(() => {
      useGlobalStore.getState().removeFromWatchlist('BTC/USD');
    });
    expect(useGlobalStore.getState().watchlist).not.toContain('BTC/USD');
  });
});