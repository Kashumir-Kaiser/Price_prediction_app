import { test, expect } from '../fixtures/auth';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ authPage, testUser }) => {
    await authPage.gotoLogin();
    await authPage.login(testUser.email, testUser.password);
    await expect(authPage.page).toHaveURL('/');
  });

  test('dashboard loads with chart', async ({ authPage }) => {
    await authPage.page.click('[data-testid="asset-btc-usd"]');
    await expect(authPage.page.locator('[data-testid="market-overview-chart"]')).toBeVisible();
  });

  test('symbol search filters data', async ({ authPage }) => {
    await authPage.page.fill('[data-testid="symbol-search"]', 'BTC/USD');
    await authPage.page.click('[data-testid="search-button"]');
    await expect(authPage.page.locator('[data-testid="symbol-title"]')).toContainText('BTC/USD');
    await expect(authPage.page.locator('[data-testid="market-overview-chart"]')).toBeVisible();
  });
});
