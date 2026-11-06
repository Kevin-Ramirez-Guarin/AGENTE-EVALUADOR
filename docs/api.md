# Contrato de la API

Base: `http://localhost:8000`. Todo es JSON salvo la carga del PDF. Todas las rutas de este documento están implementadas. Los errores HTTP devuelven `{"detail": "mensaje"}` (en 422 de validación de campos, `detail` es una lista de errores de FastAPI). Los modelos están en `backend/app/models.py`.

## GET /health  (implementada)
```json
{ "status": "ok" }
```

## GET /vacantes  (implementada)
200 → lista de vacantes.
```json
[
  {
    "id": "backend-jr",
    "titulo": "Desarrollador/a Backend Jr (Python)",
    "requisitos_obligatorios": ["Python", "SQL", "Git"],
    "deseables": ["FastAPI/Django", "Docker", "Testing"],
    "blandas": ["Trabajo en equipo", "Aprendizaje"],
    "experiencia_min_anios": 1,
    "nivel_educativo_min": "tecnologo",
    "idiomas": [{ "idioma": "inglés", "nivel": "A2" }],
    "pesos": { "tecnico": 0.45, "experiencia": 0.25, "blandas": 0.15, "educacion": 0.10, "idiomas": 0.05 }
  }
]
```
`GET /vacantes/{id}` (implementada) devuelve una sola vacante; 404 `{"detail": "Vacante no encontrada"}` si no existe.

## POST /postulaciones  (implementada)
`multipart/form-data`:

| Campo | Tipo | Notas |
|---|---|---|
| `vacante_id` | texto | debe existir, si no 404 |
| `nombre`, `email` | texto | datos de contacto, se guardan aparte de la HV |
| `pdf` | archivo | solo PDF, máx. 5 MB |
| `consentimiento` | booleano | debe ser `true` (Ley 1581), si no 422 |

201 (la evaluación sigue en segundo plano; el agente real tarda 15-27 s por HV):
```json
{ "evaluacion_id": 12, "estado": "en_evaluacion" }
```
Las validaciones son síncronas y no guardan nada (se audita `postulacion_rechazada`): 404 vacante inexistente; 415 no es PDF o está corrupto; 413 PDF > 5 MB (o cuerpo mayor a ~5,1 MB); 422 sin consentimiento, campos inválidos (`nombre` 1-200 caracteres, `email` con formato válido y máx. 254) o PDF sin capa de texto (escaneo; `detail`: "No pudimos leer texto en tu PDF; ¿es un escaneo? Súbelo con texto seleccionable").

**Segundo plano.** Tras el 201 una tarea abre su propia sesión de BD y llama al evaluador con `identidad={"nombre", "email"}`. Estados de la evaluación:
- `en_evaluacion` → `pendiente_revision`: resultado guardado y auditoría `evaluacion_creada`.
- `en_evaluacion` → `error_evaluacion`: `error` breve (tipo de excepción, sin trazas ni datos personales) y auditoría `evaluacion_fallida`. El PDF se conserva para reintentar.
- `pendiente_revision` → `decidida`: ver `/decision`.

El cliente consulta `GET /evaluaciones/{id}` hasta que `estado` deje de ser `en_evaluacion`.

## GET /evaluaciones  (implementada)
Panel del reclutador. Orden: primero las evaluadas (`pendiente_revision` y `decidida`) por puntaje descendente, luego `en_evaluacion` y luego `error_evaluacion`; `puntaje_total` y `veredicto_sugerido` son `null` en estas dos últimas. Query opcional: `vacante_id`, `estado`, `limit` (1-200, por defecto 50) y `offset` (>= 0, por defecto 0).
```json
[
  {
    "id": 12,
    "vacante_id": "backend-jr",
    "candidato": "Ana Pérez",
    "puntaje_total": 82.5,
    "veredicto_sugerido": "ENTREVISTA",
    "veredicto_final": null,
    "estado": "pendiente_revision"
  }
]
```

## GET /evaluaciones/{id}  (implementada)
200 (404 si no existe):
```json
{
  "id": 12,
  "vacante_id": "backend-jr",
  "candidato": "Ana Pérez",
  "perfil": {
    "habilidades_tecnicas": [{ "nombre": "Python", "nivel": "avanzado", "evidencia": "2 años desarrollando APIs en Python" }],
    "habilidades_blandas": [],
    "anios_experiencia": 2,
    "nivel_educativo": "tecnologo",
    "idiomas": [{ "idioma": "inglés", "nivel": "B1" }],
    "fortalezas": ["Dominio de Python"],
    "debilidades": ["Poca experiencia con Docker"],
    "resumen": "Desarrolladora backend con 2 años de experiencia."
  },
  "resultado": {
    "puntaje_total": 82.5,
    "puntajes_por_criterio": { "tecnico": 88, "experiencia": 80, "blandas": 70, "educacion": 100, "idiomas": 100 },
    "veredicto_sugerido": "ENTREVISTA",
    "cumple_obligatorios": true,
    "explicacion": "Cumple los 3 requisitos obligatorios con evidencia en la HV.",
    "mejor_vacante_alternativa": null,
    "criterios": [
      {
        "criterio": "tecnico",
        "puntaje": 88,
        "peso": 0.45,
        "cumplidos": ["Python", "SQL", "Git", "Docker"],
        "faltantes": ["Testing"],
        "evidencias": ["2 años desarrollando APIs en Python"],
        "nota": "Cumple todos los requisitos imprescindibles. Reforzar testing te ayudaría a crecer en el cargo."
      }
    ]
  },
  "veredicto_final": null,
  "estado": "pendiente_revision",
  "error": null
}
```
`perfil` y `resultado` son `null` mientras `estado` sea `en_evaluacion` o `error_evaluacion`; `error` (texto corto o `null`) se llena solo en `error_evaluacion`. `veredicto_sugerido` / `veredicto_final`: `ENTREVISTA`, `REVISION_HUMANA` o `NO_CONTINUA`.

**Cambio de contrato (aditivo):** `resultado.criterios` es una lista, vacía por defecto, con un objeto por criterio (`tecnico`, `experiencia`, `blandas`, `educacion`, `idiomas`). Cada objeto trae `puntaje` (0-100), `peso` (0-1), `cumplidos`, `faltantes`, `evidencias` y una `nota` en lenguaje claro para la persona candidata. Los campos existentes no cambian. (El ejemplo muestra solo un criterio por brevedad.)

## POST /evaluaciones/{id}/decision  (implementada)
Solo aquí, al aprobar, se envían el correo y el evento de Calendar.

Cuerpo:
```json
{ "veredicto": "ENTREVISTA", "motivo": "Buen perfil técnico", "reclutador": "jvarz12" }
```
`motivo` es obligatorio si `veredicto` difiere del sugerido (queda en la auditoría).

200:
```json
{ "id": 12, "veredicto_final": "ENTREVISTA", "estado": "decidida", "entrevista": { "inicio": "2026-11-09T10:00:00-05:00", "meet_link": "https://meet.google.com/xxx-xxxx-xxx" } }
```
Los correos y el evento salen después de guardar la decisión: `ENTREVISTA` agenda (siguiente día hábil 10:00, 45 min, Meet) y envía invitación; `NO_CONTINUA` envía un correo con explicación breve por criterio; `REVISION_HUMANA` no envía nada. `entrevista` es `null` si el veredicto no es `ENTREVISTA`, si Google no está autorizado (auditoría `notificacion_omitida`) o si falla (la decisión se mantiene; auditoría `notificacion_fallida`). `motivo` máx. 1000 caracteres y `reclutador` 1-100 (lo declara el cliente; sin autenticación por ahora). Errores: 404 evaluación inexistente; 422 falta motivo; 409 si el estado no es `pendiente_revision` (ya decidida, `en_evaluacion` o `error_evaluacion`).

## POST /evaluaciones/{id}/reintentar  (implementada)
Vuelve a programar en segundo plano una evaluación en `error_evaluacion` (usa el PDF conservado). Sin cuerpo.

202:
```json
{ "id": 12, "estado": "en_evaluacion" }
```
Errores: 404 no existe; 409 si no está en `error_evaluacion`.
