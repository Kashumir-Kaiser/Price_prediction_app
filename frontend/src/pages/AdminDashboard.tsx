/**
 * Admin dashboard page with traffic analytics
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Users,
  Activity,
  AlertCircle,
  Clock,
  Globe,
  UserX,
  RefreshCw,
  Shield,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { adminApi } from '@/api/client';
import { useAuthStore } from '@/store/useAuthStore';

interface OverviewStats {
  total_requests_today: number;
  unique_ips_today: number;
  avg_response_ms: number;
  error_rate_pct: number;
}

interface TrafficData {
  hour: string;
  requests: number;
  errors: number;
}

interface EndpointStat {
  path: string;
  hits: number;
  avg_duration_ms: number;
  error_rate_pct: number;
}

interface UserStat {
  username: string;
  requests_today: number;
  last_seen: string;
}

interface ErrorLog {
  method: string;
  path: string;
  status_code: number;
  duration_ms: number;
  logged_at: string;
}

interface UserItem {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { role, logout } = useAuthStore();

  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [traffic, setTraffic] = useState<TrafficData[]>([]);
  const [endpoints, setEndpoints] = useState<EndpointStat[]>([]);
  const [userStats, setUserStats] = useState<UserStat[]>([]);
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [overviewRes, trafficRes, endpointsRes, userStatsRes, errorsRes, usersRes] =
        await Promise.all([
          adminApi.getOverviewStats(),
          adminApi.getTrafficStats(),
          adminApi.getEndpointStats(),
          adminApi.getUserStats(),
          adminApi.getErrorLogs(),
          adminApi.getUsers(),
        ]);

      setOverview(overviewRes);
      setTraffic(trafficRes);
      setEndpoints(endpointsRes);
      setUserStats(userStatsRes);
      setErrors(errorsRes);
      setUsers(usersRes);
      setLastRefresh(new Date());
    } catch (err: any) {
      if (err.response?.status === 403) {
        // Not an admin
        navigate('/');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (role !== 'admin') {
      navigate('/');
      return;
    }
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [role, navigate]);

  const handleDeactivateUser = async (userId: number) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    try {
      await adminApi.deactivateUser(userId);
      fetchData();
    } catch (err) {
      alert('Failed to deactivate user');
    }
  };

  if (isLoading && !overview) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin">
          <RefreshCw className="w-8 h-8 text-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-sm text-gray-500">System analytics and user management</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
              <button
                onClick={fetchData}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-sm text-gray-500">Total Requests Today</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview?.total_requests_today.toLocaleString() || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Globe className="w-5 h-5 text-green-600" />
              </div>
              <span className="text-sm text-gray-500">Unique IPs Today</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview?.unique_ips_today.toLocaleString() || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <span className="text-sm text-gray-500">Avg Response Time</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview?.avg_response_ms.toFixed(1) || 0} ms
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              <span className="text-sm text-gray-500">Error Rate</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {overview?.error_rate_pct.toFixed(2) || 0}%
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Traffic Chart */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Traffic (Last 24h)</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={traffic}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="requests" stroke="#3b82f6" name="Requests" />
                  <Line type="monotone" dataKey="errors" stroke="#ef4444" name="Errors" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Error Feed */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Recent Errors</h2>
            <div className="h-64 overflow-y-auto">
              {errors.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No errors in the last 24 hours</p>
              ) : (
                <div className="space-y-2">
                  {errors.map((error, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-red-50 rounded-lg"
                    >
                      <div>
                        <span className="font-mono text-sm text-red-700">
                          {error.method} {error.path}
                        </span>
                        <p className="text-xs text-red-500">
                          {new Date(error.logged_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-red-200 text-red-800 text-xs rounded">
                        {error.status_code}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Endpoints Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Top Endpoints</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-sm font-medium text-gray-600">Endpoint</th>
                    <th className="text-right py-2 text-sm font-medium text-gray-600">Hits</th>
                    <th className="text-right py-2 text-sm font-medium text-gray-600">Avg (ms)</th>
                    <th className="text-right py-2 text-sm font-medium text-gray-600">Errors %</th>
                  </tr>
                </thead>
                <tbody>
                  {endpoints.map((ep, idx) => (
                    <tr key={idx} className="border-b border-gray-100">
                      <td className="py-2 text-sm text-gray-900 truncate max-w-[200px]">{ep.path}</td>
                      <td className="text-right py-2 text-sm text-gray-900">{ep.hits}</td>
                      <td className="text-right py-2 text-sm text-gray-900">
                        {ep.avg_duration_ms.toFixed(1)}
                      </td>
                      <td className="text-right py-2 text-sm text-gray-900">
                        {ep.error_rate_pct.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Active Users */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Active Users Today</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-sm font-medium text-gray-600">Username</th>
                    <th className="text-right py-2 text-sm font-medium text-gray-600">Requests</th>
                    <th className="text-right py-2 text-sm font-medium text-gray-600">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {userStats.map((user, idx) => (
                    <tr key={idx} className="border-b border-gray-100">
                      <td className="py-2 text-sm text-gray-900">{user.username}</td>
                      <td className="text-right py-2 text-sm text-gray-900">
                        {user.requests_today}
                      </td>
                      <td className="text-right py-2 text-sm text-gray-500">
                        {user.last_seen
                          ? new Date(user.last_seen).toLocaleTimeString()
                          : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* User Management */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">User Management</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Username</th>
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Email</th>
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Role</th>
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Status</th>
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Created</th>
                  <th className="text-right py-2 text-sm font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-gray-100">
                    <td className="py-2 text-sm text-gray-900">{user.username}</td>
                    <td className="py-2 text-sm text-gray-600">{user.email}</td>
                    <td className="py-2 text-sm">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          user.role === 'admin'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {user.role}
                      </span>
                    </td>
                    <td className="py-2 text-sm">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-2 text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="text-right py-2">
                      {user.role !== 'admin' && user.is_active && (
                        <button
                          onClick={() => handleDeactivateUser(user.id)}
                          className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                        >
                          <UserX className="w-4 h-4" />
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
