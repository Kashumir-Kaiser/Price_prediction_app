/**Login page tests -- no timing-dependent assertions.*/
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "../LoginPage";

// Mock the API and store modules
vi.mock("../../api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
  setToken: vi.fn(),
}));

vi.mock("../../store/useGlobalStore", () => ({
  useGlobalStore: vi.fn(() => ({
    login: vi.fn(),
    addToast: vi.fn(),
  })),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows username and password inputs", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("toggles between login and register mode", () => {
    render(<LoginPage />);

    // Initially shows login
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();

    // Click register toggle
    fireEvent.click(screen.getByRole("button", { name: /switch to registration/i }));

    // Now shows register
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it("submits form with credentials", async () => {
    const { login } = await import("../../api/auth");
    vi.mocked(login).mockResolvedValue({
      access_token: "test_token",
      token_type: "bearer",
      role: "user",
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: "testuser" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "testpass123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        username: "testuser",
        password: "testpass123",
      });
    });
  });
});
