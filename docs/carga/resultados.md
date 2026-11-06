# Resultados de la prueba de carga

Script: `load/locustfile.py` (Locust 2.47). Flujo: `GET /vacantes`, `GET /evaluaciones` y `POST /postulaciones` con una HV real con texto (`samples/hv_backend_fuerte_1.pdf`); tras cada POST se consulta `GET /evaluaciones/{id}` hasta que la evaluación sale de `en_evaluacion`.

## Condiciones
- 2026-11-06, Windows 11, Python 3.13, uvicorn con 1 worker en el puerto 8765.
- `EVALUADOR=falso` (no se llamó a Gemini), `DATABASE_URL` y `UPLOADS_DIR` temporales (BD SQLite con WAL y `busy_timeout`).
- 20 usuarios, rampa de 5 por segundo, 60 s, `--headless`. Pesos de tareas: 3 vacantes, 3 evaluaciones, 1 postulación.

## Resultados (ms)

| Endpoint | Peticiones | Fallas | p50 | p95 | p99 |
|---|---:|---:|---:|---:|---:|
| `GET /vacantes` | 428 | 0 | 3 | 7 | 2100 |
| `GET /evaluaciones` | 438 | 0 | 7 | 19 | 2100 |
| `POST /postulaciones` | 146 | 0 | 10 | 22 | 38 |
| `GET /evaluaciones/{id}` | 290 | 0 | 4 | 8 | 18 |
| **Total** | **1302** | **0** | **5** | **15** | **2100** |

Las 146 postulaciones terminaron en `pendiente_revision`: ninguna quedó en `en_evaluacion` ni en `error_evaluacion`. El log del servidor no tiene trazas ni "database is locked".

## Conclusión
- Con 20 usuarios concurrentes (~22 peticiones/s) no hubo fallas y el p95 global fue de 15 ms. El `POST /postulaciones` responde en ~10 ms porque la evaluación ya no bloquea la petición.
- El p99 de 2,1 s son unas pocas peticiones (menos del 1 %) con ~2,07 s de máximo, que coinciden con el arranque de los 20 usuarios (causa probable, no medida). En `POST` y `GET /evaluaciones/{id}` el p99 fue de 38 y 18 ms.
- "database is locked" no apareció. Se mantienen WAL y `busy_timeout` (10 s) porque las tareas en segundo plano escriben mientras el panel lee.
- Limitación: el evaluador era el simulado (instantáneo). Con el agente real (15 a 27 s por HV, llamadas a Gemini) las tareas en segundo plano durarán mucho más y habrá cuotas y límites de tasa de Gemini que esta prueba no mide. Las tareas corren en el pool de hilos de Starlette (por defecto 40 hilos), por lo que unas 40 evaluaciones simultáneas saturarían el pool; para la demo basta, para producción haría falta una cola.
