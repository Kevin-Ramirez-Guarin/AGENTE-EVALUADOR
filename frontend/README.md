# Frontend — Portal del candidato (Nexo Digital)

Vite + React + TypeScript + Tailwind + React Router.

```bash
npm install
npm run dev        # http://localhost:5173 (/vacantes, /aplicar/:id, /privacidad)
npm test           # Vitest + Testing Library
npm run build      # typecheck + build
cd ../e2e && npm install && npx playwright install chromium && npm test   # humo e2e
```

**Mocks:** `.env.development` trae `VITE_USE_MOCKS=true`, así `src/api.ts` responde con los JSON de `docs/api.md`
sin backend. Para usar la API real pon `VITE_USE_MOCKS=false` (o quítala) y `VITE_API_URL` (por defecto `http://localhost:8000`).
