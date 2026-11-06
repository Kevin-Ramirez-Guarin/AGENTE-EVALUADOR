import pytest

from app import config, llm


def test_get_llm_sin_key_falla_claro(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.get_llm()


def test_get_llm_construye_sin_red(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-falsa")
    modelo = llm.get_llm()
    assert modelo.vertexai is True
    assert modelo.model.endswith(config.get_model())
