/**
 * API client for backend communication
 */
import type { Prediction } from "@/types/market";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function getToken(): string | null {
  return localStorage.getItem("token");
}

export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

export async function apiPost<T>(
  endpoint: string,
  body: unknown,
  options: RequestInit = {}
): Promise<T> {
  const response = await apiFetch(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

export async function apiGet<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await apiFetch(endpoint, {
    method: "GET",
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

export async function apiPatch<T>(
  endpoint: string,
  body: unknown,
  options: RequestInit = {}
): Promise<T> {
  const response = await apiFetch(endpoint, {
    method: "PATCH",
    body: JSON.stringify(body),
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

export async function apiDelete<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await apiFetch(endpoint, {
    method: "DELETE",
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }

  return response.json();
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export const authApi = {
  async login(username: string, password: string): Promise<{ access_token: string; role: string }> {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch(`${API_BASE}/auth/login`, {
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
      throw new ApiError(response.status, error.detail || "Login failed");
    }

    return response.json();
  },

  async register(username: string, email: string, password: string): Promise<any> {
    return apiPost("/auth/register", { username, email, password });
  },
};

export const pricesApi = {
  async getCryptoHistory(symbol: string, _timeframe: string, start?: string, end?: string): Promise<{ data: any[] }> {
    const params = new URLSearchParams();
    params.append("symbol", symbol);
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    return apiGet(`/prices?${params.toString()}`);
  },

  async getStockHistory(symbol: string, start?: string, end?: string): Promise<{ data: any[] }> {
    const params = new URLSearchParams();
    params.append("symbol", symbol);
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    return apiGet(`/prices?${params.toString()}`);
  },

  async getStockFinancials(_symbol: string): Promise<{ data: any | null }> {
    // Financial endpoint is not yet available in backend.
    return { data: null };
  },
};

export const predictionsApi = {
  async getCryptoPrediction(symbol: string, model: string): Promise<Prediction> {
    return apiGet(`/predictions?symbol=${encodeURIComponent(symbol)}&model=${encodeURIComponent(model)}`);
  },
  async getStockPrediction(symbol: string, model: string): Promise<Prediction> {
    return apiGet(`/predictions?symbol=${encodeURIComponent(symbol)}&model=${encodeURIComponent(model)}`);
  },
};

export const adminApi = {
  async getUsers(): Promise<any[]> {
    return apiGet("/admin/users");
  },
  async getTrafficStats(periodDays: number = 7): Promise<any> {
    return apiGet(`/admin/traffic?period_days=${periodDays}`);
  },
  async updateUserRole(userId: number, role: "user" | "admin"): Promise<any> {
    return apiPatch(`/admin/users/${userId}/role`, { role });
  },

  // Backward-compatible aliases used by current dashboard.
  async listUsers(): Promise<any[]> {
    return this.getUsers();
  },
  async getOverviewStats(): Promise<any> {
    return this.getTrafficStats();
  },
  async getEndpointStats(): Promise<any[]> {
    return [];
  },
  async getUserStats(): Promise<any[]> {
    return [];
  },
  async getErrorLogs(): Promise<any[]> {
    return [];
  },
  async deactivateUser(userId: number): Promise<any> {
    return apiPatch(`/admin/users/${userId}/role`, { role: "user" });
  },
};