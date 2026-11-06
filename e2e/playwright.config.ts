import { existsSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { defineConfig } from '@playwright/test'

// E2E de punta a punta: Vite (5173, sin mocks) + backend real con el evaluador falso
// y una BD SQLite temporal. El backend permite CORS solo desde el 5173.
const backend = path.resolve(__dirname, '../backend')
const venvPython = path.join(backend, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const python = existsSync(venvPython) ? venvPython : 'python'
const db = path.join(tmpdir(), 'agente-e2e.db')
const uploads = path.join(tmpdir(), 'agente-e2e-uploads')
// Los workers también cargan este archivo; solo el proceso principal limpia BD y PDFs.
if (!process.env.TEST_WORKER_INDEX) {
  rmSync(db, { force: true })
  rmSync(uploads, { recursive: true, force: true })
}

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.ts',
  use: { baseURL: 'http://localhost:5173' },
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --port 8000`,
      cwd: backend,
      url: 'http://localhost:8000/health',
      env: { EVALUADOR: 'falso', DATABASE_URL: `sqlite:///${db.replaceAll('\\', '/')}`, UPLOADS_DIR: uploads },
      reuseExistingServer: false,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      cwd: path.resolve(__dirname, '../frontend'),
      url: 'http://localhost:5173',
      env: { VITE_USE_MOCKS: 'false', VITE_API_URL: 'http://localhost:8000' },
      reuseExistingServer: false,
    },
  ],
})
