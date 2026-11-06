import pytest

from app import config


@pytest.fixture(autouse=True)
def _sin_dotenv(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)


def test_sin_api_key_da_error_claro(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        config.get_api_key()


def test_con_api_key_la_devuelve(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "abc")
    assert config.get_api_key() == "abc"


def test_modelo_por_defecto_y_override(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert config.get_model() == "gemini-3.1-flash-lite"
    monkeypatch.setenv("GEMINI_MODEL", "otro")
    assert config.get_model() == "otro"
