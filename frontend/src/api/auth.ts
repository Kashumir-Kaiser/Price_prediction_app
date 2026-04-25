/**Authentication API methods.*/
import { apiPost, apiGet } from "./client";
import type { LoginCredentials, TokenResponse, User } from "../types";

/**
 * Login and get JWT token.
 * Uses URL-encoded body for OAuth2PasswordRequestForm compatibility.
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || "/api/v1"}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

/**
 * Register a new user.
 */
export async function register(credentials: LoginCredentials & { email: string }): Promise<User> {
  return apiPost<User>("/auth/register", credentials);
}

/**
 * Get current user info.
 */
export async function getCurrentUser(): Promise<User> {
  return apiGet<User>("/auth/me");
}

/**
 * Store auth token in localStorage.
 */
export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

/**
 * Remove auth token from localStorage.
 */
export function clearToken(): void {
  localStorage.removeItem("token");
}

/**
 * Get stored token.
 */
export function getToken(): string | null {
  return localStorage.getItem("token");
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}
