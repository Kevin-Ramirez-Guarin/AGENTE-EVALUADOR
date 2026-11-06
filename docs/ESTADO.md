# Estado del proyecto

> Tablero vivo. **Cada PR actualiza este archivo.** Lo más reciente va arriba.

## En curso: Sprint 1 terminado, falta revisar y fusionar

| Track | Rama | Qué trae | Pruebas | Siguiente paso |
|---|---|---|---|---|
| Base | `feature/setup-base` | F0, guía `ONBOARDING.md` y este tablero | 21 ✅ | PR → `main` (va primero) |
| IA (Kevin) | `feature/extraccion-pdf` | 7 HV sintéticas + golden set; extracción PDF→`PerfilCandidato` con verificación de evidencias y defensa contra prompt injection | 42 unitarias ✅ · 20 evals con Gemini real ✅ | Kevin revisa y abre el PR |
| Plataforma (JVarz12) | `feature/api-postulaciones` | BD SQLite; `POST /postulaciones`, `GET /evaluaciones`, decisión del reclutador; auditoría, validaciones y Locust | 56 ✅ (96 % de cobertura) | PR |
| Frontend (Santiago) | `feature/portal-candidato` | Portal del candidato: vacantes, formulario con autorización de la Ley 1581 y página de privacidad, con mocks | 21 unitarias ✅ · 2 e2e Playwright ✅ | Santiago revisa y abre el PR |

**Orden de fusión:** primero `setup-base`; luego las otras tres en cualquier orden, porque tocan carpetas distintas. Cada una pasó por una revisión de código automática y sus hallazgos ya están corregidos.

## Siguiente (Sprint 2)
- **Kevin:** F3, que es `scoring.py` (reglas de PLAN §5) más el agente LangChain con sus 5 herramientas. Se conecta en `backend/app/evaluador.py` cambiando `evaluador_falso` por el real, y mapea `PdfInvalidoError`/`PdfSinTextoError` a 4xx.
- **Santiago:** el panel del reclutador (ranking, detalle explicado, aprobar/cambiar) y el frontend conectado a la API real (`VITE_USE_MOCKS=false`) más el e2e completo.
- **JVarz12:** F6 (Gmail + Calendar con OAuth) disparado al aprobar.

## Hecho
- 2026-11-06 · **Sprint 1** en paralelo: extracción, API + BD y portal del candidato (ver la tabla).
- 2026-11-06 · Gemini verificado contra Vertex con la API key del proyecto. El modelo por defecto es **`gemini-3.1-flash-lite`** (GA y más barato).
- 2026-11-06 · F0 (backend): contratos, 5 vacantes, config/LLM, API base, `docs/api.md` y CI.
- 2026-11-06 · `.gitignore`, plan v0.2, `CLAUDE.md` y `ONBOARDING.md`.

## Decisiones
- 2026-11-06 · Errores de la API con cuerpo `{detail}`; `GET /evaluaciones` paginado (`limit` 50, máx. 200); 502 si falla el evaluador.
- 2026-11-06 · El texto de la HV que se envía al LLM tiene un tope de 20 000 caracteres y las etiquetas de delimitación se neutralizan.
- 2026-11-05 · LinkedIn solo como canal de publicación ("aplicar en sitio externo"); no hay scraping ni API (requiere partner).
- 2026-11-05 · La IA extrae y justifica; el puntaje lo calcula Python con reglas fijas.
- 2026-11-05 · Humano en el bucle: nada se envía sin aprobación del reclutador.
- 2026-11-05 · Gemini vía Vertex AI (API key); modelo en `GEMINI_MODEL`.

## Hallazgos para el track de IA (Kevin)
- En español el género se cuela en el texto ("Desarrolladora", "Tecnóloga") y Gemini lo copia al `resumen`. El anonimizador de F7 tiene que neutralizar esos sustantivos, no solo borrar el nombre.
- Cuando la HV no menciona debilidades, el modelo responde "No especificadas". Hay que decidir si eso se permite o si debe inferir áreas de mejora frente a la vacante.
- Hoy la HV completa, con nombre y contacto, llega al LLM. Los evals comprueban que no se filtre a la salida, pero el anonimizador (F7) debe quitarlo **antes**.
- `samples/esperado.json` ya trae `veredicto` y `vacante` esperados: F3 debe usarlos en sus evals.

## Deuda conocida
- `reclutador` lo declara el cliente y no hay autenticación, así que la auditoría es suplantable. Es aceptable para el MVP; documentarlo en `docs/etica.md`.
- El 413 del middleware (Content-Length) no queda en la auditoría.
- SQLite puede dar "database is locked" con muchos usuarios concurrentes. Medirlo en la prueba de carga del Sprint 3.
- El primer p95 de Locust salió en ~2,1 s (5 usuarios, 10 s, con el agente falso). Repetirlo con una corrida más larga antes de sacar conclusiones.

## Bloqueos
- Ninguno.
