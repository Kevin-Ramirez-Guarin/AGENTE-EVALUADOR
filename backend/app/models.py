"""Contratos de datos (PLAN.md §4 y §6). Cambian solo con PR revisado por los tres."""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

NivelEducativo = Literal["bachiller", "tecnico", "tecnologo", "profesional", "posgrado"]


class Habilidad(BaseModel):
    nombre: str
    nivel: Literal["basico", "intermedio", "avanzado"]
    evidencia: str  # cita textual de la HV


class PerfilCandidato(BaseModel):
    habilidades_tecnicas: list[Habilidad]
    habilidades_blandas: list[Habilidad]
    anios_experiencia: float
    nivel_educativo: NivelEducativo
    idiomas: list[dict]  # {idioma, nivel}
    fortalezas: list[str] = Field(max_length=3)
    debilidades: list[str] = Field(max_length=3)  # áreas de mejora, redacción respetuosa
    resumen: str


class Pesos(BaseModel):
    tecnico: float
    experiencia: float
    blandas: float
    educacion: float
    idiomas: float

    @model_validator(mode="after")
    def _suman_uno(self):
        total = sum(self.model_dump().values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"los pesos deben sumar 1.0 (suman {total})")
        return self


class Vacante(BaseModel):
    id: str
    titulo: str
    requisitos_obligatorios: list[str]
    deseables: list[str]
    blandas: list[str]
    experiencia_min_anios: float
    nivel_educativo_min: NivelEducativo
    idiomas: list[dict]  # {idioma, nivel}
    pesos: Pesos


class Veredicto(str, Enum):
    ENTREVISTA = "ENTREVISTA"
    REVISION_HUMANA = "REVISION_HUMANA"
    NO_CONTINUA = "NO_CONTINUA"


class ResultadoEvaluacion(BaseModel):
    puntaje_total: float
    puntajes_por_criterio: dict[str, float]
    veredicto_sugerido: Veredicto
    cumple_obligatorios: bool
    explicacion: str
    mejor_vacante_alternativa: str | None = None  # id de otra vacante con ≥ 75
