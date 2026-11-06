import { defineConfig } from '@playwright/test'

// Humo contra `npm run dev` del frontend, que usa mocks (.env.development).
export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.ts',
  use: { baseURL: 'http://localhost:5173' },
  webServer: {
    command: 'npm run dev -- --port 5173 --strictPort',
    cwd: '../frontend',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
})
