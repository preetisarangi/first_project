import { type Page, type Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly userAvatar: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('input[data-testid="username-input"], input[name="username"]');
    this.passwordInput = page.locator('input[data-testid="password-input"], input[name="password"]');
    this.submitButton = page.locator('button[type="submit"], button[data-testid="login-submit"]');
    this.errorMessage = page.locator('[data-testid="auth-error-alert"], .error-banner');
    this.userAvatar = page.locator('[data-testid="user-profile-avatar"]');
  }

  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectLoginSuccess() {
    await expect(this.userAvatar).toBeVisible({ timeout: 5000 });
  }

  async expectErrorMessage(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }
}

