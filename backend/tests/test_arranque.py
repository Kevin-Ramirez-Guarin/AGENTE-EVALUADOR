import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

# Subproceso: importar app.main dentro del proceso de pruebas no se puede repetir.
CODIGO = """
import dotenv
llamadas = []
dotenv.load_dotenv = lambda *a, **k: llamadas.append(a or k) or True
import app.main
print(len(llamadas), llamadas[0] if llamadas else None)
"""


def test_main_carga_el_env_del_backend_al_arrancar():
    salida = subprocess.run([sys.executable, "-c", CODIGO], cwd=BACKEND, capture_output=True, text=True, check=True)
    n, args = salida.stdout.strip().split(" ", 1)
    assert int(n) >= 1, "app.main no llamó a load_dotenv: EVALUADOR/MODO_EVALUACION del .env se ignoran"
    assert str(BACKEND / ".env") in args
