"""Cliente HTTP síncrono e resiliente para a API pública do Hevy."""

import os
import time
from typing import Any

import httpx

from src.infrastructure.config import settings


class HevyApiError(httpx.HTTPStatusError):
    """Erro HTTP enriquecido com o endpoint solicitado."""


class HevyClient:
    """Cliente de leitura do catálogo Hevy autenticado por ``api-key``."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.BaseTransport | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("HEVY_API_BASE_URL")
            or os.getenv("HEVY_BASE_URL")
            or settings.hevy_api_base_url
            or "https://api.hevyapp.com"
        ).rstrip("/")
        self.api_key = api_key or os.getenv("HEVY_API_KEY") or settings.hevy_api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"api-key": self.api_key or ""},
            timeout=self.timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HevyClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Executa GET e aplica backoff para respostas temporárias 429."""
        for attempt in range(self.max_retries + 1):
            response = self._client.get(endpoint, params=params)
            if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise HevyApiError(str(exc), request=exc.request, response=exc.response) from exc
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError(f"Resposta inválida em {endpoint}: objeto JSON esperado")
                return payload

            if attempt == self.max_retries:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            self._sleep(delay)

        raise RuntimeError("Fluxo de retry inesperadamente encerrado")

    def get_exercise_templates(self, page: int = 1) -> dict[str, Any]:
        return self._get("/v1/exercise_templates", {"page": page})

    def get_routine_folders(self, page: int = 1) -> dict[str, Any]:
        return self._get("/v1/routine_folders", {"page": page})

    def get_routines(self, page: int = 1) -> dict[str, Any]:
        return self._get("/v1/routines", {"page": page})

    def post(self, endpoint: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Executa escrita com chave de idempotência e retry somente para 429."""
        headers = {"Idempotency-Key": idempotency_key}
        for attempt in range(self.max_retries + 1):
            response = self._client.post(endpoint, json=payload, headers=headers)
            if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError(f"Resposta inválida em {endpoint}: objeto JSON esperado")
                return data
            if attempt == self.max_retries:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            self._sleep(float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt)
        raise RuntimeError("Fluxo de retry inesperadamente encerrado")
