# Celonis MCP Adoption Roadmap

## Overall Status

**Not Started** · Last updated: 2026-03-20

---

## Objective

Integrate the Celonis **Agent Tools (MCP) Asset** into Delivery Forge workflows so that AI agents can securely access Process Intelligence data, trigger actions in external systems, and write decisions back to Celonis — all within the existing governance framework.

---

## Scope

- Setting up and publishing a Celonis Agent Tools (MCP) Asset.
- Authentication baseline for production (OAuth 2.0) and local development (Application Key).
- Designing and exposing the first set of high-value tools (process context retrieval, KPI lookup, action triggers, feedback write-back).
- Connecting at least one reference MCP client and validating end-to-end tool execution.
- Defining operational governance: rate limiting, monitoring, permission hygiene, and rollout gates.

## Non-Goals

- Replacing existing Foundry governance review flows or any `POST /reviews/*` and `POST /celonis/*` backend contracts.
- Implementing a full SSO/OIDC provider; Celonis OAuth endpoints are used as the auth server.
- Managing the Celonis platform tenant administration beyond what is needed for MCP asset permissions.
- Shipping AI/LLM orchestration code in this repository (the MCP Layer is the interface contract only).

---

## Key Terms

| Term | Definition |
|---|---|
| **Agent Tools (MCP) Asset** | A Celonis asset type that encapsulates a named collection of tools exposed to AI agents via JSON-RPC 2.0 or OpenAPI. |
| **MCP Client** | Any MCP-compatible client (e.g. Claude Desktop, Postman, custom app) that connects to the MCP Server URL to discover and execute tools. |
| **MCP Server URL** | The published asset endpoint: `https://[team].[realm].celonis.cloud/studio-copilot/api/v1/mcp-servers/mcp/[mcp-server-id]` |
| **Tool** | A named function with a defined input/output schema callable by AI agents through the MCP Server. |
| **OAuth scope** | `mcp-asset.tools:execute` — required scope for all connections. |

---

## Progress Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Blocked — see notes |

---

## Phase 1 — Foundation and Access

> **Status: Not Started**  
> **Blocks:** Phase 2 and Phase 3 setup.  
> **Owner:** Technical Lead

### Prerequisites

- [ ] Confirm a Celonis account with Agent Tools (MCP) Asset feature enabled for the team.
- [ ] Identify a Celonis team URL (`https://[team].[realm].celonis.cloud`).
- [ ] Confirm administrative access to create OAuth clients or Application Keys on the team.
- [ ] Identify an MCP-compatible client to use for initial validation (e.g. Postman).

### Asset Creation and Publishing

- [ ] Log in to Celonis Studio and navigate to the target package.
- [ ] Create a new asset of type **Agent Tools (MCP) Asset** (MCP Server).
- [ ] Add at minimum one tool to the asset configuration (can be a placeholder for schema testing).
- [ ] Publish the asset and copy the generated **MCP Server URL**.
- [ ] Record the MCP Server URL in team configuration notes.

### Authentication Setup

- [ ] **Option A — OAuth 2.0 (production path):** Create an OAuth Client with:
  - Grant type: `Client Credentials` (server-to-server and automated workflows).
  - Authentication method: `Client Secret` (client secret basic or post).
  - Scope: `mcp-asset.tools:execute`.
  - Save the Client ID and Client Secret securely.
- [ ] **Option B — Application Key (dev/test path only):** Create an Application Key for local testing.
  - Save the key securely. **Do not use in production.**
- [ ] Grant the **"use" permission** to the OAuth Client / Application Key on the published Agent Tools (MCP) Asset.

### Connectivity Baseline

- [ ] Perform a first MCP connection attempt from the reference client.
  - For OAuth 2.0: exchange credentials at `https://[team].[realm].celonis.cloud/oauth2/token` and confirm a token is returned.
  - For Application Key: set `Authorization: Bearer [key]` header.
- [ ] Confirm the client can list the published asset's tools (tool discovery works).
- [ ] Record the validated MCP Server URL and auth method in team notes.

---

## Phase 2 — Tool Surface Design

> **Status: Not Started**  
> **Depends on:** Phase 1 (connection baseline available).  
> **Can run partially in parallel with Phase 3 preparation.**  
> **Owner:** Technical Lead

### Business-Aligned Tool Inventory

Prioritize tools covering each of the four Celonis MCP goal areas:

- [ ] **Search / context retrieval**: define a tool that queries Celonis knowledge bases or data models for relevant process context (e.g. asset metadata lookup, process variant search).
- [ ] **KPI and insights retrieval**: define a tool that returns real-time process metrics, KPIs, or bottleneck summaries for a given project or asset scope.
- [ ] **External action trigger**: define a tool that triggers a specific action in an external system based on process intelligence output (e.g. escalation notification, task creation).
- [ ] **Write-back / feedback loop**: define a tool that writes an agent decision or annotation back to Celonis to improve future process execution (e.g. flagging a recommendation, updating a process attribute).

### Schema and Naming Conventions

- [ ] Agree on a naming convention for tools (e.g. `get_`, `list_`, `trigger_`, `write_` prefixes).
- [ ] Define input/output schema expectations for each tool:
  - Required vs. optional fields.
  - Data types and validation constraints.
  - Error response format (align with existing Foundry API error conventions).
- [ ] Document tool descriptions clearly enough for AI agent auto-discovery (descriptions are used by agents for tool selection).

### Transport Path Decision

- [ ] For each planned tool and MCP client, decide which calling path to use:
  - **MCP Protocol (JSON-RPC):** use when the client supports native MCP tool discovery and execution (e.g. Postman MCP Request, Claude Desktop).
  - **OpenAPI tool calling:** use when the client or platform expects an OpenAPI contract. Access the generated spec via the "Use OpenAPI instead" button in Studio and import into the target client.
- [ ] Record the decision per client type in this document or a linked configuration note.

---

## Phase 3 — Client Integration and Validation

> **Status: Not Started**  
> **Depends on:** Phase 1 completed, Phase 2 tool definitions agreed.  
> **Owner:** Integration Lead

### Reference Client Configuration

- [ ] Configure one reference MCP client with all connection details:
  - MCP Server URL.
  - OAuth 2.0 credentials: Access Token URL, Client ID, Client Secret, scope `mcp-asset.tools:execute`.
  - (Or Application Key bearer token for local testing only.)
- [ ] Confirm the client can successfully connect and retrieve the list of available tools.

### Happy-Path Validation

- [ ] Execute each tool defined in Phase 2 with a representative input and verify the response matches the expected schema.
- [ ] Confirm write-back tool results appear correctly in the Celonis platform.
- [ ] Record baseline response times for each tool call.

### Troubleshooting Checklist

When a connection or tool call fails, verify in order:

- [ ] Asset is published and the saved MCP Server URL is correct.
- [ ] OAuth Client / Application Key has 'use' permission on the asset explicitly granted.
- [ ] OAuth Client scope is exactly `mcp-asset.tools:execute`.
- [ ] Token URL and authorization URL match the team's realm: `https://[team].[realm].celonis.cloud/oauth2/token`.
- [ ] Client ID and Client Secret have not been regenerated since the connection was configured.
- [ ] For OpenAPI calling: the tool endpoint format is `…/mcp-servers/mcp/[mcp-server-id]/tool-api/[tool-id]`.

---

## Phase 4 — Operational Hardening

> **Status: Not Started**  
> **Depends on:** Phases 1–3 completed and validated.  
> **Owner:** Technical Lead + Integration Lead

### Rate Limiting and Usage Strategy

- [ ] Document the default rate limit: **500 calls per minute per asset**.
- [ ] Identify workflows that may burst above this threshold and design batching or queuing at the consumer side.
- [ ] Add a note in any integration code or agent configuration warning against tight polling loops.

### Monitoring and Incident Checklist

- [ ] Define a minimum monitoring baseline:
  - Alert when tool call error rate exceeds an agreed threshold.
  - Alert when token refresh consistently fails (OAuth 2.0 path).
- [ ] Document the incident response steps (revoke and re-issue Application Key or re-generate OAuth Client Secret, re-grant permissions, verify URL).
- [ ] Confirm Celonis platform logging for the MCP Asset is reviewed in post-incident reviews.

### Rollout Gates for Production

- [ ] Production connections **must** use OAuth 2.0 (not Application Key); enforce this in team configuration process.
- [ ] OAuth Client Secret stored only in secure secret management (not in `.env` committed to version control).
- [ ] Verified tool schemas annotated and reviewed by a second team member (4-eyes, consistent with Foundry governance).
- [ ] Tool descriptions reviewed to ensure no PII or internal-only context leaks through the tool discovery interface.
- [ ] Final sign-off from the same delivery lead role used for Foundry asset approvals.

---

## Next 3 Actions

> Update this section after each work session.

1. Confirm Celonis account has Agent Tools (MCP) Asset enabled (Phase 1 prerequisite).
2. Identify the target Studio package and create the first Agent Tools (MCP) Asset.
3. Decide OAuth 2.0 or Application Key for the initial dev validation and create the credential.

---

## Progress Log

| Date | Update | Author |
|---|---|---|
| 2026-03-20 | Roadmap created from Celonis MCP Asset documentation review. All phases set to Not Started. | Delivery Forge |

---

## References

- [Celonis Agent Tools (MCP) Asset — Overview](https://developer.celonis.com/mcp-server-asset/overview/)
- [Celonis Agent Tools (MCP) Asset — Getting Started](https://developer.celonis.com/mcp-server-asset/getting-started/)
- [Celonis Agent Tools (MCP) Asset — Glossary](https://developer.celonis.com/mcp-server-asset/glossary/)
- [Extension Integration Contract](extension-integration.md) — security/trust-boundary patterns for companion integrations
- [ADR 0001: Foundry MVP Architecture](adr/0001-mvp-architecture.md) — architectural constraints this roadmap operates within
