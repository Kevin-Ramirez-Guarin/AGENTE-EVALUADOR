"""Pruebas de carga del Agente Evaluador.

Uso (con el backend levantado en http://localhost:8000):
    cd backend && .venv/Scripts/activate && pip install -r requirements.txt
    uvicorn app.main:app
    locust -f ../load/locustfile.py --host http://localhost:8000            # UI en :8089
    locust -f ../load/locustfile.py --host http://localhost:8000 \
        --headless -u 5 -r 5 -t 10s                                         # corrida de humo

Cada usuario reparte su tiempo entre GET /vacantes, GET /evaluaciones y POST /postulaciones
(con un PDF mínimo). Usa una BD desechable: cada POST crea una postulación real.
"""
from locust import HttpUser, between, task

PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


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
        self.client.post(
            "/postulaciones",
            data={"vacante_id": "backend-jr", "nombre": "Carga Prueba",
                  "email": "carga@example.com", "consentimiento": "true"},
            files={"pdf": ("hv.pdf", PDF_MINIMO, "application/pdf")},
        )
