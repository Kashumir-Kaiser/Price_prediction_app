/**
 * Admin dashboard with RBAC enforcement.
 */
import { useState, useEffect } from "react";
import { useGlobalStore } from "../store/useGlobalStore";
import { listUsers, updateUserRole, getTrafficStats } from "../api/admin";
import type { User, TrafficStats } from "../types";

export default function AdminPage() {
  const role = useGlobalStore((s) => s.role);
  const addToast = useGlobalStore((s) => s.addToast);

  const [users, setUsers] = useState<User[]>([]);
  const [traffic, setTraffic] = useState<TrafficStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (role !== "admin") return;

    const loadData = async () => {
      try {
        const [usersData, trafficData] = await Promise.all([
          listUsers(),
          getTrafficStats(7),
        ]);
        setUsers(usersData);
        setTraffic(trafficData);
      } catch (err: any) {
        addToast("error", "Failed to load admin data", err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [role, addToast]);

  const handleRoleChange = async (userId: number, newRole: "user" | "admin") => {
    try {
      const result = await updateUserRole(userId, newRole);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u))
      );
      addToast("info", "Role updated", result.message);
    } catch (err: any) {
      addToast("error", "Failed to update role", err.message);
    }
  };

  // Non-admin users see a 403-style message
  if (role !== "admin") {
    return (
      <div className="flex items-center justify-center h-screen" role="alert" aria-label="Access denied">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-red-600 mb-2">403</h1>
          <p className="text-gray-600">Administrator access required.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <>
          {/* Traffic Stats */}
          {traffic && (
            <div className="bg-white rounded-lg shadow p-6 mb-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Traffic (last {traffic.period_days} days)
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-500">Total Requests</p>
                  <p className="text-2xl font-bold text-gray-900">{traffic.total_requests.toLocaleString()}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-500">Avg Duration</p>
                  <p className="text-2xl font-bold text-gray-900">{traffic.avg_duration_ms}ms</p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-500">2xx</p>
                  <p className="text-2xl font-bold text-green-600">
                    {traffic.requests_by_status
                      .filter((s) => s.status_code >= 200 && s.status_code < 300)
                      .reduce((sum, s) => sum + s.count, 0)
                      .toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm text-gray-500">5xx</p>
                  <p className="text-2xl font-bold text-red-600">
                    {traffic.requests_by_status
                      .filter((s) => s.status_code >= 500)
                      .reduce((sum, s) => sum + s.count, 0)
                      .toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Users Table */}
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Users</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full" role="table" aria-label="Users list">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                    <th className="px-6 py-3">ID</th>
                    <th className="px-6 py-3">Username</th>
                    <th className="px-6 py-3">Email</th>
                    <th className="px-6 py-3">Role</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{user.id}</td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{user.username}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{user.email}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            user.role === "admin"
                              ? "bg-purple-100 text-purple-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            user.is_active
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {user.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={user.role}
                          onChange={(e) =>
                            handleRoleChange(user.id, e.target.value as "user" | "admin")
                          }
                          className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          aria-label={`Change role for ${user.username}`}
                        >
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
