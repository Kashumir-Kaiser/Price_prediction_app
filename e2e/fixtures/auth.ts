import { test as base, expect, type Page } from '@playwright/test';

export type UserRole = 'user' | 'premium_user' | 'admin';

interface User {
  email: string;
  password: string;
  role: UserRole;
}

const TEST_USERS: Record<UserRole, User> = {
  user: {
    email: 'test_user@example.com',
    password: 'TestPassword123!',
    role: 'user',
  },
  premium_user: {
    email: 'test_premium@example.com',
    password: 'PremiumPass123!',
    role: 'premium_user',
  },
  admin: {
    email: 'test_admin@example.com',
    password: 'AdminPass123!',
    role: 'admin',
  },
};

type Fixtures = {
  authPage: AuthPage;
  testUser: User;
};

export class AuthPage {
  constructor(public page: Page) {}

  async gotoLogin() {
    await this.page.goto('/login');
    await expect(this.page.locator('[data-testid="login-form"]')).toBeVisible();
  }

  async gotoRegister() {
    await this.page.goto('/register');
    await expect(this.page.locator('[data-testid="register-form"]')).toBeVisible();
  }

  async login(email: string, password: string) {
    await this.page.fill('[data-testid="username-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="login-button"]');
  }

  async logout() {
    await this.page.click('[data-testid="logout-button"]');
    await expect(this.page.locator('[data-testid="login-form"]')).toBeVisible();
  }

  async register(email: string, password: string) {
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    await this.page.click('[data-testid="register-button"]');
  }
}

export const test = base.extend<Fixtures>({
  authPage: async ({ page }, use) => {
    await use(new AuthPage(page));
  },
  testUser: async ({}, use) => {
    await use(TEST_USERS.user);
  },
});

export { expect };
