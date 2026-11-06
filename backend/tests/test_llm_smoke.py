import pytest

from scripts.smoke_gemini import HV_SINTETICA, extraer_perfil

from app.models import PerfilCandidato


@pytest.mark.llm
def test_gemini_devuelve_perfil_estructurado():
    perfil = extraer_perfil(HV_SINTETICA)
    assert isinstance(perfil, PerfilCandidato)
    assert perfil.habilidades_tecnicas
