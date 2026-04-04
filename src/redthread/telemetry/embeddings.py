"""Text Embeddings Client for Telemetry (Phase 4.5).

Provides a lightweight, dependency-free (no PyTorch/sentence-transformers) 
interface to generate embeddings by calling the backend provider directly
(Ollama or OpenAI).
"""

from __future__ import annotations

import logging
from typing import Any

from redthread.config.settings import RedThreadSettings, TargetBackend

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Generates vector embeddings for text using the target's backend."""

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self.backend = settings.target_backend
        self.base_url = settings.target_base_url
        self.api_key = settings.openai_api_key

        # Decide on embedding model based on backend
        if settings.telemetry_embedding_model:
            self.model = settings.telemetry_embedding_model
        elif self.backend == TargetBackend.OLLAMA:
            # Fallback to a standard resident model confirmed in 'ollama list'
            self.model = "llama3.2:3b"
        else:
            self.model = "text-embedding-3-small"

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        if not text.strip():
            return []

        if self.settings.dry_run:
            import random
            # Return a deterministic random vector of dim 1536
            random.seed(hash(text))
            base = [random.uniform(-1, 1) for _ in range(1536)]
            norm = sum(x*x for x in base) ** 0.5
            return [x/norm for x in base]

        if self.backend == TargetBackend.OLLAMA:
            return await self._embed_ollama(text)
        elif self.backend == TargetBackend.OPENAI:
            return await self._embed_openai(text)
        else:
            raise NotImplementedError(f"Embeddings not supported for {self.backend}")

    async def _embed_ollama(self, text: str) -> list[float]:
        """Call Ollama /v1/embeddings (OpenAI-compatible) endpoint."""
        import httpx
        
        # Using /v1/embeddings is the most robust way to support both native models and proxies
        url = f"{self.base_url.rstrip('/')}/v1/embeddings"
        payload = {
            "model": self.model,
            "input": text,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            # /v1/embeddings returns {'data': [{'embedding': [...]}]}
            return data["data"][0]["embedding"]  # type: ignore[no-any-return]

    async def _embed_openai(self, text: str) -> list[float]:
        """Call OpenAI /v1/embeddings API."""
        import httpx
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]  # type: ignore[no-any-return]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts sequentially or batched if supported."""
        import asyncio
        if self.backend == TargetBackend.OPENAI and not self.settings.dry_run:
            # OpenAI supports batch embeddings natively
            import httpx
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "input": texts,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
        
        # Fallback to concurrent single calls
        return await asyncio.gather(*(self.embed(t) for t in texts))
