import json
import httpx
from typing import Dict, Any
from fastapi import HTTPException
from app.core.config import settings
from app.services.llm_client import LLMClient

class OllamaLLMClient(LLMClient):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.OLLAMA_MODEL

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                response_text = data.get("response", "")
                
                if not response_text:
                    raise HTTPException(status_code=500, detail="Empty response from LLM")
                    
                return json.loads(response_text)
                
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Ollama connection error: {str(e)}")
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="LLM returned invalid JSON")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=502, detail=f"LLM API error: {e.response.status_code}")

llm_client = OllamaLLMClient()
