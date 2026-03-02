# Extension Integration Contract (Prepared)

This document defines the backend contracts for a future browser extension that adds in-page controls on Celonis pages.

## Scope

- The extension is optional.
- Core behavior already works via Foundry dashboard companion forms.
- Extension should only call stable backend APIs and must not bypass Foundry governance.

## Backend Endpoints

- `GET /celonis/connections`
- `POST /celonis/connections/upsert`
- `POST /celonis/extract`
- `POST /celonis/import`

## Payload Contracts

### Upsert connection

```json
{
  "client_id": "<uuid>",
  "tenant_base_url": "https://team.eu-1.celonis.cloud",
  "is_active": true
}
```

### Extract

```json
{
  "client_id": "<uuid>",
  "source_path": "/process-mining/api/teams"
}
```

### Import

```json
{
  "client_id": "<uuid>",
  "target_path": "/process-mining/api/teams",
  "payload": {"name": "foundry-import"}
}
```

## Security and Trust Boundary

- Tokens remain backend-side in `FORGE_CELONIS_API_TOKEN`.
- Extension should never store Celonis API secrets.
- Extension should send only minimal context and action intent to backend.

## Next Build Step

- Add authenticated extension-to-backend session flow.
- Add explicit per-user authorization in backend before permitting `/celonis/*` actions.
- Replace placeholder content script badge with real action buttons and overlays tied to page context.
