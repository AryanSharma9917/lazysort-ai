from typing import Any

import httpx


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = {item.get("name") for item in response.json().get("models", [])}
        except (httpx.HTTPError, ValueError):
            return {"status": "ollama_unavailable", "model": self.model}
        ready = self.model in models or any(name and name.split(":")[0] == self.model for name in models)
        return {"status": "ready" if ready else "model_unavailable", "model": self.model}

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json={
                "model": self.model, "prompt": prompt, "stream": False, "format": "json",
                "options": {"temperature": 0.1},
            })
            response.raise_for_status()
            return response.json()["response"]
