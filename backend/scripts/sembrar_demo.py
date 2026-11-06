"""Siembra el panel para ensayar la demo: sube las HV sintéticas de samples/ por la API pública.

Usa el mismo endpoint y los mismos campos que el portal (POST /postulaciones), con las identidades
sintéticas de samples/esperado.json y consentimiento=true. La HV escaneada se omite (da 422) salvo
que se pida con --solo. Las HV sin vacante en el golden van a backend-jr.

Uso (desde backend/, con el backend corriendo):
    python -m scripts.sembrar_demo [--url http://localhost:8000] [--solo hv_injection.pdf]
"""
import argparse
import json
from collections.abc import Callable
from pathlib import Path

import httpx

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
VACANTE_POR_DEFECTO = "backend-jr"


def sembrar(url: str, enviar: Callable = httpx.post, solo: str | None = None) -> list[tuple[str, int, dict]]:
    golden = json.loads((SAMPLES / "esperado.json").read_text(encoding="utf-8"))
    if solo is not None and solo not in golden:
        raise ValueError(f"{solo} no está en samples/esperado.json")
    archivos = [solo] if solo else [a for a, e in golden.items() if "error" not in e]
    resultados = []
    for archivo in archivos:
        g = golden[archivo]
        r = enviar(f"{url.rstrip('/')}/postulaciones",
                   data={"vacante_id": g["vacante"] or VACANTE_POR_DEFECTO, "nombre": g["nombre"],
                         "email": g.get("correo", "demo@example.com"), "consentimiento": "true"},
                   files={"pdf": (archivo, (SAMPLES / archivo).read_bytes(), "application/pdf")})
        resultados.append((archivo, r.status_code, _cuerpo(r)))
    return resultados


def _cuerpo(r) -> dict | str:
    try:
        return r.json()
    except ValueError:  # un 500 de Starlette llega en texto plano
        return r.text


def main(argv: list[str] | None = None, enviar: Callable = httpx.post) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--solo", help="sube solo este archivo de samples/ (ej. hv_injection.pdf)")
    args = ap.parse_args(argv)
    try:
        resultados = sembrar(args.url, enviar, args.solo)
    except httpx.HTTPError as exc:
        print(f"No hay backend en {args.url} ({type(exc).__name__}). ¿Corriste uvicorn?")
        return 1
    except ValueError as exc:
        ap.error(str(exc))
    for archivo, status, cuerpo in resultados:
        print(f"{status}  {archivo}: {cuerpo}")
    return 0 if all(s == 201 for _, s, _ in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
