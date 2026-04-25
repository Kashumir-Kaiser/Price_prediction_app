/**Admin API methods.*/
import { apiGet, apiPatch, apiPost } from "./client";
import type { User, TrafficStats } from "../types";

/**
 * List all users (admin only).
 */
export async function listUsers(): Promise<User[]> {
  return apiGet<User[]>("/admin/users");
}

/**
 * Update user role (admin only).
 */
export async function updateUserRole(
  userId: number,
  role: "user" | "admin"
): Promise<{ id: number; username: string; role: string; message: string }> {
  return apiPatch(`/admin/users/${userId}/role`, { role });
}

/**
 * Create user (admin only).
 */
export async function createUser(user: {
  username: string;
  email: string;
  password: string;
  role?: string;
  is_active?: boolean;
}): Promise<User> {
  return apiPost<User>("/admin/users", user);
}

/**
 * Get traffic statistics (admin only).
 */
export async function getTrafficStats(periodDays: number = 7): Promise<TrafficStats> {
  return apiGet<TrafficStats>(`/admin/traffic?period_days=${periodDays}`);
}
