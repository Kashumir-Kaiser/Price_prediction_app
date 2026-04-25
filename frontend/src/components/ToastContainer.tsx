/**Toast notification container component.*/
import { useGlobalStore } from "../store/useGlobalStore";
import type { ToastType } from "../types";

const typeStyles: Record<ToastType, { bg: string; icon: string }> = {
  error: { bg: "#fef2f2", icon: "bg-red-500" },
  warning: { bg: "#fffbeb", icon: "bg-yellow-500" },
  info: { bg: "#eff6ff", icon: "bg-blue-500" },
};

export default function ToastContainer() {
  const toasts = useGlobalStore((s) => s.toasts);
  const removeToast = useGlobalStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 rounded-lg p-4 shadow-lg border max-w-sm`}
          style={{
            backgroundColor: typeStyles[toast.type].bg,
            borderColor: typeStyles[toast.type].bg.replace("f2", "e5"),
          }}
          role="alert"
          aria-live="polite"
        >
          <div
            className={`w-1.5 h-full rounded-full ${typeStyles[toast.type].icon}`}
            style={{ minHeight: "40px" }}
          />
          <div className="flex-1">
            <p className="font-semibold text-sm text-gray-900">{toast.title}</p>
            <p className="text-sm text-gray-600 mt-0.5">{toast.message}</p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-gray-400 hover:text-gray-600 text-lg leading-none"
            aria-label={`Dismiss ${toast.title} notification`}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
