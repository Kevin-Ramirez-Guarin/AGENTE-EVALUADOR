# Agente Evaluador — Plan del proyecto (MVP)

> Grupo 3 · Agente evaluador para selección y contratación laboral (inspiración: *Gattaca*)
> Versión 0.1 · 2026-11-05 · Documento vivo: se actualiza al cerrar cada fase.

---

## 1. Qué vamos a construir (en una frase)

Un sistema donde un candidato se postula a una vacante subiendo su hoja de vida en PDF. Un **agente LangChain + Gemini** extrae sus competencias en JSON, las compara contra el perfil del cargo y produce un **puntaje explicado por criterio**. Un reclutador humano **aprueba o corrige** el veredicto. Solo entonces el sistema envía el correo y agenda la entrevista en Google Calendar.

## 2. Ajustes al flujo original (y por qué)

| Idea original | Ajuste | Razón |
|---|---|---|
| Sacar postulaciones de LinkedIn | La vacante se publica en LinkedIn con **"Aplicar en sitio externo"**, que apunta a nuestro formulario `/aplicar/:vacante`. | La API de LinkedIn exige ser partner certificado (Apply Connect), y el scraping viola sus términos (sección 8.2). El formulario propio además deja pedir la **autorización de datos** que exige la Ley 1581. |
| La IA decide y envía el correo sola | La IA **recomienda**. El reclutador da clic en "Aprobar" y ahí se envían el correo y el evento. | Hay derecho a revisión humana (GDPR art. 22, guía SIC 2024), y en la UE el reclutamiento es "alto riesgo" (AI Act). Esto es el corazón del eje ético. |
| La IA da el puntaje | La IA **extrae y justifica con evidencia**. El puntaje lo calcula **Python con reglas y pesos fijos**. | Es explicable, reproducible y auditable. El LLM no "inventa" números. |
| La IA lee la HV completa | Antes de evaluar se **anonimiza**: nombre, género, edad, foto, estado civil, nacionalidad, dirección. | Mitiga la discriminación algorítmica. Esa evaluación "ciega" es una de las demos del proyecto. |
| Perfil por puesto | Un solo perfil del candidato se compara contra **todas** las vacantes abiertas, y se sugiere la mejor. | Es la misma llamada de extracción reutilizada. Cuesta casi cero. |

## 3. Arquitectura

```
                 LinkedIn (vacante → "aplicar en sitio externo")
                                   │
                                   ▼
┌──────────────────────── FRONTEND (React + Vite + Tailwind) ────────────────────────┐
│  Portal candidato: /vacantes, /aplicar/:id  (PDF + consentimiento)                 │
│  Panel reclutador: /panel  (ranking, detalle explicado, Aprobar / Rechazar / Editar)│
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ REST (JSON)
┌───────────────────────────── BACKEND (FastAPI, Python) ─────────────────────────────┐
│  API ──► Servicio de evaluación ──► AGENTE LangChain (create_agent + Gemini)       │
│                                       herramientas:                                 │
│                                        1. extraer_texto_pdf   (pypdf)               │
│                                        2. anonimizar_texto    (regex + LLM)         │
│                                        3. extraer_perfil      (salida JSON Pydantic)│
│                                        4. evaluar_contra_vacante (reglas Python)    │
│                                        5. comparar_otras_vacantes                   │
│  Reglas de negocio (scoring.py) · Auditoría (log de cada decisión)                 │
│  Al aprobar ─► Gmail API (correo) + Calendar API (evento con link de Meet)         │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │
                        SQLite (SQLModel) + carpeta /uploads
```

**Stack y motivo**

- **Backend: Python + FastAPI.** LangChain es nativo en Python. FastAPI genera la documentación `/docs` gratis.
- **LLM: `ChatGoogleGenerativeAI(vertexai=True, api_key=...)`** de `langchain-google-genai` 4.x. Usa Vertex AI en *express mode*. El modelo va en la variable `GEMINI_MODEL`, porque Google cambia los nombres seguido. Arrancamos con `gemini-3-flash-preview` (está confirmado en express mode) y probamos `gemini-3.1-flash-lite`, que es más barato.
- **Agente: `langchain.agents.create_agent`** (LangChain 1.x, corre sobre LangGraph) con `response_format` = modelo Pydantic.
- **BD: SQLite.** Es un archivo, no hay servidor que instalar, y alcanza para un MVP.
- **Frontend: React + Vite + Tailwind.** Son dos vistas, sin librería de estado.
- **Correo y calendario: Gmail API + Calendar API** con un solo OAuth (cuenta Gmail del equipo, app en modo *testing*).

## 4. El negocio ficticio

**Nexo Digital S.A.S.** es una empresa de software en Medellín, de 40 personas, que hace productos web para pymes.

| Vacante | Imprescindibles (knock-out) | Deseables | Blandas clave |
|---|---|---|---|
| Desarrollador/a Backend Jr (Python) | Python, SQL, Git | FastAPI/Django, Docker, testing | Trabajo en equipo, aprendizaje |
| Desarrollador/a Frontend (React) | JavaScript, React, HTML/CSS | TypeScript, Tailwind, accesibilidad | Comunicación, atención al detalle |
| Analista de Datos | SQL, Excel avanzado, estadística básica | Python/pandas, Power BI | Pensamiento analítico, comunicación |
| QA Tester | Casos de prueba, reporte de bugs | Automatización (Playwright/Selenium), API testing | Rigurosidad, comunicación |
| Soporte Técnico / Customer Success | Atención al cliente, inglés B1 | Ticketing (Jira/Zendesk), SQL básico | Empatía, resolución de problemas |

Cada vacante vive en `backend/data/vacantes.json` con estos campos: `requisitos_obligatorios`, `deseables`, `blandas`, `experiencia_min_anios`, `nivel_educativo_min`, `idiomas` y `pesos`.

## 5. Reglas de negocio (scoring determinístico)

```
puntaje = 0.45·técnico + 0.25·experiencia + 0.15·blandas + 0.10·educación + 0.05·idiomas   (0–100)
```

- **Técnico:** los obligatorios valen el 70% de este bloque y los deseables el 30%. Cada habilidad cuenta solo si el LLM cita **evidencia textual** de la HV. Si no hay evidencia, no hay puntos.
- **Knock-out:** si falta ≥1 requisito obligatorio, el puntaje se topa en 40.
- **Veredicto sugerido:**
  - **≥ 75:** `ENTREVISTA`
  - **55–74:** `REVISION_HUMANA`
  - **< 55:** `NO_CONTINUA`
- **Recomendación cruzada:** si el candidato saca ≥ 75 en *otra* vacante abierta, se sugiere moverlo allá.
- **Nada sale sin aprobación:** el correo y el evento solo se disparan cuando el reclutador aprueba. El reclutador puede cambiar el veredicto, y el cambio queda en la auditoría con su motivo.
- **Entrevista:** se agenda en el siguiente día hábil, a las 10:00 o a las 15:00 (hora de Bogotá), con 45 min de duración y link de Meet.

## 6. Contratos de datos (salida JSON del LLM)

```python
class Habilidad(BaseModel):
    nombre: str
    nivel: Literal["basico", "intermedio", "avanzado"]
    evidencia: str            # cita textual de la HV

class PerfilCandidato(BaseModel):
    habilidades_tecnicas: list[Habilidad]
    habilidades_blandas: list[Habilidad]
    anios_experiencia: float
    nivel_educativo: Literal["bachiller","tecnico","tecnologo","profesional","posgrado"]
    idiomas: list[dict]       # {idioma, nivel}
    fortalezas: list[str]     # 3 máx
    debilidades: list[str]    # 3 máx (áreas de mejora, redacción respetuosa)
    resumen: str
```

**Tablas:**

- `Vacante`
- `Candidato` (datos de contacto, separados de la HV anonimizada)
- `Postulacion`
- `Evaluacion` (perfil JSON, puntajes por criterio, veredicto IA, veredicto final, quién aprobó)
- `Auditoria`

## 7. Eje ético y regulatorio (entregable propio, no un anexo)

1. **Consentimiento:** el formulario pide una autorización expresa e informada (Ley 1581 art. 9) y enlaza a la política de tratamiento.
2. **Minimización:** no se piden ni se extraen datos sensibles (art. 5). El LLM nunca ve los datos de identidad.
3. **Evaluación ciega:** la anonimización se hace antes del agente.
4. **Prueba de sesgo contrafactual:** es un script con la misma HV y variaciones de nombre/género/origen (ej. "María Gómez" vs "Juan Gómez" vs un nombre extranjero). La diferencia de puntaje debe ser **< 5 puntos**. El resultado va al informe.
5. **Derecho a la explicación:** el panel y el correo muestran el puntaje por criterio y la evidencia, en lenguaje claro.
6. **Humano en el bucle:** la IA nunca rechaza sola. Ver la sección 5.
7. **Auditoría y retención:** se registra cada decisión. Las HV se borran a los 6 meses (lo documentamos; el borrado automático es opcional).
8. **Documento:** se redacta una evaluación de impacto de privacidad (pide la Circular SIC 002/2024), junto con el análisis de la Ley 1581, el Decreto 1377, la Ley 1482 (antidiscriminación), la T-323/2024, GDPR art. 22 y el AI Act. *Colombia no tiene ley de IA aprobada a oct-2026.*

## 8. Estructura del repo

```
AGENTE-EVALUADOR/
├── PLAN.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI: rutas
│   │   ├── models.py        # SQLModel + Pydantic
│   │   ├── agent.py         # create_agent + herramientas
│   │   ├── scoring.py       # reglas de negocio (con tests)
│   │   ├── anonymizer.py
│   │   └── google_apis.py   # Gmail + Calendar
│   ├── data/vacantes.json
│   ├── tests/
│   ├── scripts/bias_test.py
│   └── .env.example         # GEMINI_API_KEY, GEMINI_MODEL, ...
├── frontend/                # Vite + React
├── samples/                 # HV sintéticas en PDF (nunca reales)
└── docs/etica.md
```

## 9. Fases (módulo a módulo)

Cada fase termina en algo **demostrable** y en un commit.

| # | Fase | Resultado verificable | Depende de |
|---|---|---|---|
| F0 | **Setup** | Repo clonado, estructura, `.env`, script que llama a Gemini y responde. | — |
| F1 | **Negocio y datos** | `vacantes.json` (5 vacantes) y 6–8 HV sintéticas en PDF (fuertes, medias, débiles, una escaneada). | F0 |
| F2 | **Extracción (núcleo IA)** | `python -m app.agent samples/hv1.pdf` imprime el `PerfilCandidato` en JSON. | F0, F1 |
| F3 | **Scoring y agente completo** | `scoring.py` con tests, agente con las 5 herramientas, salida = evaluación + veredicto + mejor vacante. | F2 |
| F4 | **API** | Rutas `POST /postulaciones`, `GET /vacantes`, `GET /evaluaciones`, `POST /evaluaciones/{id}/decision`. | F3 |
| F5 | **Frontend** | Portal candidato y panel reclutador funcionando contra la API. | F4 (puede empezar antes con datos mock) |
| F6 | **Gmail + Calendar** | Al aprobar llega el correo y aparece el evento con Meet. | F0 (independiente) |
| F7 | **Ética** | Anonimizador, `bias_test.py` con resultados, explicación visible, `docs/etica.md`. | F3 |
| F8 | **Demo y entrega** | README, guion de demo de 5 min, video corto, informe. | todas |

**En paralelo** (con sesiones o sub-agentes separados): cuando cierre F3, **F5**, **F6** y **F7** corren al mismo tiempo porque no tocan los mismos archivos.

**Camino crítico:** F0 → F1 → F2 → F3 → F4. Si el tiempo aprieta, el MVP mínimo presentable es **F0–F4 + F7**, con la API usada desde `/docs`.

## 10. Cómo vamos a trabajar (orquestación)

- **Yo (orquestador):** mantengo este plan, defino cada fase, reviso y te reporto. No escribo el código directamente.
- **Por fase:** un sub-agente implementa siguiendo la sección de este plan. Luego un sub-agente revisor (código y seguridad) lo revisa, yo verifico el criterio "Resultado verificable" y se hace commit.
- **Ahorro de tokens:** cada sub-agente recibe solo su fase y los contratos (secciones 5–6), no la conversación entera.
- **Ramas:** `main` estable y una rama por fase (`feat/f2-extraccion`), con PR para que el resto del grupo vea el avance.

## 11. Lo que necesito de ti (bloqueantes)

1. **Acceso al repo:** `github.com/Kevin-Ramirez-Guarin/AGENTE-EVALUADOR` no responde con tu cuenta. Lo más probable es que tengas una invitación de colaborador pendiente; acéptala en `https://github.com/Kevin-Ramirez-Guarin/AGENTE-EVALUADOR/invitations`.
2. **API key de Gemini:** actívala en Vertex AI *express mode* (Google Cloud Console → Vertex AI / "Agent Platform" → Express mode). Nunca la pegues en el chat ni en el repo: va en `backend/.env`.
3. **OAuth para Gmail y Calendar** (solo hasta F6): en Cloud Console, crea una pantalla de consentimiento en modo *Testing*, agrega tu correo como usuario de prueba y crea un "OAuth client ID" de tipo Desktop. Yo te guío cuando lleguemos.
4. **Validar el negocio:** confirma si te sirve "Nexo Digital" y las 5 vacantes, o cámbialas.

## 12. Riesgos

| Riesgo | Mitigación |
|---|---|
| No está confirmado que los créditos de $300 apliquen a express mode. | En F0 se mide el costo real de una evaluación. Con modelos *flash-lite* una HV cuesta < $0,01. |
| Google cambia o retira modelos (los 2.5 se retiraron el 20-oct-2026). | El modelo va en la variable `GEMINI_MODEL`. |
| Los tokens OAuth en modo testing caducan a los 7 días. | Re-autenticar antes de la demo. Como respaldo, correo por SMTP con contraseña de aplicación. |
| PDFs escaneados sin texto | Si `pypdf` devuelve poco texto, se envía el PDF directo a Gemini (que lee PDFs). |
| El LLM inventa habilidades. | Cada habilidad exige evidencia textual, y se verifica que la cita exista en la HV. |
