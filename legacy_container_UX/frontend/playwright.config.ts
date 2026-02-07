import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000, // Reduced from 60s to 30s
  expect: { timeout: 5000 },
  fullyParallel: true,
  workers: 12,
  retries: process.env.CI ? 1 : 0,
  // Use 'line' reporter for CI/terminal - doesn't wait for user input
  // HTML report is generated but doesn't block
  reporter: process.env.CI ? [['line'], ['json', { outputFile: 'test-results.json' }]] 
    : [['line'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5174',
    trace: process.env.CI ? 'on-first-retry' : 'off',
    screenshot: 'only-on-failure',
    video: process.env.CI ? 'retain-on-failure' : 'off',
  },
  webServer: {
    command: 'npm run dev:demo',
    url: 'http://localhost:5174',
    reuseExistingServer: true,
    timeout: 120000,
  },
  projects: [
    {
      name: 'msedge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
  ],
});
