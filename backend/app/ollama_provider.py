import requests
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaProvider:
    def __init__(self, model: str = "mistral:latest"):
        self.model = model
        self.base_url = "http://localhost:11434"

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                return self.model in model_names
            return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def complete_messages(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        timeout: int = 120  # Increased timeout for complex book generation tasks
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2048,  # Max tokens for book content
                "top_p": 0.9,
                "top_k": 40
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            result = response.json()
            return result["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise Exception("Local model request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama")
            raise Exception("Cannot connect to local Ollama server")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Local model error: {e}")