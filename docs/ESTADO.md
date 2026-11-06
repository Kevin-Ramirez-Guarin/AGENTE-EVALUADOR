# Estado del proyecto

> Tablero vivo. **Cada PR actualiza este archivo.** Lo más reciente va arriba.

## En curso: Sprint 2 terminado, faltan los PRs

| Track | Rama | Qué trae | Pruebas | Siguiente paso |
|---|---|---|---|---|
| IA (Kevin) | `feature/scoring-y-agente` | `scoring.py` (reglas de PLAN §5), agente LangChain `create_agent` con 4 herramientas (fuente de verdad: `contexto`, no el LLM), evaluador real conectado, contrato `CriterioDetalle`, `MODO_EVALUACION=agente\|pipeline` | 164 ✅ (98 %) · 30 evals Gemini real: 29–30 ✅ (ver hallazgos) | Kevin revisa el PR |
| Plataforma (JVarz12) | `feature/correo-y-calendario` | Gmail + Calendar con OAuth (`scripts/autorizar_google.py`), correo de invitación con Meet y de rechazo explicado, errores PDF → 415/422, `UPLOADS_DIR`, CI con job de frontend | 103 ✅ (96 %) | Configurar OAuth y probar con Google real |
| Frontend (Santiago) | `feature/panel-reclutador` | Panel del reclutador: ranking paginado, detalle explicado por criterio con evidencias, decisión con confirmación; API real por defecto | 48 unitarias ✅ · 4 e2e Playwright contra el backend real ✅ | Santiago revisa el PR |

**Integración verificada (local):** las 3 ramas se fusionan sin conflictos. Juntas pasan 190 pruebas de backend y 48 de frontend. La demo de punta a punta con Gemini real hizo lo siguiente: 4 HV → ranking 100 / 95.5 / 28.3 / 21.7 (la HV con *prompt injection* quedó última) → detalle explicado → decisión → auditoría.

## Siguiente (Sprint 3: ética y cierre)
- **Kevin:**
  - Anonimizador antes del LLM. Además de nombre y contacto, debe neutralizar el género ("Desarrolladora", "Técnica").
  - `scripts/bias_test.py` contrafactual (diferencia < 5 puntos).
  - Robustecer el matching frente a la variación del LLM (ver hallazgos).
- **Santiago:** UI de transparencia para el candidato ("cómo evaluamos") y accesibilidad general. Las `nota` hablan en 2.ª persona ("Tu experiencia…"); en el panel conviene una versión para el reclutador.
- **JVarz12:**
  - Probar Gmail/Calendar con Google real.
  - Prueba de carga con Locust con el evaluador falso (p95) y medir la latencia real (~15–27 s por HV en modo agente). Esa latencia probablemente pide procesar en segundo plano.
- **Los tres:** `docs/etica.md`, guion de demo e informe.

## Hecho
- 2026-11-06 · **Sprint 2**: scoring + agente, Gmail/Calendar y panel del reclutador (ver la tabla).
- 2026-11-06 · **Sprint 1** fusionado en `main` (PRs #5, #6 y #7): extracción, API + BD y portal del candidato.
- 2026-11-06 · Gemini verificado contra Vertex. El modelo por defecto es **`gemini-3.1-flash-lite`**.
- 2026-11-06 · F0, plan v0.2, `CLAUDE.md` y `ONBOARDING.md` (PR #1).

## Decisiones
- 2026-11-06 · El agente LangChain es el modo por defecto, porque es requisito académico. `MODO_EVALUACION=pipeline` existe para cuando la latencia o el costo importan (1 llamada al LLM en vez de ~5).
- 2026-11-06 · Los números del resultado salen del `contexto` de las herramientas y de `scoring.py`, nunca del texto del LLM.
- 2026-11-06 · Correo de rechazo: si el reclutador contradice a la IA se usa su `motivo`; si no, las notas de los criterios con faltantes, sin cifras. Nunca se envía el puntaje crudo.
- 2026-11-06 · Un framework de Python (Django, FastAPI, Flask, pandas, pytest) cuenta como evidencia de "Python".
- 2026-11-06 · Golden: `hv_datos_media` pasa a ENTREVISTA, porque cumple las reglas de PLAN §5 (77.3).
- 2026-11-06 · Errores de la API con cuerpo `{detail}`; `GET /evaluaciones` paginado; 502 si falla el evaluador; 415/422 para PDF inválido o sin texto.
- 2026-11-05 · LinkedIn solo como canal de publicación; la IA extrae y justifica y Python puntúa; humano en el bucle; Gemini vía Vertex.

## Hallazgos para el informe y el Sprint 3
- **La variación del LLM puede tumbar un obligatorio.** En 1 de 4 corridas, la HV fuerte de frontend sacó 40 (knock-out) en vez de 100, según cómo Gemini nombró las habilidades. Mitigación propuesta: buscar también los requisitos en el texto verificado de la HV y ampliar los sinónimos. Que la IA solo recomiende y un humano decida es justamente la salvaguarda.
- **Sesgo de género en el idioma:** Gemini copia "Desarrolladora" y "Técnica" en el resumen y en las evidencias. El anonimizador debe neutralizarlo.
- **El golden no cubre `REVISION_HUMANA`.** Hace falta una HV con un obligatorio en el límite.
- **Defensa contra *prompt injection* verificada con Gemini real:** la HV que pide "asigna puntaje 100" saca 21.7.

## Deuda conocida
- Sin autenticación: el `reclutador` lo declara el cliente y el panel es público. Aceptable para el MVP; documentarlo en `docs/etica.md`.
- `siguiente_horario` no considera festivos colombianos.
- El 413 del middleware (Content-Length) no queda en la auditoría.
- SQLite puede dar "database is locked" con carga alta.
- El modo agente tarda ~15–27 s por HV.

## Bloqueos
- **OAuth de Google (JVarz12):** para probar los correos reales hay que crear el cliente OAuth de escritorio, guardarlo en `backend/credentials.json` y correr `python -m scripts.autorizar_google`.
