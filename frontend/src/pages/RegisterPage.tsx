import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, User, Mail, TrendingUp, Moon, Sun } from 'lucide-react';
import { authApi } from '@/api/client';
import { useGlobalStore } from '@/store/useGlobalStore';
import { useThemeStore } from '@/store/useThemeStore';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { login: globalLogin } = useGlobalStore();
  const { theme, toggleTheme } = useThemeStore();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.register(username, email, password);
      const loginResponse = await authApi.login(username, password);
      globalLogin({ username, role: loginResponse.role as 'user' | 'admin' }, loginResponse.access_token);
      navigate('/', { replace: true });
    } catch (err: any) {
      if (err.status === 409) {
        setError('Username or email already taken');
      } else if (err.status === 422) {
        setError('Invalid input. Please check your details.');
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4 transition-colors relative">
      <button
        onClick={toggleTheme}
        className="absolute top-4 right-4 p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        aria-label="Toggle dark mode"
      >
        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
      </button>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-2xl w-full max-w-md p-8 transition-colors">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
          Register
        </h1>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-8">
          Sign up to start using the platform
        </p>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Choose a username"
                required
                minLength={3}
                maxLength={64}
                pattern="^[a-zA-Z0-9_]+$"
                title="Only letters, numbers, and underscores allowed"
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                id="email"
                data-testid="email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your email"
                required
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                id="password"
                data-testid="password-input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Create a password"
                required
                minLength={8}
                maxLength={128}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Confirm
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                id="confirmPassword"
                aria-label="Confirm Password"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Confirm your password"
                required
                minLength={8}
              />
            </div>
          </div>

          <button
            type="submit"
            data-testid="register-button"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-gray-600 dark:text-gray-400 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;