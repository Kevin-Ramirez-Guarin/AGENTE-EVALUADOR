"""Pruebas de carga del Agente Evaluador.

Uso (backend levantado con una BD y uploads desechables; EVALUADOR=falso evita llamar a Gemini):
    cd backend && .venv/Scripts/activate
    DATABASE_URL=sqlite:///./carga.db UPLOADS_DIR=./carga_uploads EVALUADOR=falso \
        uvicorn app.main:app --port 8001
    locust -f ../load/locustfile.py --host http://localhost:8001                 # UI en :8089
    locust -f ../load/locustfile.py --host http://localhost:8001 \
        --headless -u 20 -r 5 -t 60s                                             # corrida headless

Flujo nuevo: POST /postulaciones responde 201 en_evaluacion y la evaluación termina en segundo
plano, así que tras postular se consulta GET /evaluaciones/{id} hasta que deje de estar en
evaluación. Cada POST crea una postulación real: usa una BD desechable.
"""
import time
from pathlib import Path

from locust import HttpUser, between, task

# Con capa de texto: la API valida el PDF al momento (un PDF vacío daría 422).
PDF = (Path(__file__).resolve().parent.parent / "samples" / "hv_backend_fuerte_1.pdf").read_bytes()
ESPERA_MAX_S = 30


class Reclutador(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def vacantes(self):
        self.client.get("/vacantes")

    @task(3)
    def evaluaciones(self):
        self.client.get("/evaluaciones")

    @task(1)
    def postular(self):
        with self.client.post(
            "/postulaciones",
            data={"vacante_id": "backend-jr", "nombre": "Carga Prueba",
                  "email": "carga@example.com", "consentimiento": "true"},
            files={"pdf": ("hv.pdf", PDF, "application/pdf")},
            catch_response=True,
        ) as r:
            if r.status_code != 201 or r.json().get("estado") != "en_evaluacion":
                r.failure(f"respuesta inesperada: {r.status_code}")
                return
            evaluacion_id = r.json()["evaluacion_id"]
        self._esperar_resultado(evaluacion_id)

    def _esperar_resultado(self, evaluacion_id: int):
        limite = time.monotonic() + ESPERA_MAX_S
        while time.monotonic() < limite:
            with self.client.get(f"/evaluaciones/{evaluacion_id}", name="/evaluaciones/{id}",
                                 catch_response=True) as r:
                estado = r.json().get("estado") if r.status_code == 200 else None
                if estado == "error_evaluacion":
                    r.failure("la evaluación terminó en error_evaluacion")
                if estado != "en_evaluacion":
                    return
            time.sleep(0.5)
