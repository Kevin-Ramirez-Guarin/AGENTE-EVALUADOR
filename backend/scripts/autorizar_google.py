"""Autoriza Gmail y Calendar una sola vez y guarda `backend/token.json`.

Pasos previos en Google Cloud Console:
  1. Habilita Gmail API y Google Calendar API en tu proyecto.
  2. Crea la pantalla de consentimiento OAuth en modo "Testing" y agrega tu correo
     como usuario de prueba.
  3. Crea un cliente OAuth de tipo "App de escritorio", descárgalo y guárdalo como
     `backend/credentials.json` (está en .gitignore; nunca lo subas).

Uso (desde backend/):  python scripts/autorizar_google.py
Se abre el navegador; al aceptar, se escribe `token.json`.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from app.google_apis import CREDENTIALS_PATH, SCOPES, TOKEN_PATH  # noqa: E402


def main() -> None:
    if not CREDENTIALS_PATH.exists():
        sys.exit(f"Falta {CREDENTIALS_PATH}. Sigue los pasos del docstring de este script.")
    creds = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH), SCOPES).run_local_server(port=0)
    # Permisos 0o600 desde la creación: el token da acceso al Gmail del usuario.
    fd = os.open(TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN_PATH, 0o600)  # si el archivo ya existía con otros permisos
    print(f"Listo: token guardado en {TOKEN_PATH}")


if __name__ == "__main__":
    main()
