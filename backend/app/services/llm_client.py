from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMClient(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        pass
