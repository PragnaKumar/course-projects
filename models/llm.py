from langchain_ollama import ChatOllama

DEFAULT_MODEL = "qwen2.5:7b"
OLLAMA_BASE_URL = "http://localhost:11434"

def get_llm(temperature: float = 0.2, model : str = DEFAULT_MODEL):
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=OLLAMA_BASE_URL
    )