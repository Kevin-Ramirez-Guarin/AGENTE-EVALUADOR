import os

from dotenv import load_dotenv

DEFAULT_MODEL = "gemini-3.1-flash-lite"


def get_api_key() -> str:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta GEMINI_API_KEY: defínela en backend/.env (ver .env.example).")
    return key


def get_model() -> str:
    load_dotenv()
    return os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
