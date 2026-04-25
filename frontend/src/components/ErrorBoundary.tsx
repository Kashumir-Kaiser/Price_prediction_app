/**React error boundary with fallback UI.*/
import React, { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * GlobalErrorBoundary catches React rendering errors in any child component.
 * Displays a user-friendly fallback UI instead of a white screen.
 *
 * Usage: Wrap top-level routes:
 *   <GlobalErrorBoundary>
 *     <AppRoutes />
 *   </GlobalErrorBoundary>
 */
export class GlobalErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error tracking service (Sentry, etc.)
    console.error("[ErrorBoundary] Caught error:", error);
    console.error("[ErrorBoundary] Component stack:", errorInfo.componentStack);

    // In production, send to error tracking:
    // Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          aria-label="Application error"
          style={{
            padding: "2rem",
            maxWidth: "600px",
            margin: "4rem auto",
            textAlign: "center",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h1 style={{ color: "#dc2626", fontSize: "1.5rem", marginBottom: "1rem" }}>
            Something went wrong
          </h1>
          <p style={{ color: "#6b7280", marginBottom: "2rem" }}>
            An unexpected error occurred. Our team has been notified.
          </p>
          {this.state.error && (
            <pre
              style={{
                background: "#f3f4f6",
                padding: "1rem",
                borderRadius: "0.5rem",
                fontSize: "0.875rem",
                overflow: "auto",
                textAlign: "left",
                marginBottom: "2rem",
              }}
            >
              {this.state.error.message}
            </pre>
          )}
          <button
            onClick={this.handleRetry}
            style={{
              padding: "0.5rem 1.5rem",
              background: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "0.375rem",
              cursor: "pointer",
              fontSize: "1rem",
            }}
            aria-label="Reload application"
          >
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
