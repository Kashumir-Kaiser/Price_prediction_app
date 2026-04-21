import { test, expect } from '../fixtures/auth';

test.describe('Registration', () => {
  test('register new account', async ({ authPage }) => {
    await authPage.gotoRegister();
    const email = `e2e_${Date.now()}@example.com`;
    await authPage.register(email, 'TestPassword123!');
    await expect(authPage.page.locator('[data-testid="success-message"]')).toContainText('Registration successful');
    await expect(authPage.page).toHaveURL('/login');
  });

  test('duplicate email shows error', async ({ authPage, testUser }) => {
    await authPage.gotoRegister();
    await authPage.register(testUser.email, 'TestPassword123!');
    await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText('Email already registered');
  });
});
