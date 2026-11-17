import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  use: {
    baseURL: 'http://127.0.0.1:5181',
    viewport: { width: 1440, height: 960 },
    channel: process.env.PLAYWRIGHT_CHANNEL,
  },
  webServer: [
    {
      command:
        '"' +
        (process.env.FLOWHARBOR_PYTHON ?? 'python') +
        '" -m uvicorn app.main:app --host 127.0.0.1 --port 8181',
      cwd: '../backend',
      url: 'http://127.0.0.1:8181/api/health',
      env: {
        FLOWHARBOR_SESSION_SECRET: 'browser-test-only-secret-never-use-in-deployment',
        FLOWHARBOR_PUBLIC_ORIGIN: 'http://127.0.0.1:5181',
        CRAWLAB_BASE_URL: 'http://127.0.0.1:1/api/',
      },
    },
    {
      command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5181',
      url: 'http://127.0.0.1:5181',
      env: { FLOWHARBOR_API_PROXY: 'http://127.0.0.1:8181' },
    },
  ],
})
