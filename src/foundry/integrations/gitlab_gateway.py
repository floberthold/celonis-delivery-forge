import json
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from foundry.settings import Settings


@dataclass
class GitLabPipelineResult:
    pipeline_id: int
    status: str
    ref: str
    web_url: str | None


class GitLabGateway:
    def __init__(self, settings: Settings):
        self._settings = settings

    def trigger_pipeline(
        self,
        *,
        repo_path: str,
        ref: str,
        variables: dict,
        token_override: str | None = None,
    ) -> GitLabPipelineResult:
        encoded_path = quote(repo_path.strip(), safe="")
        url = f"{self._normalize_base_url()}/api/v4/projects/{encoded_path}/pipeline"
        payload: dict[str, object] = {"ref": ref}
        if variables:
            payload["variables"] = [{"key": key, "value": str(value)} for key, value in variables.items()]
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=self._headers(token_override), json=payload)

        if response.status_code >= 500:
            raise Exception(f"GitLab trigger failed with status {response.status_code}")
        if response.status_code >= 400:
            raise ValueError(self._response_preview(response))

        body = response.json()
        return GitLabPipelineResult(
            pipeline_id=int(body.get("id")),
            status=str(body.get("status", "pending")),
            ref=str(body.get("ref", ref)),
            web_url=body.get("web_url"),
        )

    def get_pipeline_status(
        self,
        *,
        repo_path: str,
        pipeline_id: int,
        token_override: str | None = None,
    ) -> GitLabPipelineResult:
        encoded_path = quote(repo_path.strip(), safe="")
        url = f"{self._normalize_base_url()}/api/v4/projects/{encoded_path}/pipelines/{pipeline_id}"
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers(token_override))

        if response.status_code >= 500:
            raise Exception(f"GitLab status check failed with status {response.status_code}")
        if response.status_code >= 400:
            raise ValueError(self._response_preview(response))

        body = response.json()
        return GitLabPipelineResult(
            pipeline_id=int(body.get("id", pipeline_id)),
            status=str(body.get("status", "unknown")),
            ref=str(body.get("ref", "")),
            web_url=body.get("web_url"),
        )

    def list_pipelines(
        self,
        *,
        repo_path: str,
        ref: str | None = None,
        per_page: int = 10,
        token_override: str | None = None,
    ) -> list[GitLabPipelineResult]:
        encoded_path = quote(repo_path.strip(), safe="")
        url = f"{self._normalize_base_url()}/api/v4/projects/{encoded_path}/pipelines"
        params: dict[str, str | int] = {"per_page": per_page}
        if ref:
            params["ref"] = ref

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._headers(token_override), params=params)

        if response.status_code >= 500:
            raise Exception(f"GitLab list pipelines failed with status {response.status_code}")
        if response.status_code >= 400:
            raise ValueError(self._response_preview(response))

        results: list[GitLabPipelineResult] = []
        for row in response.json():
            results.append(
                GitLabPipelineResult(
                    pipeline_id=int(row.get("id")),
                    status=str(row.get("status", "unknown")),
                    ref=str(row.get("ref", "")),
                    web_url=row.get("web_url"),
                )
            )
        return results

    def _headers(self, token_override: str | None) -> dict[str, str]:
        token = (token_override or self._settings.gitlab_api_token or "").strip()
        if not token:
            raise ValueError("FORGE_GITLAB_API_TOKEN is not configured")
        return {
            "PRIVATE-TOKEN": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _normalize_base_url(self) -> str:
        value = self._settings.gitlab_base_url.strip().rstrip("/")
        if not value:
            raise ValueError("FORGE_GITLAB_BASE_URL is not configured")
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return f"https://{value}"

    @staticmethod
    def _response_preview(response: httpx.Response) -> str:
        body = response.text
        if len(body) > 1200:
            body = f"{body[:1200]}..."
        try:
            parsed = response.json()
            body = json.dumps(parsed, ensure_ascii=False)[:1200]
        except Exception:
            pass
        return body
