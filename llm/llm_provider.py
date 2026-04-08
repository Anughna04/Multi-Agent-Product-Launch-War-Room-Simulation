import os
import requests
from abc import ABC, abstractmethod
from utils.logger import logger

try:
    import ollama
except ImportError:
    ollama = None

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        if ollama is None:
            raise ImportError("ollama package is not installed. Run 'pip install ollama'")

    def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            response = ollama.chat(model=self.model_name, messages=messages)
            return response['message']['content']
        except Exception as e:
            logger.error(f"[OllamaProvider] Error generating response: {e}")
            raise

class LLMFactory:
    @staticmethod
    def _is_ollama_available() -> bool:
        logger.info("[LLMFactory] Checking Ollama availability...")
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def get_provider() -> LLMProvider:
        if not LLMFactory._is_ollama_available():
            logger.error("[LLMFactory] Ollama is not available.")
            raise RuntimeError("Ollama is not running or model not available. Please start Ollama and pull llama3.2.")
        
        logger.info("[LLMFactory] Using LLaMA 3.2 (local)")
        return OllamaProvider(model_name="llama3.2")
