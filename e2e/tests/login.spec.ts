import { test, expect } from '../fixtures/auth';

test.describe('Login', () => {
  test('page elements are visible', async ({ authPage }) => {
    await authPage.gotoLogin();
    await expect(authPage.page.locator('h2')).toContainText('Login');
    await expect(authPage.page.locator('[data-testid="email-input"]')).toBeVisible();
    await expect(authPage.page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(authPage.page.locator('[data-testid="login-button"]')).toBeVisible();
    await expect(authPage.page.locator('[data-testid="register-link"]')).toBeVisible();
  });

  test('successful login redirects to dashboard', async ({ authPage, testUser }) => {
    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await expect(authPage.page).toHaveURL('/');
    await expect(authPage.page.locator('[data-testid="dashboard-welcome"]')).toBeVisible();
  });

  test('invalid credentials show error message', async ({ authPage }) => {
    await authPage.gotoLogin();
    await authPage.login('bad@example.com', 'wrongpassword');
    await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    await expect(authPage.page).toHaveURL('/login');
  });
});
