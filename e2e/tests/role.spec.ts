import { test, expect, type UserRole } from '../fixtures/auth';

const roleTests: { role: UserRole; visible: string[]; hidden: string[] }[] = [
  {
    role: 'user',
    visible: ['dashboard-nav', 'watchlist-nav'],
    hidden: ['admin-panel-nav', 'premium-badge'],
  },
  {
    role: 'premium_user',
    visible: ['dashboard-nav', 'watchlist-nav', 'premium-badge'],
    hidden: ['admin-panel-nav'],
  },
  {
    role: 'admin',
    visible: ['dashboard-nav', 'watchlist-nav', 'admin-panel-nav'],
    hidden: ['premium-badge'],
  },
];

for (const tc of roleTests) {
  test.describe(`${tc.role} role`, () => {
    test('navigation elements match role', async ({ page }) => {
      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', `test_${tc.role}@example.com`);
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      await expect(page).toHaveURL('/dashboard');

      for (const el of tc.visible) {
        await expect(page.locator(`[data-testid="${el}"]`)).toBeVisible();
      }
      for (const el of tc.hidden) {
        await expect(page.locator(`[data-testid="${el}"]`)).toBeHidden();
      }
    });
  });
}
