"""Cliente HTTP da ExerciseDB; não faz scraping nem downloads de mídia."""

import os
import time
from typing import Any

import httpx

from src.exercise_db.schemas import ExerciseDbExercise
from src.infrastructure.config import settings


class ExerciseDbClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, *, timeout: float | None = None,
                 transport: httpx.BaseTransport | None = None, max_retries: int = 2, sleep: Any = time.sleep) -> None:
        self.base_url = (base_url or os.getenv("EXERCISEDB_API_BASE_URL") or settings.exercisedb_api_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else (os.getenv("EXERCISEDB_API_KEY") or settings.exercisedb_api_key)
        self.max_retries, self._sleep = max_retries, sleep
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
            headers["api-key"] = self.api_key
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout or settings.exercisedb_api_timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ExerciseDbClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        for attempt in range(self.max_retries + 1):
            response = self._client.get(path, params=params)
            if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
                response.raise_for_status()
                return response.json()
            if attempt == self.max_retries:
                response.raise_for_status()
            self._sleep(float(response.headers.get("Retry-After", 2 ** attempt)))
        raise RuntimeError("retry inesperado")

    @staticmethod
    def _items(payload: Any) -> list[ExerciseDbExercise]:
        raw = payload if isinstance(payload, list) else payload.get("data", payload.get("exercises", [])) if isinstance(payload, dict) else []
        if isinstance(raw, dict):
            raw = raw.get("data", raw.get("exercises", []))
        return [ExerciseDbExercise.from_api(item) for item in raw if isinstance(item, dict)]

    def list_exercises(self, page: int = 1, limit: int = 100) -> list[ExerciseDbExercise]:
        return self._items(self._get("/exercises", {"page": page, "limit": limit}))

    def get_exercise_by_id(self, external_id: str) -> ExerciseDbExercise:
        return ExerciseDbExercise.from_api(self._get(f"/exercises/{external_id}"))

    def search_exercises(self, *, name: str | None = None, body_part: str | None = None,
                         target: str | None = None, equipment: str | None = None,
                         page: int = 1, limit: int = 100) -> list[ExerciseDbExercise]:
        params = {key: value for key, value in {"name": name, "bodyPart": body_part, "target": target, "equipment": equipment, "page": page, "limit": limit}.items() if value is not None}
        return self._items(self._get("/exercises", params))