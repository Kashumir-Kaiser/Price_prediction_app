import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useGlobalStore } from '@/store/useGlobalStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAdmin = false,
}) => {
  const { isLoggedIn, role } = useGlobalStore();
  const location = useLocation();

  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">Administrator access required.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};