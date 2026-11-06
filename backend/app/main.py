import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_engine
from app.models import Vacante

VACANTES_PATH = Path(__file__).resolve().parent.parent / "data" / "vacantes.json"

@asynccontextmanager
async def lifespan(_app):
    get_engine()  # crea las tablas al arrancar, antes de atender peticiones concurrentes
    yield


app = FastAPI(title="Agente Evaluador", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def _cargar_vacantes() -> list[Vacante]:
    return [Vacante(**v) for v in json.loads(VACANTES_PATH.read_text(encoding="utf-8"))]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/vacantes", response_model=list[Vacante])
def listar_vacantes():
    return _cargar_vacantes()


@app.get("/vacantes/{vacante_id}", response_model=Vacante)
def obtener_vacante(vacante_id: str):
    for v in _cargar_vacantes():
        if v.id == vacante_id:
            return v
    raise HTTPException(status_code=404, detail="Vacante no encontrada")


from app.routes import router  # noqa: E402  (routes usa _cargar_vacantes de este módulo)

app.include_router(router)
