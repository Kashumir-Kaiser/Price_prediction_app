import { useState, useEffect } from 'react';
import { useGlobalStore } from '../store/useGlobalStore';
import { useThemeStore } from '../store/useThemeStore';
import { listUsers, updateUserRole, getTrafficStats } from '../api/admin';
import type { User, TrafficStats } from '../types';
import { Moon, Sun } from 'lucide-react';

export default function AdminPage() {
  const role = useGlobalStore((s) => s.role);
  const addToast = useGlobalStore((s) => s.addToast);
  const { theme, toggleTheme } = useThemeStore();

  const [users, setUsers] = useState<User[]>([]);
  const [traffic, setTraffic] = useState<TrafficStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (role !== 'admin') return;

    const loadData = async () => {
      try {
        const [usersData, trafficData] = await Promise.all([
          listUsers(),
          getTrafficStats(7),
        ]);
        setUsers(usersData);
        setTraffic(trafficData);
      } catch (err: any) {
        addToast('error', 'Failed to load admin data', err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [role, addToast]);

  const handleRoleChange = async (userId: number, newRole: 'user' | 'admin') => {
    try {
      const result = await updateUserRole(userId, newRole);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u)));
      addToast('info', 'Role updated', result.message);
    } catch (err: any) {
      addToast('error', 'Failed to update role', err.message);
    }
  };

  if (role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900" role="alert">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-red-600 mb-2">403</h1>
          <p className="text-gray-600 dark:text-gray-400">Administrator access required.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 max-w-6xl mx-auto transition-colors">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          aria-label="Toggle dark mode"
        >
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500 dark:text-gray-400">Loading...</p>
      ) : (
        <>
          {traffic && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Traffic (last {traffic.period_days} days)
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total Requests</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{traffic.total_requests.toLocaleString()}</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Avg Duration</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{traffic.avg_duration_ms}ms</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded">
                  <p className="text-sm text-gray-500 dark:text-gray-400">2xx</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {traffic.requests_by_status
                      .filter((s) => s.status_code >= 200 && s.status_code < 300)
                      .reduce((sum, s) => sum + s.count, 0)
                      .toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded">
                  <p className="text-sm text-gray-500 dark:text-gray-400">5xx</p>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400">
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
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 transition-colors">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Users</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full" role="table" aria-label="Users list">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-700 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    <th className="px-6 py-3">ID</th>
                    <th className="px-6 py-3">Username</th>
                    <th className="px-6 py-3">Email</th>
                    <th className="px-6 py-3">Role</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{user.id}</td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{user.username}</td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{user.email}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            user.role === 'admin'
                              ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            user.is_active
                              ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300'
                              : 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                          }`}
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={user.role}
                          onChange={(e) => handleRoleChange(user.id, e.target.value as 'user' | 'admin')}
                          className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
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