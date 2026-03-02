import json
from dataclasses import dataclass

import httpx

from foundry.settings import Settings


@dataclass
class CelonisHttpResult:
    action: str
    url: str
    status_code: int
    ok: bool
    response_preview: str


class CelonisGateway:
    def __init__(self, settings: Settings):
        self._settings = settings

    def extract(self, *, tenant_base_url: str, source_path: str) -> CelonisHttpResult:
        normalized_base = self._normalize_base_url(tenant_base_url)
        normalized_path = self._normalize_path(source_path)
        url = f"{normalized_base}{normalized_path}"
        with httpx.Client(timeout=self._settings.celonis_timeout_seconds) as client:
            response = client.get(url, headers=self._headers())
        return self._to_result(action="extract", url=url, response=response)

    def import_data(self, *, tenant_base_url: str, target_path: str, payload: dict) -> CelonisHttpResult:
        normalized_base = self._normalize_base_url(tenant_base_url)
        normalized_path = self._normalize_path(target_path)
        url = f"{normalized_base}{normalized_path}"
        with httpx.Client(timeout=self._settings.celonis_timeout_seconds) as client:
            response = client.post(url, headers=self._headers(), json=payload)
        return self._to_result(action="import", url=url, response=response)

    def _headers(self) -> dict:
        if not self._settings.celonis_api_token:
            raise ValueError("FORGE_CELONIS_API_TOKEN is not configured")
        return {
            "Authorization": f"Bearer {self._settings.celonis_api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        base = value.strip().rstrip("/")
        if base.startswith("http://") or base.startswith("https://"):
            return base
        return f"https://{base}"

    @staticmethod
    def _normalize_path(value: str) -> str:
        path = value.strip()
        if not path:
            return "/"
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/"):
            return path
        return f"/{path}"

    @staticmethod
    def _to_result(*, action: str, url: str, response: httpx.Response) -> CelonisHttpResult:
        body = response.text
        if len(body) > 1200:
            body = f"{body[:1200]}..."
        try:
            parsed = response.json()
            body = json.dumps(parsed, ensure_ascii=False)[:1200]
        except Exception:
            pass
        return CelonisHttpResult(
            action=action,
            url=url,
            status_code=response.status_code,
            ok=response.is_success,
            response_preview=body,
        )
