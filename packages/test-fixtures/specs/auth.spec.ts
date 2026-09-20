import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test.describe('Authentication Flows', () => {
  test('successful user login sets session token and navigates to dashboard', async ({ page, context }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('qa-engineer@antigravity.internal', 'SuperSecret123!');
    await loginPage.expectLoginSuccess();

    // Verify authentication cookies/tokens
    const cookies = await context.cookies();
    const authCookie = cookies.find(c => c.name === 'auth_token' || c.name === 'session_id');
    expect(authCookie).toBeDefined();

    // Verify redirection
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('displays validation error banner on invalid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    await loginPage.login('unknown_user@antigravity.internal', 'WrongPassword!');
    await loginPage.expectErrorMessage('Invalid credentials. Please try again.');
  });
});

