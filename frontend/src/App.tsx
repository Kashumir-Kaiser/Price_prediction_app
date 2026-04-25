/**Root app component with error boundary, routing, and toast notifications.*/
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useGlobalStore } from "./store/useGlobalStore";
import { GlobalErrorBoundary } from "./components/ErrorBoundary";
import ToastContainer from "./components/ToastContainer";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import ModelPage from "./pages/ModelPage";
import AdminPage from "./pages/AdminPage";

// Create react-query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes default stale time
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * Protected route: redirect to /login if not authenticated.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isLoggedIn = useGlobalStore((s) => s.isLoggedIn);

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/**
 * Admin route: redirect to / if not admin.
 */
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, role } = useGlobalStore((s) => ({
    isLoggedIn: s.isLoggedIn,
    role: s.role,
  }));

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  if (role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <GlobalErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/models"
              element={
                <ProtectedRoute>
                  <ModelPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminPage />
                </AdminRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <ToastContainer />
      </GlobalErrorBoundary>
    </QueryClientProvider>
  );
}
