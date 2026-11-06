"""Contratos de datos (PLAN.md §4 y §6). Cambian solo con PR revisado por los tres."""
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

Puntaje = Annotated[float, Field(ge=0, le=100)]
Peso = Annotated[float, Field(ge=0, le=1)]
NivelEducativo = Literal["bachiller", "tecnico", "tecnologo", "profesional", "posgrado"]


class Idioma(BaseModel):
    idioma: str
    nivel: str


class Habilidad(BaseModel):
    nombre: str
    nivel: Literal["basico", "intermedio", "avanzado"]
    evidencia: str  # cita textual de la HV


class PerfilCandidato(BaseModel):
    habilidades_tecnicas: list[Habilidad]
    habilidades_blandas: list[Habilidad]
    anios_experiencia: float
    nivel_educativo: NivelEducativo
    idiomas: list[Idioma]
    fortalezas: list[str] = Field(max_length=3)
    debilidades: list[str] = Field(max_length=3)  # áreas de mejora, redacción respetuosa
    resumen: str


class Pesos(BaseModel):
    tecnico: Peso
    experiencia: Peso
    blandas: Peso
    educacion: Peso
    idiomas: Peso

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
    idiomas: list[Idioma]
    pesos: Pesos


class Veredicto(str, Enum):
    ENTREVISTA = "ENTREVISTA"
    REVISION_HUMANA = "REVISION_HUMANA"
    NO_CONTINUA = "NO_CONTINUA"


class CriterioDetalle(BaseModel):
    """Desglose explicable de un criterio (derecho a la explicación, PLAN.md §7)."""
    criterio: Literal["tecnico", "experiencia", "blandas", "educacion", "idiomas"]
    puntaje: Puntaje
    peso: Peso
    cumplidos: list[str] = []
    faltantes: list[str] = []
    evidencias: list[str] = []
    nota: str


class ResultadoEvaluacion(BaseModel):
    puntaje_total: Puntaje
    puntajes_por_criterio: dict[str, Puntaje]
    veredicto_sugerido: Veredicto
    cumple_obligatorios: bool
    explicacion: str
    mejor_vacante_alternativa: str | None = None  # id de otra vacante con ≥ 75
    criterios: list[CriterioDetalle] = []  # cambio aditivo: detalle por criterio
