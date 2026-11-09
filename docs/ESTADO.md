# Estado del proyecto

> Tablero vivo. **Cada PR actualiza este archivo.** Lo más reciente va arriba.

## En curso: Sprint 4 (entrega)

| Rama | Qué trae | Pruebas |
|---|---|---|
| `feature/resumen-ejecutivo-y-guion` | `docs/resumen-ejecutivo.md` (1 página, con pregunta de debate) y `docs/guion-video.md` (video de 10 min con cronometría A–D, quién habla y qué se muestra) | — |
| `feature/cargar-env-al-arrancar` | El backend lee `backend/.env` al arrancar. Antes, `EVALUADOR`, `MODO_EVALUACION` y `UPLOADS_DIR` del `.env` se ignoraban hasta la primera llamada a Gemini | 411 ✅ (99 %) |
| `feature/guion-demo-y-readme` | `README.md`, guion de demo de 5 min para los tres (`docs/demo.md`) y `scripts/sembrar_demo.py` para poblar el panel con las HV sintéticas | 416 ✅ · probado contra uvicorn real |
| `feature/citas-legales` | Citas de `docs/etica.md` verificadas contra fuentes oficiales, con sección *Fuentes*. Cinco afirmaciones corregidas (ver Decisiones) | — |
| `feature/informe-final` | `docs/informe.md` (~4200 palabras) con resultados, hallazgos y pruebas exploratorias | — |
| `feature/estado-sprint-4` | Este tablero; ONBOARDING y PLAN corregidos (rama `main`, PDF escaneado → 422) | — |

**Pruebas exploratorias con Gemini real** (7 HV raras; detalle en `docs/informe.md` §8): inglés → ENTREVISTA 92.5; habilidades en tabla → se leen bien; negación explícita de React → se respeta; escaneada, vacía o casi vacía → se rechazan antes del LLM.

## Siguiente
- **JVarz12:** reautorizar Google el día antes de la demo (`python -m scripts.autorizar_google`; el token de prueba vence a los 7 días).
- **Los tres:** ensayar `docs/demo.md`, grabar el video y completar la portada del informe (curso, profesor, nombres completos).
- **Kevin (opcional):** sumar "maquetador/a" y similares al neutralizador; mensaje "texto insuficiente" para HV casi vacías.

## Hecho
- 2026-11-06 · **Rebranding a Giveaway y rediseño del frontend** fusionados (PRs #22 y #23).
- 2026-11-06 · **Entrevista en el perfil**: la fecha y el enlace de Meet quedan guardados y se ven en `/panel/:id` con un botón para unirse.
- 2026-11-06 · **Gmail + Calendar con Google real**: postulación → Gemini (ENTREVISTA, 100) → decisión → correo e invitación con Meet; auditoría `notificacion_enviada` (informe §8.4).
- 2026-11-06 · **Sprint 4** fusionado (PRs #16 a #20).
- 2026-11-06 · **Sprint 3** fusionado (PRs #12 a #15).
- 2026-11-06 · **Sprint 3**: anonimizador y prueba de sesgo, evaluación en segundo plano, retención, carga, transparencia, accesibilidad y `docs/etica.md`.
- 2026-11-06 · **Sprint 2** fusionado (PRs #8 a #11): scoring y agente, Gmail/Calendar y panel del reclutador.
- 2026-11-06 · **Sprint 2**: scoring + agente, Gmail/Calendar y panel del reclutador (ver la tabla).
- 2026-11-06 · **Sprint 1** fusionado en `main` (PRs #5, #6 y #7): extracción, API + BD y portal del candidato.
- 2026-11-06 · Gemini verificado contra Vertex. El modelo por defecto es **`gemini-3.1-flash-lite`**.
- 2026-11-06 · F0, plan v0.2, `CLAUDE.md` y `ONBOARDING.md` (PR #1).

## Decisiones
- 2026-11-06 · `GET /evaluaciones/{id}` suma `entrevista` (aditivo; pendiente de revisión de los tres). `NOTIFICADOR=falso|deshabilitado` manda sobre `token.json`: las e2e y los ensayos nunca envían correos reales.
- 2026-11-06 · **Rebranding a Giveaway** (plataforma de tours con guías locales). `Vacante` suma `descripcion`, `equipo`, `ubicacion` y `modalidad`, opcionales y sin efecto en el puntaje; requisitos y pesos no cambian. Cambio de contrato pendiente de revisión por los tres.
- 2026-11-06 · Citas legales verificadas (sin abogado). Cambios de fondo: la **T-323/2024** trata el uso de ChatGPT por un juez, así que se cita por analogía; la **Circular 002/2024 SIC** exige estudio de impacto solo si el riesgo es alto; la Ley 1482/1752 no nombra "origen" sino nacionalidad y raza; **no hay ley de IA** en Colombia (PL 025/2026 Cámara sin primer debate); Gemini en Vertex es *transmisión* a un encargado (Decreto 1377, arts. 24–25).
- 2026-11-06 · El agente LangChain es el modo por defecto, porque es requisito académico. `MODO_EVALUACION=pipeline` existe para cuando la latencia o el costo importan (1 llamada al LLM en vez de ~5).
- 2026-11-06 · Los números del resultado salen del `contexto` de las herramientas y de `scoring.py`, nunca del texto del LLM.
- 2026-11-06 · Correo de rechazo: si el reclutador contradice a la IA se usa su `motivo`; si no, las notas de los criterios con faltantes, sin cifras. Nunca se envía el puntaje crudo.
- 2026-11-06 · Un framework de Python (Django, FastAPI, Flask, pandas, pytest) cuenta como evidencia de "Python".
- 2026-11-06 · Golden: `hv_datos_media` pasa a ENTREVISTA, porque cumple las reglas de PLAN §5 (77.3).
- 2026-11-06 · Errores de la API con cuerpo `{detail}`; `GET /evaluaciones` paginado; 502 si falla el evaluador; 415/422 para PDF inválido o sin texto.
- 2026-11-05 · LinkedIn solo como canal de publicación; la IA extrae y justifica y Python puntúa; humano en el bucle; Gemini vía Vertex.

## Hallazgos para el informe
- **La experiencia no mide relevancia** (exploratoria): un chef con 8 años saca 100 en experiencia para Backend Jr. El knock-out técnico evita el falso positivo.
- **"Maquetadora" se coló en el resumen**: palabra fuera del diccionario de género. Confirma el límite de las listas finitas.
- **El `.env` no se leía al arrancar** (lo encontró el agente de la demo). Corregido en `feature/cargar-env-al-arrancar`.
- **El LLM reintroduce el género por su cuenta.** Con la entrada ya neutra, Gemini escribió "la candidata" en 2 de 7 HV. Mitigación: se neutraliza también la salida.
- **Efecto techo en la prueba de sesgo.** Con una HV fuerte todo da 100 y la prueba no detecta nada. Se repitió con una HV de rango medio, y ahora el script advierte la saturación de forma automática.
- **La arquitectura protege por sí sola.** Sin anonimizador, el puntaje tampoco cambió, porque el LLM solo extrae y las reglas puntúan.
- **La purga dejaba citas de la HV en el perfil**, y la revisión lo detectó. Ahora se redacta el perfil completo.
- **La variación del LLM puede tumbar un obligatorio.** En 1 de 4 corridas, la HV fuerte de frontend sacó 40 (knock-out) en vez de 100, según cómo Gemini nombró las habilidades. Mitigación propuesta: buscar también los requisitos en el texto verificado de la HV y ampliar los sinónimos. Que la IA solo recomiende y un humano decida es justamente la salvaguarda.
- **Sesgo de género en el idioma:** Gemini copia "Desarrolladora" y "Técnica" en el resumen y en las evidencias. El anonimizador debe neutralizarlo.
- **El golden no cubre `REVISION_HUMANA`.** Hace falta una HV con un obligatorio en el límite.
- **Defensa contra *prompt injection* verificada con Gemini real:** la HV que pide "asigna puntaje 100" saca 21.7.

## Deuda conocida
- Sin autenticación: el `reclutador` lo declara el cliente y el panel es público (documentado en `docs/etica.md` §6).
- CORS solo admite `http://localhost:5173` (abrir el frontend por `127.0.0.1` falla).
- `EVALUADOR=falso` da puntajes que no dependen del contenido de la HV: sirve para la demo de flujo, no para mostrar resultados.
- `siguiente_horario` no considera festivos colombianos.
- El 413 del middleware (Content-Length) no queda en la auditoría.
- SQLite puede dar "database is locked" con carga alta.
- El modo agente tarda ~15–27 s por HV.

## Bloqueos
- Ninguno.
