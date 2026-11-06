# CLAUDE.md — Agente Evaluador

Reglas del proyecto para cualquier asistente de IA (y humano) que trabaje en este repo.

## Antes de tocar código
1. Lee `PLAN.md` (qué construimos, contratos, fases) y `docs/ESTADO.md` (quién hace qué, qué sigue).
2. Trabaja solo dentro de las carpetas de tu track (PLAN.md §10). Los contratos (`backend/app/models.py`, `backend/data/vacantes.json`, rutas de la API) solo cambian con PR revisado por los tres.

## Git
- Rama: `feature/<nombre-de-la-feature>` desde `main` actualizado. Nunca push directo a `main`.
- Commits pequeños y frecuentes (un paso lógico; si pasa de ~10 archivos, partirlo).
- Asunto: `feature/<accion-corta>` (ej. `feature/añadir-pdf`). Cuerpo: 1–3 frases en español, tono humano y profesional, qué hace y por qué.
- PR a `main`: CI verde + 1 revisión + `docs/ESTADO.md` actualizado.

## TDD
- Primero la prueba (commit `feature/test-...`, debe fallar), luego la implementación.
- Tipos de prueba y dónde viven: PLAN.md §11. Las pruebas que llaman a Gemini real llevan `@pytest.mark.llm` y no corren en CI.
- Cobertura ≥ 80 % en `backend/app`.

## Comandos
```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt
pytest                      # unitarias + caja negra (sin Gemini)
pytest -m llm               # evals con Gemini real (cuesta créditos)
uvicorn app.main:app --reload
# frontend
cd frontend && npm install && npm run dev
```

## Seguridad y datos
- Secretos solo en `backend/.env` (plantilla en `.env.example`). Nunca en código, commits, logs ni chat.
- Solo hojas de vida **sintéticas** en `samples/`. Las reales nunca se versionan (Ley 1581).
- El LLM nunca recibe datos de identidad: se anonimiza antes del agente.
- La IA recomienda; un humano aprueba antes de enviar correos o agendar.
