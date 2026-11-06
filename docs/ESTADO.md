# Estado del proyecto

> Tablero vivo. **Cada PR actualiza este archivo.** Lo más reciente va arriba.

## En curso

| Quién | Rama | Tarea | Estado |
|---|---|---|---|
| JVarz12 (orquestador) | `feature/setup-base` | F0: estructura, contratos, CI, prueba de conexión con Gemini | En progreso |
| Kevin | — | Revisar contratos (PLAN.md §5–6) y vacantes | Pendiente |
| Santiago | — | Revisar contratos y rutas de la API | Pendiente |

## Siguiente (Sprint 1)
- **Kevin:** F1 (5 vacantes + 6–8 HV sintéticas en PDF) → F2 extracción PDF→JSON.
- **Santiago:** portal candidato (`/vacantes`, `/aplicar/:id`) con datos mock.
- **JVarz12:** API + BD con agente falso.

## Hecho
- 2026-11-06 · `.gitignore` y plan del proyecto v0.2 (equipo, sprints, pruebas, convenciones).

## Decisiones
- 2026-11-05 · LinkedIn solo como canal de publicación ("aplicar en sitio externo"); no hay scraping ni API (requiere partner).
- 2026-11-05 · La IA extrae y justifica; el puntaje lo calcula Python con reglas fijas.
- 2026-11-05 · Humano en el bucle: nada se envía sin aprobación del reclutador.
- 2026-11-05 · Gemini vía Vertex AI express mode (API key); modelo en `GEMINI_MODEL`.

## Bloqueos
- API key de Gemini (JVarz12) — necesaria para cerrar F0.
