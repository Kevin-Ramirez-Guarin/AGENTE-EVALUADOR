from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_api_key, get_model


def get_llm() -> ChatGoogleGenerativeAI:
    # `api_key` es el alias de `google_api_key` (verificado en langchain-google-genai 4.4.3)
    return ChatGoogleGenerativeAI(model=get_model(), api_key=get_api_key(), vertexai=True)
