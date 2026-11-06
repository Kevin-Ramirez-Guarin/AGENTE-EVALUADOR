import json
from pathlib import Path

from app.models import Vacante

VACANTES = Path(__file__).resolve().parent.parent / "data" / "vacantes.json"


def test_vacantes_json_carga_cinco_validas():
    vacantes = [Vacante(**v) for v in json.loads(VACANTES.read_text(encoding="utf-8"))]
    assert len(vacantes) == 5
    assert len({v.id for v in vacantes}) == 5


def test_vacantes_json_describen_el_rol_en_giveaway():
    for v in json.loads(VACANTES.read_text(encoding="utf-8")):
        vacante = Vacante(**v)
        assert vacante.descripcion and vacante.equipo and vacante.ubicacion and vacante.modalidad, v["id"]
