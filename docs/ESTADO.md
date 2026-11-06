# Estado del proyecto

> Tablero vivo. **Cada PR actualiza este archivo.** Lo más reciente va arriba.

## En curso: Sprint 3 (ética y cierre) terminado, faltan los PRs

| Track | Rama | Qué trae | Pruebas |
|---|---|---|---|
| IA (Kevin) | `feature/anonimizador-y-sesgo` | Anonimizador determinístico antes de Gemini (identidad, contacto, edad, origen y género); neutralización también de la **salida** del LLM; matching que busca en el texto verificado y descarta negaciones; golden `REVISION_HUMANA`; `bias_test.py` con un factor a la vez | 389 ✅ (97 %) · **41/41 evals con Gemini real** |
| Plataforma (JVarz12) | `feature/evaluacion-en-segundo-plano` | Evaluación en segundo plano (`en_evaluacion`, `pendiente_revision`, `error_evaluacion`) con reintento y recuperación de filas atascadas; SQLite WAL; purga a los 180 días que redacta el perfil; prueba de carga real | 211 ✅ (98 %) · carga: 1302 peticiones, 0 fallas, POST p95 22 ms |
| Frontend (Santiago) | `feature/transparencia-y-accesibilidad` | Panel con los estados nuevos y refresco; página **"Cómo evaluamos"** (criterios, pesos, derechos de la Ley 1581); notas rotuladas; accesibilidad con axe | 73 ✅ · 11 e2e ✅ · axe: 0 violaciones serias |
| Documentación | `feature/documento-etica` | `docs/etica.md` integrador (marco legal, riesgo → control → evidencia, límites) y resultados de la prueba de sesgo | — |

**Integración verificada (local):** las 4 ramas se fusionan sin conflictos. Juntas pasan 410 pruebas de backend (98 %), 73 de frontend, `tsc` y **11/11 e2e en navegador** contra el backend asíncrono con anonimizador. La integración destapó un bug (las e2e subían un PDF sin texto) que ya está corregido.

**Prueba de sesgo con Gemini real:** 8 variantes (nombre, género, origen, edad y combinada) × 3 corridas → **71,7 en todas, con y sin anonimizador** (diferencia 0,0). Detalle en `docs/etica.md` §5.

## Siguiente (Sprint 4: entrega)
- **JVarz12:** probar Gmail/Calendar con Google real (falta crear el cliente OAuth).
- **Los tres:** guion de demo de 5 min, video corto e informe final. Revisar las citas "por verificar" de `docs/etica.md`.

## Hecho
- 2026-11-06 · **Sprint 3**: anonimizador y prueba de sesgo, evaluación en segundo plano, retención, carga, transparencia, accesibilidad y `docs/etica.md`.
- 2026-11-06 · **Sprint 2** fusionado (PRs #8 a #11): scoring y agente, Gmail/Calendar y panel del reclutador.
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

## Hallazgos para el informe
- **El LLM reintroduce el género por su cuenta.** Con la entrada ya neutra, Gemini escribió "la candidata" en 2 de 7 HV. Mitigación: se neutraliza también la salida.
- **Efecto techo en la prueba de sesgo.** Con una HV fuerte todo da 100 y la prueba no detecta nada. Se repitió con una HV de rango medio, y ahora el script advierte la saturación de forma automática.
- **La arquitectura protege por sí sola.** Sin anonimizador, el puntaje tampoco cambió, porque el LLM solo extrae y las reglas puntúan.
- **La purga dejaba citas de la HV en el perfil**, y la revisión lo detectó. Ahora se redacta el perfil completo.
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
