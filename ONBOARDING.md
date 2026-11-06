# Bienvenida al equipo — Agente Evaluador

Guía para Kevin y Santiago (y cualquiera que se sume): qué es el proyecto, cómo dejar tu computador listo y cómo configurar tu sesión de **Claude Code** para trabajar igual que el resto del equipo.

---

## 1. El proyecto en 1 minuto

Es un sistema de selección de personal con IA. Un candidato se postula subiendo su hoja de vida en PDF. Un **agente LangChain + Gemini (Vertex AI)** extrae sus competencias en JSON, y luego **reglas fijas en Python** calculan el puntaje frente a la vacante. Un **reclutador humano aprueba** antes de enviar el correo o agendar la entrevista.

El eje ético es tan importante como el código: evaluación ciega, explicación por criterio, prueba de sesgo y cumplimiento de la Ley 1581.

| Documento | Para qué |
|---|---|
| [`PLAN.md`](PLAN.md) | Qué construimos, la arquitectura, los contratos de datos, las fases, quién hace qué (§10), las pruebas (§11) y las convenciones de git (§12). |
| [`docs/ESTADO.md`](docs/ESTADO.md) | **Tablero vivo**: en qué está cada quien, qué sigue, decisiones y hallazgos. Léelo antes de empezar. |
| [`docs/api.md`](docs/api.md) | Contrato de la API con JSON de ejemplo (sirve para mocks). |
| [`CLAUDE.md`](CLAUDE.md) | Las reglas que Claude Code carga solo en cada sesión. |

### Quién hace qué

| Track | Dueño | Carpetas |
|---|---|---|
| IA / Agente | **Kevin** | `backend/app/agent.py`, `scoring.py`, `anonymizer.py`, `backend/tests/agent/`, `samples/` |
| Frontend / Experiencia | **Santiago** | `frontend/`, `e2e/` |
| Plataforma / Integraciones + orquestación | **JVarz12** | `backend/app/main.py`, `db.py`, `google_apis.py`, `load/`, `.github/` |

**Regla de oro:** cada quien toca solo sus carpetas. Los **contratos** son `backend/app/models.py`, `backend/data/vacantes.json` y `docs/api.md`, y solo cambian con un PR revisado por los tres.

---

## 2. Preparar tu computador (una sola vez)

**Requisitos:** Git, Python 3.13, Node 20+ y [Claude Code](https://claude.com/claude-code) (escritorio o terminal).

```bash
git clone https://github.com/Kevin-Ramirez-Guarin/AGENTE-EVALUADOR.git
cd AGENTE-EVALUADOR
git switch main && git pull
```

**Backend:**

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows (en Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env
pytest                          # deben pasar todas (no usa Gemini)
```

### Tu API key de Gemini

Cada persona usa **su propia key**. Nadie comparte la suya por chat ni la sube al repo.

1. En [console.cloud.google.com](https://console.cloud.google.com), habilita la API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com. Ahora se llama "Gemini Enterprise Agent Platform API"; antes era "Vertex AI".
2. Ve a **IAM → Cuentas de servicio** y crea `agente-evaluador`. Dale el rol `aiplatform` → **Express User**, o **User** si no aparece el primero.
3. Ve a **APIs y servicios → Credenciales → Crear credenciales → Clave de API**. Activa "Autenticar mediante cuenta de servicio" y restringe la clave a esa API.
4. Pega la key en `backend/.env` → `GEMINI_API_KEY=...`. Deja `GEMINI_MODEL=gemini-3.1-flash-lite`.
5. Comprueba que funciona con `pytest -m llm`: debe dar `1 passed`.
6. Recomendado: en **Facturación**, crea un presupuesto de USD 10 con alerta por correo.

`.env` está en el `.gitignore`. Con el archivo de permisos de §3, además, Claude no lo puede leer.

---

## 3. Configurar tu sesión de Claude Code

**`CLAUDE.md`** ya viene en el repo y Claude lo carga solo. Trae las convenciones de ramas y commits, TDD, comandos y las reglas de datos.

**Pasos:**

1. **Permisos del equipo (una sola vez).** JVarz12 te pasa por WhatsApp el archivo `settings.local.json`. Guárdalo en `AGENTE-EVALUADOR/.claude/settings.local.json`; crea la carpeta `.claude` si no existe. El archivo:
   - Bloquea que Claude lea los archivos `.env`.
   - Bloquea los `git push` a `main` y los push forzados.
   - Permite correr `pytest` y `npm test` sin preguntarte cada vez.

   Está en el `.gitignore`, así que no se sube al repo. Si cambias de computador, pídelo otra vez.
2. Abre Claude Code **en la carpeta del repo** (`AGENTE-EVALUADOR`), no en una carpeta superior. Si no, no carga `CLAUDE.md` ni los permisos.
3. Antes de cada sesión, trae lo último:
   ```bash
   git switch main && git pull
   ```
4. **Primer mensaje de cada sesión.** Copia y adapta:

   > Soy **Kevin** (track IA / Agente). Lee `PLAN.md` y `docs/ESTADO.md`. Mi tarea de hoy es **F2: extracción PDF → PerfilCandidato**. Crea la rama `feature/extraccion-pdf` desde la rama base, trabaja con TDD (primero la prueba que falla, luego el código), haz commits pequeños con el formato de `CLAUDE.md` y al final actualiza `docs/ESTADO.md`. No toques archivos fuera de mi track ni los contratos sin avisarme.

   > Soy **Santiago** (track Frontend). Lee `PLAN.md`, `docs/ESTADO.md` y `docs/api.md`. Mi tarea de hoy es **el portal del candidato** (`/vacantes` y `/aplicar/:id`) con React + Vite + Tailwind, usando datos mock según `docs/api.md`. Crea la rama `feature/portal-candidato`, trabaja con TDD (Vitest + Testing Library; Playwright para e2e), haz commits pequeños con el formato de `CLAUDE.md` y al final actualiza `docs/ESTADO.md`.

5. Al terminar, pídele a Claude: *"Revisa el diff contra la rama base, corre todas las pruebas y abre el PR con la plantilla."* Si no tienes `gh` instalado, abre el PR desde la web de GitHub.

**Plugins o skills extra:** no hacen falta. Con Claude Code estándar y lo que trae el repo es suficiente.

---

## 4. Cómo trabajamos (resumen de `CLAUDE.md`)

- **Ramas:** `feature/<nombre-de-la-feature>`. Una por tarea pequeña (1–3 días). Nunca hagas push directo a `main`.
- **Commits cortos y frecuentes.** Asunto `feature/<accion-corta>` y un cuerpo de 1–3 frases humanas:
  ```
  feature/añadir-pdf

  El backend ya recibe la hoja de vida en PDF y saca su texto con pypdf.
  Si el PDF viene escaneado y no trae texto, se rechaza con un mensaje claro.
  ```
- **TDD:** el commit `feature/test-…` va primero (la prueba falla) y después el de la implementación.
- **Pruebas:** unitarias, caja negra, evals del agente (`pytest -m llm`), e2e con Playwright y carga con Locust (`PLAN.md` §11).
- **PR:** CI en verde, 1 revisión de otro integrante y `docs/ESTADO.md` actualizado.

## 5. Lo que nunca va al repo

- API keys, `token.json`, `credentials.json` ni cualquier `.env`.
- **Hojas de vida reales.** En `samples/` solo van HV sintéticas, inventadas (Ley 1581).
- Bases de datos locales (`*.db`) ni la carpeta `uploads/`.

Si subes algo por error, avisa en el grupo **de inmediato**. Una key filtrada se revoca y se crea otra.

## 6. Dudas

Escribe en el grupo o deja la pregunta en la sección **Bloqueos** de `docs/ESTADO.md`. Las decisiones que tomemos van a la sección **Decisiones** del mismo archivo, para que nadie pierda el contexto.
