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

201:
```json
{ "evaluacion_id": 12, "estado": "pendiente_revision" }
```
Errores: 404 vacante inexistente; 415 no es PDF; 413 PDF > 5 MB (o cuerpo mayor a ~5,1 MB); 422 sin consentimiento, campos inválidos (`nombre` 1-200 caracteres, `email` con formato válido y máx. 254) o PDF sin capa de texto (escaneo; `detail`: "No pudimos leer texto en tu PDF; ¿es un escaneo? Súbelo con texto seleccionable"); 415 también si el evaluador detecta un PDF corrupto; 502 el evaluador falló por otra causa. En todos los errores del evaluador se audita y no se guarda nada.

## GET /evaluaciones  (implementada)
Panel del reclutador, ordenado por puntaje descendente. Query opcional: `vacante_id`, `estado`, `limit` (1-200, por defecto 50) y `offset` (>= 0, por defecto 0).
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
    "mejor_vacante_alternativa": null
  },
  "veredicto_final": null,
  "estado": "pendiente_revision"
}
```
`veredicto_sugerido` / `veredicto_final`: `ENTREVISTA`, `REVISION_HUMANA` o `NO_CONTINUA`.

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
`entrevista` es `null` si el veredicto no es `ENTREVISTA`; en este sprint siempre es `null` (aún no se envía correo ni se agenda). `motivo` máx. 1000 caracteres y `reclutador` 1-100 (lo declara el cliente; sin autenticación por ahora). Errores: 404 evaluación inexistente; 422 falta motivo; 409 ya decidida.
