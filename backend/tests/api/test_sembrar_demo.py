"""Siembra de la demo: sube las HV sintéticas por la API pública, como el portal."""
import json
from pathlib import Path

import pytest

from scripts.sembrar_demo import VACANTE_POR_DEFECTO, main, sembrar

SAMPLES = Path(__file__).resolve().parents[3] / "samples"
GOLDEN = json.loads((SAMPLES / "esperado.json").read_text(encoding="utf-8"))
CON_TEXTO = [a for a, e in GOLDEN.items() if "error" not in e]


class PosterFalso:
    """Registra lo que se enviaría al backend y responde 201."""

    def __init__(self, status=201):
        self.envios, self.status = [], status

    def __call__(self, url, data, files):
        self.envios.append((url, data, files))
        status = self.status
        return type("R", (), {"status_code": status,
                              "json": lambda _self: {"evaluacion_id": 1, "estado": "en_evaluacion"}})()


def test_sube_las_hv_con_texto_con_identidad_sintetica_y_consentimiento():
    poster = PosterFalso()
    resultados = sembrar("http://localhost:8000/", enviar=poster)
    assert [a for a, _, _ in resultados] == CON_TEXTO
    for (url, data, files), archivo in zip(poster.envios, CON_TEXTO):
        g = GOLDEN[archivo]
        assert url == "http://localhost:8000/postulaciones"
        assert data == {"vacante_id": g["vacante"] or VACANTE_POR_DEFECTO, "nombre": g["nombre"],
                        "email": g["correo"], "consentimiento": "true"}
        assert files["pdf"] == (archivo, (SAMPLES / archivo).read_bytes(), "application/pdf")


def test_solo_sube_un_archivo():
    poster = PosterFalso()
    sembrar("http://x", enviar=poster, solo="hv_injection.pdf")
    assert len(poster.envios) == 1 and poster.envios[0][2]["pdf"][0] == "hv_injection.pdf"


def test_solo_con_archivo_desconocido_falla():
    with pytest.raises(ValueError):
        sembrar("http://x", enviar=PosterFalso(), solo="no_existe.pdf")


def test_main_resume_y_sale_1_si_algo_falla(capsys):
    assert main(["--solo", "hv_debil.pdf"], enviar=PosterFalso()) == 0
    assert main([], enviar=PosterFalso(status=422)) == 1
    assert "422" in capsys.readouterr().out


def test_main_sin_backend_da_mensaje_claro(capsys):
    import httpx

    def caido(*_a, **_k):
        raise httpx.ConnectError("rechazada")

    assert main(["--url", "http://localhost:9"], enviar=caido) == 1
    assert "localhost:9" in capsys.readouterr().out


def test_contra_la_api_real_crea_postulaciones(client):
    """Mismo endpoint y campos que el portal: el backend acepta todo lo sembrado."""
    resultados = sembrar("", enviar=lambda url, data, files: client.post(url, data=data, files=files))
    assert {s for _, s, _ in resultados} == {201}
    assert len(client.get("/evaluaciones").json()) == len(CON_TEXTO)
