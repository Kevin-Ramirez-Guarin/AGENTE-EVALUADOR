# Frontend — Portal del candidato y panel del reclutador (Nexo Digital)

Vite + React + TypeScript + Tailwind + React Router.

```bash
npm install
npm run dev        # http://localhost:5173 (/vacantes, /aplicar/:id, /privacidad, /panel, /panel/:id)
npm test           # Vitest + Testing Library
npm run build      # typecheck + build
cd ../e2e && npm install && npx playwright install chromium && npm test   # e2e (levanta backend con EVALUADOR=falso y BD temporal)
```

**API real por defecto:** `.env.development` trae `VITE_USE_MOCKS=false`, así que `npm run dev` necesita el backend en
`VITE_API_URL` (por defecto `http://localhost:8000`). Los mocks (JSON de `docs/api.md`) los usa Vitest; para el desarrollo
sin backend: `VITE_USE_MOCKS=true npm run dev`.

**E2E:** `e2e/playwright.config.ts` levanta el backend con `backend/.venv` (créalo e instala `backend/requirements.txt`),
`EVALUADOR=falso` y una BD SQLite temporal, más Vite en el 5173. Los puertos 8000 y 5173 deben estar libres.

**Panel (`/panel`):** demo sin autenticación; el nombre del reclutador se guarda en `localStorage`.
