from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi.responses import RedirectResponse


def with_query_params(path: str, **params: str | None) -> str:
    parts = urlsplit(path)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return urlunsplit(("", "", parts.path or "/", urlencode(query), parts.fragment))


def redirect_dashboard(*, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=with_query_params("/dashboard", ok=ok), status_code=303)
    if err:
        return RedirectResponse(url=with_query_params("/dashboard", err=err), status_code=303)
    return RedirectResponse(url="/dashboard", status_code=303)


def redirect_ui(path: str, *, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        return RedirectResponse(url=with_query_params(path, ok=ok), status_code=303)
    if err:
        return RedirectResponse(url=with_query_params(path, err=err), status_code=303)
    return RedirectResponse(url=path, status_code=303)
