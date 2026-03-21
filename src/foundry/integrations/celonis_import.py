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


@dataclass
class CelonisPreflightHttpResult:
    service: str
    probe_path: str
    probe_url: str
    has_token: bool
    request_attempted: bool
    reachable: bool
    authenticated: bool
    permission_status: str
    status_code: int | None
    error: str | None
    response_preview: str


class CelonisGateway:
    SERVICE_DEFAULT_PROBES = {
        "core": "/",
        "process-mining": "/process-mining/api/teams",
        "data-integration": "/integration/api/pools",
        "studio": "/studio/api/spaces",
        "apps": "/apps/api/packages",
    }

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

    def preflight(
        self,
        *,
        tenant_base_url: str,
        probe_path: str = "/",
        service: str = "core",
    ) -> CelonisPreflightHttpResult:
        normalized_base = self._normalize_base_url(tenant_base_url)
        normalized_service = self._normalize_service(service)
        default_probe = self.SERVICE_DEFAULT_PROBES[normalized_service]
        requested_probe = probe_path.strip() if probe_path else ""
        effective_probe = requested_probe or default_probe
        normalized_path = self._normalize_path(effective_probe)
        probe_url = f"{normalized_base}{normalized_path}"

        if not self._settings.celonis_api_token:
            return CelonisPreflightHttpResult(
                service=normalized_service,
                probe_path=normalized_path,
                probe_url=probe_url,
                has_token=False,
                request_attempted=False,
                reachable=False,
                authenticated=False,
                permission_status="missing-token",
                status_code=None,
                error="FORGE_CELONIS_API_TOKEN is not configured",
                response_preview="",
            )

        try:
            with httpx.Client(timeout=self._settings.celonis_timeout_seconds) as client:
                response = client.get(probe_url, headers=self._headers())
        except Exception as exc:
            return CelonisPreflightHttpResult(
                service=normalized_service,
                probe_path=normalized_path,
                probe_url=probe_url,
                has_token=True,
                request_attempted=True,
                reachable=False,
                authenticated=False,
                permission_status="unreachable",
                status_code=None,
                error=str(exc),
                response_preview="",
            )

        permission_status = self._permission_status(response.status_code)
        is_authenticated = response.status_code not in {401, 403}

        return CelonisPreflightHttpResult(
            service=normalized_service,
            probe_path=normalized_path,
            probe_url=probe_url,
            has_token=True,
            request_attempted=True,
            reachable=True,
            authenticated=is_authenticated,
            permission_status=permission_status,
            status_code=response.status_code,
            error=None,
            response_preview=self._build_response_preview(response),
        )

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

    def _normalize_service(self, service: str) -> str:
        candidate = (service or "core").strip().lower()
        if candidate in self.SERVICE_DEFAULT_PROBES:
            return candidate
        return "core"

    @staticmethod
    def _permission_status(status_code: int) -> str:
        if 200 <= status_code < 300:
            return "authorized"
        if status_code == 401:
            return "unauthorized"
        if status_code == 403:
            return "forbidden"
        if status_code == 404:
            return "not-found"
        if 400 <= status_code < 500:
            return "client-error"
        if 500 <= status_code < 600:
            return "server-error"
        return "unknown"

    @staticmethod
    def _to_result(*, action: str, url: str, response: httpx.Response) -> CelonisHttpResult:
        return CelonisHttpResult(
            action=action,
            url=url,
            status_code=response.status_code,
            ok=response.is_success,
            response_preview=CelonisGateway._build_response_preview(response),
        )

    @staticmethod
    def _build_response_preview(response: httpx.Response) -> str:
        body = response.text
        if len(body) > 1200:
            body = f"{body[:1200]}..."
        try:
            parsed = response.json()
            body = json.dumps(parsed, ensure_ascii=False)[:1200]
        except Exception:
            pass
        return body
