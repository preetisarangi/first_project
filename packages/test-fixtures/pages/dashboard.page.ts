import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly sidebarNav: Locator;
  readonly logoutButton: Locator;
  readonly metricsCards: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { level: 1 });
    this.sidebarNav = page.locator('nav[aria-label="Main Navigation"]');
    this.logoutButton = page.locator('button[data-testid="logout-btn"]');
    this.metricsCards = page.locator('[data-testid="metrics-card"]');
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async verifyHeading(expectedTitle: string) {
    await expect(this.heading).toHaveText(expectedTitle);
  }

  async logout() {
    await this.logoutButton.click();
    await this.page.waitForURL('**/login');
  }
}

