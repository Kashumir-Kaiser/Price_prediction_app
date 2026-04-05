/**
 * Tests for useAuthStore
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '@/store/useAuthStore';
import { act } from '@testing-library/react';

// Mock jwt-decode
vi.mock('jwt-decode', () => ({
  jwtDecode: (token: string) => {
    if (token === 'valid_token') {
      return { sub: 'testuser', role: 'user', exp: Date.now() / 1000 + 3600 };
    }
    if (token === 'expired_token') {
      return { sub: 'testuser', role: 'user', exp: Date.now() / 1000 - 3600 };
    }
    throw new Error('Invalid token');
  },
}));

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

describe('useAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    act(() => {
      useAuthStore.setState({
        token: null,
        role: null,
        username: null,
        isAuthenticated: false,
      });
    });
  });

  it('initializes with null values', () => {
    const state = useAuthStore.getState();

    expect(state.token).toBeNull();
    expect(state.role).toBeNull();
    expect(state.username).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('setAuth stores token, role, and username', () => {
    act(() => {
      useAuthStore.getState().setAuth('valid_token', 'user', 'testuser');
    });

    const state = useAuthStore.getState();
    expect(state.token).toBe('valid_token');
    expect(state.role).toBe('user');
    expect(state.username).toBe('testuser');
    expect(state.isAuthenticated).toBe(true);
    expect(mockSessionStorage.setItem).toHaveBeenCalledWith('auth_token', 'valid_token');
  });

  it('logout clears all fields and removes sessionStorage', () => {
    act(() => {
      useAuthStore.getState().setAuth('valid_token', 'user', 'testuser');
    });

    act(() => {
      useAuthStore.getState().logout();
    });

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.role).toBeNull();
    expect(state.username).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('auth_token');
  });

  it('checkAuth returns true for valid token', () => {
    act(() => {
      useAuthStore.getState().setAuth('valid_token', 'user', 'testuser');
    });

    const result = useAuthStore.getState().checkAuth();
    expect(result).toBe(true);
  });

  it('checkAuth returns false and logs out for expired token', () => {
    act(() => {
      useAuthStore.setState({
        token: 'expired_token',
        role: 'user',
        username: 'testuser',
        isAuthenticated: true,
      });
    });

    const result = useAuthStore.getState().checkAuth();
    expect(result).toBe(false);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
