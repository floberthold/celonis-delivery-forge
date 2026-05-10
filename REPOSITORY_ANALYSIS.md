# Celonis Delivery Forge - Complete Repository Analysis

**Last Updated:** May 10, 2026  
**Project Version:** 0.1.0  
**Status:** Active Development  
**Python Version:** 3.11+

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Complete Directory Structure](#complete-directory-structure)
3. [Programming Languages & File Types](#programming-languages--file-types)
4. [Architecture Overview](#architecture-overview)
5. [Key Components & Relationships](#key-components--relationships)
6. [Core Technology Stack](#core-technology-stack)
7. [Database Schema Overview](#database-schema-overview)
8. [API Routes & Endpoints](#api-routes--endpoints)
9. [Integration Points](#integration-points)
10. [Build & Deployment](#build--deployment)
11. [Testing Framework](#testing-framework)
12. [Documentation System](#documentation-system)
13. [External Dependencies & Submodules](#external-dependencies--submodules)
14. [Configuration & Runtime Modes](#configuration--runtime-modes)
15. [Key Entry Points](#key-entry-points)

---

## Project Overview

### Purpose & Vision

**Celonis Delivery Forge** is a dual-control governance framework for multi-tenant Celonis implementations. It serves as a delivery operating system built for consultants, teams, and organizations working with Celonis.

**Core Motto:** "Every asset is forged. Every change is reviewed. Nothing reaches production without two hammers."

### Target Model

- **Individual users** have their own workspace, preferences, and personal agent support
- **Organizations** provide the shared tenant, billing boundary, and collaboration space
- **Clients, projects, assets, reviews, templates, and agents** live within the organization context
- **AI agents** support reasoning and automation at personal, shared, and project scope

### MVP Scope

✅ Project and client registry  
✅ Asset ownership and membership tracking  
✅ 4-eyes review flow (submit → approve/request changes)  
✅ Timeline view for project and asset activity  
✅ Topic pages with inline create/edit/delete operations  
✅ Local accounts with JWT login  
✅ Read-only Celonis import adapter (stub)  
✅ Companion Celonis actions (connect, extract, import)  
✅ Extension-ready backend contracts  

🚧 SaaS multi-tenancy foundation (in progress)  
📋 Agent model and orchestration layer (planned)  
📋 Subscriptions and billing (planned)  

---

## Complete Directory Structure

```
celonis-delivery-forge/
├── Root Configuration & Build Files
│   ├── README.md                          # Main project README
│   ├── QUICKSTART.md                      # Quick start guide
│   ├── STARTUP.md                         # Detailed startup guide
│   ├── STARTUP_CHECKLIST.md               # Pre-flight checklist
│   ├── IMPLEMENTATION_SUMMARY.md          # Implementation details
│   ├── pyproject.toml                     # Python package configuration
│   ├── mkdocs.yml                         # MkDocs documentation config
│   ├── docker-compose.yml                 # Docker Compose services
│   ├── Dockerfile                         # Container image definition
│   ├── alembic.ini                        # Database migration config
│   ├── foundry.db.pre_browser_demo.bak    # Backup database file
│   ├── FoundryDesktop.spec                # PyInstaller desktop spec
│   ├── START.ps1                          # PowerShell startup script
│   ├── START.bat                          # Batch startup script
│   └── analyze_demand.py                  # Demand forecasting analysis
│
├── src/                                   # Main source code
│   └── foundry/                           # Primary package
│       ├── __init__.py
│       ├── models.py                      # SQLModel database models & enums
│       ├── schemas.py                     # Pydantic schemas for API
│       ├── settings.py                    # Application settings/configuration
│       ├── security.py                    # Authentication & security
│       ├── db.py                          # Database initialization & utilities
│       │
│       ├── api/                           # FastAPI application
│       │   ├── main.py                    # FastAPI app entry point, ASGI config
│       │   ├── deps.py                    # Dependency injection utilities
│       │   │
│       │   └── routes/                    # 27+ API route modules
│       │       ├── auth.py                # Authentication (login, register, password reset)
│       │       ├── users.py               # User/person management
│       │       ├── orgs.py                # Organization management
│       │       ├── clients.py             # Client management
│       │       ├── projects.py            # Project management
│       │       ├── assets.py              # Asset management
│       │       ├── reviews.py             # 4-eyes review workflow
│       │       ├── templates.py           # Template library management
│       │       ├── timeline.py            # Activity timeline
│       │       ├── todos.py               # Todo/task management
│       │       ├── files.py               # File storage & retrieval
│       │       ├── kpis.py                # KPI definitions
│       │       ├── kpi_book.py            # KPI book/catalog
│       │       ├── snapshots.py           # Asset snapshots
│       │       ├── use_cases.py           # Use-case library
│       │       ├── forum_insights.py      # Forum insight tracking
│       │       ├── quests.py              # Agent quest management
│       │       ├── celonis.py             # Celonis integration
│       │       ├── celonis_marketplace.py # Celonis marketplace
│       │       ├── celonis_deployments.py # Celonis deployment tracking
│       │       ├── gitlab.py              # GitLab integration
│       │       ├── local_knowledge.py     # Local knowledge gateway
│       │       ├── ingest.py              # Data ingestion
│       │       ├── tool_hub.py            # Tool hub management
│       │       ├── florian_assets.py      # Custom asset routes (Florian's work)
│       │       ├── ui.py                  # UI helper endpoints
│       │       └── __init__.py
│       │
│       ├── services/                      # Business logic & integrations (25+ services)
│       │   ├── activity_log.py            # Activity logging
│       │   ├── celonis_contracts.py       # Celonis API contracts
│       │   ├── celonis_data_agent_service.py  # Celonis data agent client
│       │   ├── celonis_deployment_service.py  # Deployment management
│       │   ├── celonis_payload_extractors.py  # Payload parsing
│       │   ├── email_service.py           # Email notifications
│       │   ├── feature_rollout.py         # Feature flag service
│       │   ├── ingest_service.py          # Data ingestion pipeline
│       │   ├── local_knowledge_gateway.py # Knowledge base integration
│       │   ├── project_service.py         # Project operations
│       │   ├── quest_service.py           # Quest/agent operations
│       │   ├── review_service.py          # Review workflow
│       │   ├── snapshot_service.py        # Asset snapshot management
│       │   ├── snapshot_coverage_service.py # Snapshot coverage analysis
│       │   ├── snapshot_export_service.py # Snapshot export
│       │   ├── snapshot_git_service.py    # Git-based snapshot storage
│       │   ├── snapshot_detail_extractors.py # Snapshot detail parsing
│       │   ├── template_service.py        # Template operations
│       │   ├── template_seed.py           # Template initialization
│       │   ├── todo_service.py            # Todo management
│       │   ├── use_case_views.py          # Use-case aggregation
│       │   ├── florian_script_seed.py     # Custom data seeding
│       │   ├── trycelonis_demo_rebuild.py # Demo data generation
│       │   └── __pycache__/
│       │
│       ├── ui/                            # Web UI templates & static
│       │   ├── static/
│       │   │   ├── app.css                # Main stylesheet
│       │   │   └── orchestration_map.js   # Orchestration visualization
│       │   │
│       │   └── templates/                 # 40+ Jinja2 HTML templates
│       │       ├── base.html              # Base layout template
│       │       ├── dashboard.html         # Main dashboard
│       │       ├── login.html             # Authentication UI
│       │       ├── register.html          # User registration
│       │       ├── forgot_password.html   # Password recovery
│       │       ├── account.html           # User account settings
│       │       ├── workspace.html         # User workspace
│       │       ├── tenant.html            # Tenant/organization view
│       │       ├── people.html            # People/users management
│       │       ├── clients.html           # Client list
│       │       ├── client_health.html     # Client health dashboard
│       │       ├── client_overview.html   # Client detail view
│       │       ├── projects.html          # Projects list
│       │       ├── project_overview.html  # Project detail
│       │       ├── assets.html            # Assets list
│       │       ├── asset_detail.html      # Asset detail
│       │       ├── reviews.html           # Review workflow UI
│       │       ├── templates.html         # Template library
│       │       ├── timeline.html          # Activity timeline
│       │       ├── todos.html             # Task/todo management
│       │       ├── files.html             # File manager
│       │       ├── kpis.html              # KPI dashboard
│       │       ├── kpi_book.html          # KPI catalog
│       │       ├── snapshots.html         # Snapshots list
│       │       ├── snapshot_detail.html   # Snapshot detail
│       │       ├── sales.html             # Sales dashboard
│       │       ├── foundry_admin.html     # Admin panel
│       │       ├── agentic-methodology.html # Agentic workflow UI
│       │       ├── celonis_setup_wizard.html # Celonis setup flow
│       │       ├── celonis_discovery.html # Celonis discovery
│       │       ├── celonis_credentials.html # Credential management
│       │       ├── celonis_token_admin.html # Token administration
│       │       ├── celonis_deployments.html # Deployment tracking UI
│       │       ├── celonis_tool_hub.html  # Tool hub interface
│       │       ├── celonis-tool-hub-ui.html # Alternative tool hub UI
│       │       ├── gitlab_repo_overview.html # GitLab integration UI
│       │       ├── local-knowledge-ui.html # Knowledge base UI
│       │       ├── orchestration.html     # Orchestration view
│       │       ├── person_overview.html   # Person/user detail
│       │       └── __pycache__/
│       │
│       ├── desktop/                       # Desktop app launcher
│       │   ├── app.py                     # Desktop application entry point
│       │   └── __pycache__/
│       │
│       ├── integrations/                  # External system integrations
│       │   ├── celonis_import.py          # Celonis import/export
│       │   ├── gitlab_gateway.py          # GitLab API client
│       │   └── __pycache__/
│       │
│       ├── mcp/                           # Model Context Protocol (MCP) servers
│       │   ├── _stub_server.py            # MCP stub server
│       │   ├── agentic_test_runner.py     # Test runner MCP
│       │   ├── agentic_bug_ledger.py      # Bug tracking MCP
│       │   ├── agentic_evidence.py        # Evidence retrieval MCP
│       │   ├── agentic_deployment_readiness.py # Deployment readiness MCP
│       │   └── __pycache__/
│       │
│       └── __pycache__/
│
├── tests/                                 # Test suite (40+ test files)
│   ├── conftest.py                        # Pytest configuration & fixtures
│   ├── e2e/                               # End-to-end tests
│   │   └── __init__.py
│   ├── test_account_ui.py                 # Account page UI tests
│   ├── test_login_ui.py                   # Login flow tests
│   ├── test_dashboard_celonis_preflight_ui.py # Dashboard tests
│   ├── test_client_health_ui.py           # Client health tests
│   ├── test_people_ui.py                  # People management tests
│   ├── test_assets_ui_florian_import.py   # Asset import tests
│   ├── test_asset_detail.py               # Asset detail tests
│   ├── test_celonis_ui_route_presence.py  # Celonis UI routing
│   ├── test_celonis_marketplace_api.py    # Marketplace API tests
│   ├── test_celonis_extract_import_api.py # Extract/import tests
│   ├── test_celonis_deployments_api.py    # Deployment API tests
│   ├── test_celonis_token_admin_ui.py     # Token management tests
│   ├── test_celonis_tool_hub_ui.py        # Tool hub UI tests
│   ├── test_celonis_preflight_api.py      # Preflight API tests
│   ├── test_celonis_user_token_api.py     # User token API tests
│   ├── test_snapshots_api.py              # Snapshot API tests
│   ├── test_snapshot_detail_extraction.py # Snapshot detail tests
│   ├── test_kpi_ui.py                     # KPI UI tests
│   ├── test_use_case_views_api.py         # Use-case API tests
│   ├── test_quests_api.py                 # Quest API tests
│   ├── test_methodology_ui.py             # Methodology UI tests
│   ├── test_tenant_setup_wizard_ui.py     # Tenant setup tests
│   ├── test_tool_hub_ui.py                # Tool hub tests
│   ├── test_tool_hub_registry_local_knowledge.py # Registry tests
│   ├── test_tool_hub_profile_activation.py # Profile activation tests
│   ├── test_local_knowledge_ui.py         # Local knowledge tests
│   ├── test_local_knowledge_gateway_service.py # Gateway tests
│   ├── test_local_wiki_query_contract_live.py # Wiki query tests
│   ├── test_open_webui_local_knowledge_launcher.py # Open WebUI tests
│   ├── test_ingest_repo_sync_api.py       # Ingestion tests
│   ├── test_foundry_admin_ui.py           # Admin UI tests
│   ├── test_florian_assets_api.py         # Custom asset tests
│   ├── test_client_project_tokens.py      # Token tests
│   ├── test_mcp_stub_modules.py           # MCP stub tests
│   ├── test_agentic_mcp_tools.py          # Agentic MCP tests
│   ├── test_startup_db_policy.py          # Startup policy tests
│   ├── test_trycelonis_demo_rebuild.py    # Demo rebuild tests
│   ├── test_ui_datetime_sorting.py        # UI utility tests
│   ├── test_ui_domain_profile_gating.py   # Profile gating tests
│   ├── test_docs_site_routes.py           # Docs site tests
│   ├── test_e2e_artifact_helpers.py       # E2E artifact helpers
│   └── __pycache__/
│
├── alembic/                               # Database migrations (Alembic)
│   ├── env.py                             # Alembic environment config
│   ├── script.py.mako                     # Migration template
│   └── versions/                          # Migration files (20+ migrations)
│       ├── 20260302_0001_add_template_tables.py
│       ├── 20260303_0002_add_todo_table.py
│       ├── 20260319_0003_add_delivery_files.py
│       ├── 20260319_0003_expand_todo_collaboration.py
│       ├── 20260320_0004_add_organization_tables.py
│       ├── 20260321_0004_add_use_case_library_and_roadmap.py
│       ├── 20260321_0006_add_forum_insight_tracking.py
│       ├── 20260321_0007_add_ingest_tracking_tables.py
│       ├── 20260321_0008_add_snapshot_engine_and_kpi_book.py
│       ├── 20260321_0008_add_gitlab_ci_tables.py
│       ├── 20260321_0009_add_salesforce_url_to_client_project.py
│       ├── 20260321_0011_scope_core_entities_by_organization.py
│       ├── 20260321_0012_add_agent_and_quest_orchestration_tables.py
│       ├── 20260322_0014_add_snapshot_expanded_artifact_tables.py
│       ├── 20260322_0015_add_project_celonis_links_and_user_tokens.py
│       ├── 20260322_0016_add_celonis_deployment_requests.py
│       ├── 20260322_0017_add_client_and_project_tokens.py
│       └── ... (and more)
│
├── agentic/                               # Agentic/agent orchestration
│   ├── README.md                          # Agentic framework docs
│   │
│   └── tool-hub/                          # Tool hub orchestration
│       ├── start_tool_hub.ps1             # Tool hub startup script
│       ├── tool_hub_registry.json         # Central tool registry
│       │   └── Tools defined:
│       │       - foundry-api (core platform)
│       │       - celonis-data-agent-mcp (Celonis agent)
│       │       - local-wiki-query-api (knowledge hub)
│       │       - agentic-test-runner-mcp (quality automation)
│       │       - agentic-bug-ledger-mcp (quality automation)
│       │       - agentic-evidence-mcp (quality automation)
│       │       - agentic-deployment-readiness-mcp (quality automation)
│       │       - local-knowledge-gateway (knowledge hub)
│       │       - open-webui (knowledge hub)
│       │
│       └── tool_hub_profiles.json        # Runtime activation profiles
│           └── Profiles defined:
│               - full (all tools)
│               - pilot-core (core only)
│               - pilot-core-plus-knowledge (core + knowledge)
│               - integration-celonis (core + Celonis agent)
│
├── docs/                                  # Documentation source (MkDocs)
│   ├── index.md                           # Docs index
│   ├── master-roadmap.md                  # Master product roadmap
│   ├── agent-orchestration-operating-model.md # Agent orchestration model
│   ├── agent-feature-roadmap.md           # Agent feature roadmap
│   ├── agent-orchestrators-roadmap.md     # Orchestrator roadmap
│   ├── celonis-asset-manifest.txt         # Celonis asset manifest
│   ├── celonis-assets-analysis.md         # Assets analysis
│   ├── celonis-assets-roadmap.md          # Assets roadmap
│   ├── celonis-forum-insights-roadmap.md  # Forum insights roadmap
│   ├── celonis-mcp-roadmap.md             # MCP roadmap
│   ├── celonis-snapshot-coverage-matrix.md # Coverage matrix
│   ├── consultant-agent-pack.md           # Consultant pack docs
│   ├── dev-roadmap.md                     # Development roadmap
│   ├── domain-submodule-local-first-replatform.md # Platform docs
│   ├── extension-integration.md           # Extension documentation
│   ├── open-source-submodule-workflow.md  # Open source workflow
│   ├── roadmap-celonis.md                 # Celonis roadmap
│   ├── roadmap-use-cases.md               # Use-case roadmap
│   ├── rts-orchestration-roadmap.md       # RTS orchestration roadmap
│   │
│   ├── admin/                             # Admin documentation
│   │   ├── index.md
│   │   ├── full-setup.md
│   │   ├── runtime-modes.md
│   │   ├── user-provisioning-and-roles.md
│   │   ├── operations-checklist.md
│   │   ├── backup-and-recovery.md
│   │   └── incident-playbooks.md
│   │
│   ├── developer/                         # Developer documentation
│   │   ├── index.md
│   │   ├── docs-architecture.md
│   │   ├── integrations.md
│   │   ├── local-development.md
│   │   ├── architecture.md
│   │   ├── module-map.md
│   │   ├── data-models-and-migrations.md
│   │   ├── auth-and-access-control.md
│   │   └── testing.md
│   │
│   ├── guides/                            # Guides
│   │   ├── delivery-walkthrough.md
│   │   ├── account-flows.md
│   │   └── action-flow-templates.md
│   │
│   ├── user/                              # User documentation
│   │   ├── index.md
│   │   ├── account-and-security.md
│   │   ├── core-workspaces.md
│   │   ├── action-flow-templates.md
│   │   ├── governance-and-reviews.md
│   │   ├── kpi-and-snapshots.md
│   │   └── route-reference.md
│   │
│   ├── troubleshooting/                   # Troubleshooting guides
│   ├── templates/                         # Documentation templates
│   ├── adr/                               # Architecture Decision Records
│   ├── stylesheets/                       # Custom CSS for docs
│   └── __pycache__/
│
├── docs_site/                             # Built documentation (auto-generated)
│   ├── index.html
│   ├── 404.html
│   ├── sitemap.xml
│   ├── admin/, assets/, developer/, getting-started/, guides/, etc.
│   └── (Complete HTML documentation site)
│
├── docu/                                  # Legacy HTML documentation
│   ├── developer.html
│   ├── user.html
│   ├── guide-delivery-walkthrough.html
│   ├── guide-admin-setup.html
│   ├── guide-action-flow-templates.html
│   ├── guide-account-flows.html
│   └── (Legacy documentation endpoints)
│
├── extension/                             # Chrome extension (companion)
│   ├── manifest.json                      # Extension manifest (MV3)
│   │   └── Permissions: storage, activeTab, scripting
│   │   └── Host perms: *.celonis.cloud/*, 127.0.0.1:8000/*
│   │
│   └── src/
│       ├── background.js                  # Service worker
│       └── content.js                     # Content script
│
├── build/                                 # Build artifacts
│   └── FoundryDesktop/
│       └── (Bundled desktop application)
│
├── config/                                # Configuration files
│   └── ui_rollout_profiles.json           # UI feature rollout config
│
├── scripts/                               # Utility & automation scripts
│   ├── dev.ps1                            # Developer utilities (PowerShell)
│   ├── dev.bat                            # Developer utilities (CMD)
│   ├── build_desktop.ps1                  # Desktop app builder
│   ├── build_standalone.ps1               # Standalone builder
│   ├── run_standalone.bat                 # Standalone runner
│   ├── run_standalone.vbs                 # Standalone launcher
│   ├── run_standalone_debug.bat           # Debug runner
│   ├── run_forum_weekly_intake.ps1        # Forum intake automation
│   ├── start_local_knowledge_gateway.ps1  # Knowledge gateway starter
│   ├── start_open_webui_local_knowledge.ps1 # OpenWebUI launcher
│   ├── start_tool_hub.ps1                 # Tool hub launcher
│   ├── new_agent_run.ps1                  # Agent run creator
│   ├── new_consultant_agent_run.ps1       # Consultant agent runner
│   ├── close_agent_run.ps1                # Agent run closer
│   ├── list_agent_runs.ps1                # Agent run lister
│   ├── analyze_demand_forecasting.py      # Demand forecasting
│   ├── analyze_demand_forecasting_local.py # Local forecasting
│   ├── seed_forum_insights.py             # Forum insight seeding
│   ├── seed_use_cases.py                  # Use-case seeding
│   ├── trycelonis_demo_apps.py            # Demo app generator
│   ├── update_forum_intake_log.py         # Forum log updater
│   ├── validate_action_flow_templates.py  # Template validation
│   ├── repo_cleanup.ps1                   # Cleanup utilities
│   ├── add_upstream_submodule.ps1         # Submodule management
│   ├── sync_florian_submodules.ps1        # Submodule sync
│   ├── debug_package_extraction.py        # Debug utilities
│   └── __pycache__/
│
├── data/                                  # Data directories
│   ├── input/                             # Input data
│   └── generated/                         # Generated data
│
├── developer/                             # Developer resources
│   └── action_flow_templates/             # Action flow specifications
│       ├── specs/                         # Template specifications (15+ templates)
│       │   ├── weekly-steering-pack-refresh.json
│       │   ├── subscription-event-materialized-sync.json
│       │   ├── subscription-event-client-comms-draft.json
│       │   ├── stale-incomplete-execution-watchdog.json
│       │   ├── recommendation-human-approval-gate.json
│       │   ├── process-anomaly-escalation-chain.json
│       │   ├── priority-case-auto-routing.json
│       │   ├── nightly-km-recommendation-sync.json
│       │   ├── low-confidence-ai-triage-review-loop.json
│       │   ├── kpi-threshold-alert-to-task-and-notify.json
│       │   ├── data-quality-breach-stopline.json
│       │   ├── closed-loop-action-effectiveness-feedback.json
│       │   └── (More templates)
│       │
│       ├── schema/
│       │   └── action-flow-template.schema.json # Schema definition
│       │
│       └── catalog/
│           └── template-catalog.json      # Template catalog index
│
├── external resources/                    # External code & documentation
│   ├── Code from Celonis/                 # Celonis reference code
│   │   ├── swagger.json
│   │   ├── image-processing/
│   │   ├── dm-load-optimization/
│   │   ├── m-20-ocpm-bootstrapper/
│   │   └── ... (Reference implementations)
│   │
│   ├── Code by Florian/                   # Florian's implementations
│   │   └── celonis-data-agent/            # Celonis data agent (MCP server)
│   │
│   ├── Projects at Work/                  # Work projects
│   │   └── pyCelonis-tools/               # PyCelonis tooling
│   │
│   └── local-knowledge-model/             # Local knowledge model
│       └── obsidian-llm-wiki-local/       # Obsidian wiki integration
│
├── uploads/                               # User uploads directory
│
├── site_docs/                             # MkDocs source (alternative path)
│   ├── index.md
│   ├── getting-started/
│   ├── user/
│   ├── admin/
│   ├── developer/
│   ├── guides/
│   └── ...
│
└── .orchestration/                        # Tool hub runtime state
    └── tool-hub/
        ├── test-probe/                    # Test probe directory
        ├── registry.json                  # Runtime registry
        ├── profiles.json                  # Runtime profiles
        └── (Tool logs & state)
```

---

## Programming Languages & File Types

### Primary Languages

| Language | Usage | Count | Key Files |
|----------|-------|-------|-----------|
| **Python** | Backend, API, Services, Scripts, Tests | ~464 files | `.py` |
| **HTML** | UI Templates, Documentation | ~46 files | `.html` (Jinja2) |
| **CSS** | Styling | 3 files | `app.css`, `extra.css` |
| **JavaScript** | Browser Extension, Client Scripts | 3 files | `.js` (content, background, orchestration) |
| **JSON** | Configuration, Registry, Schemas | 38 files | `.json` |
| **YAML** | Documentation, Config | 1 file | `mkdocs.yml` |
| **SQL** | Database Migrations | Embedded in Python | `.py` via Alembic |
| **Markdown** | Documentation | 20+ files | `.md` |

### File Type Distribution

- **Python Scripts**: ~464 files
  - Source code: `src/foundry/`
  - Tests: `tests/`
  - Database migrations: `alembic/versions/`
  - Utility scripts: `scripts/`
  - Analysis scripts: Root `.py` files

- **HTML/Templates**: ~46 files
  - Main UI: `src/foundry/ui/templates/`
  - Legacy docs: `docu/`
  - Built docs: `docs_site/`
  - MkDocs source: `site_docs/`

- **Configuration Files**: 38 JSON files
  - Tool hub: `agentic/tool-hub/`
  - Feature flags: `config/`
  - Action flow templates: `developer/action_flow_templates/`

- **Documentation**: 20+ Markdown files
  - Developer guides: `docs/`
  - Roadmaps: `docs/`
  - Setup guides: Root `.md` files

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Web UI (Jinja2 Templates)                               │   │
│  │  • Dashboard • Projects • Assets • Reviews • KPIs •      │   │
│  │  • Snapshots • Timeline • People • Celonis Integration   │   │
│  └──────────────────────────────────────────────────────────┘   │
│         ↑ HTTP/HTTPS                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Chrome Extension Companion (MV3)                        │   │
│  │  • Injected Celonis.cloud controls                       │   │
│  │  • Event forwarding to Foundry API                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ↓ HTTP/HTTPS (127.0.0.1:8000)
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Routes (27 modules)                                │    │
│  │  • Auth (JWT) • Users • Organizations • Clients         │    │
│  │  • Projects • Assets • Reviews • Templates              │    │
│  │  • Timeline • Todos • Files • KPIs • Snapshots          │    │
│  │  • Use-cases • Forum-insights • Quests • Celonis        │    │
│  │  • GitLab • Local-knowledge • Ingest • Tool-hub         │    │
│  └─────────────────────────────────────────────────────────┘    │
│         ↓ (Requests/Responses)                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Services Layer (25+ service modules)                   │    │
│  │  • Business logic & orchestration                       │    │
│  │  • External integrations                                │    │
│  │  • Data transformations                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         ↓ Database / Integration
┌─────────────────────────────────────────────────────────────────┐
│                    Persistence Layer                            │
│  ┌──────────────────┐      ┌──────────────────────────────┐    │
│  │  SQLModel ORM    │      │  External Integrations       │    │
│  │  (SQLAlchemy)    │      │  • Celonis API / MCP         │    │
│  └──────────────────┘      │  • GitLab Gateway            │    │
│         ↓                  │  • Local Knowledge Gateway    │    │
│  ┌──────────────────┐      │  • Email Service             │    │
│  │ PostgreSQL / DB  │      └──────────────────────────────┘    │
│  │ (Container)      │                                          │
│  └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘

Tool Hub Layer (Optional - Domain-Scoped Startup)
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                          │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Tool Registry   │    │  Tool Profiles   │                  │
│  │  (tool_hub_      │    │  (activation)    │                  │
│  │   registry.json) │    │                  │                  │
│  └──────────────────┘    └──────────────────┘                  │
│         ↓                         ↓                             │
│  ┌───────────────────────────────────────────────────────┐    │
│  │  Managed Processes                                    │    │
│  │  • Foundry API (core-platform domain)                │    │
│  │  • Celonis Data Agent MCP (celonis-agent domain)     │    │
│  │  • Local Knowledge Gateway (knowledge-hub domain)    │    │
│  │  • Quality Automation MCP servers (phase 2/3)        │    │
│  │  • OpenWebUI (knowledge-hub domain)                  │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

Desktop Mode (Optional)
┌─────────────────────────────────────────────────────────────────┐
│  Desktop Launcher (foundry.desktop.app)                         │
│  • Local HTTP server (127.0.0.1:8000)                           │
│  • SQLite database (AppData\Local\CelonisDeliveryForge)          │
│  • Auto-browser launch on startup                               │
│  • Graceful shutdown handling                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Tenant Organization Scoping

The architecture implements **organization-scoped multi-tenancy**:

```
┌─────────────────┐
│  Global Layer   │
│  (Singular)     │
│                 │
│ • Users/People  │
│ • Auth/JWT      │
│ • Global Roles  │
└────────┬────────┘
         │
    ┌────┴─────────────────────────────────────────┐
    │                                              │
┌───▼──────────┐  ┌───────────────┐  ┌──────────┐ │
│ Organization │  │ Organization  │  │... More  │ │
│      1       │  │      2        │  │ Orgs     │ │
│              │  │               │  │          │ │
│ ┌──────────┐ │  │ ┌──────────┐  │  │          │ │
│ │ Clients  │ │  │ │ Clients  │  │  │          │ │
│ │Projects  │ │  │ │Projects  │  │  │          │ │
│ │Assets    │ │  │ │Assets    │  │  │          │ │
│ │Reviews   │ │  │ │Reviews   │  │  │          │ │
│ │Templates │ │  │ │Templates │  │  │          │ │
│ │KPIs      │ │  │ │KPIs      │  │  │          │ │
│ │Snapshots │ │  │ │Snapshots │  │  │          │ │
│ └──────────┘ │  │ └──────────┘  │  │          │ │
└──────────────┘  └───────────────┘  └──────────┘ │
    │                                              │
    └──────────────────────────────────────────────┘

Every API route filters by: `organization_id = current_user.active_organization_id`
Database queries enforce tenant isolation through organization_id indices
```

### Data Flow: 4-Eyes Review Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Asset Lifecycle                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  DRAFT → SUBMITTED → IN_REVIEW → {APPROVED|CHANGES}     │   │
│  │                                                          │   │
│  │  Author                Reviewer      Review Decision      │   │
│  │  ─────────────────────────────────────────────────────   │   │
│  │  Create Asset          -             draft               │   │
│  │       ↓                                                  │   │
│  │  Submit Review         -             submitted          │   │
│  │       ↓                                                  │   │
│  │  -                     Read + Review  in_review          │   │
│  │  -                     Decision       ↙      ↘           │   │
│  │  -                                approve  changes      │   │
│  │                                  ↓          ↓            │   │
│  │                            approved    back_to_author    │   │
│  │                                           ↓             │   │
│  │  Author                Revise      resubmit             │   │
│  │  Revise +              ─────────→  (new review)         │   │
│  │  Resubmit                                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Governance Rule: Two people required for approval              │
│  • Submitter ≠ Approver (enforced in review service)            │
│  • Audit trail recorded in activity_log                         │
│  • Timeline captures all state changes                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components & Relationships

### 1. **Core Entities**

| Entity | Purpose | Related Tables | Org-Scoped |
|--------|---------|----------------|-----------|
| **Organization** | SaaS tenant boundary | OrganizationMembership, all scoped entities | - |
| **Person** | User account | OrganizationMembership, ProjectMembership | ✓ (via membership) |
| **Client** | Customer/implementation target | Projects, Assets | ✓ |
| **Project** | Implementation project | Assets, Memberships | ✓ |
| **Asset** | Celonis deliverable (KPI, data model, view, etc.) | Reviews, Snapshots, Sources | ✓ |
| **Review** | 4-eyes approval workflow | Decisions (approve/changes), Timeline | ✓ |
| **Template** | Reusable asset pattern | Instantiations, Libraries | ✓ |
| **Template Library** | Collection of templates | Templates | ✓ |
| **Todo** | Task/responsibility | TimelineEvent | ✓ |
| **Timeline** | Activity log | All entities | ✓ |

### 2. **Celonis Integration Entities**

| Entity | Purpose | Integration |
|--------|---------|-------------|
| **CelonisConnection** | Credential storage | Celonis API connector |
| **Celonis Snapshot** | Asset version capture | Snapshot export service |
| **Celonis Deployment** | Target deployment info | Deployment tracking |
| **Celonis Marketplace** | Package references | Marketplace lookup |
| **Asset Source** | Source tracking (code drop, repo, etc.) | GitLab/code integration |

### 3. **Knowledge & Use-Case Entities**

| Entity | Purpose | Usage |
|--------|---------|-------|
| **UseCase** | Business case reference | Library & roadmap |
| **Roadmap Item** | Use-case progress tracking | Planned → released |
| **Forum Insight** | Celonis forum discoveries | Triage & planning |
| **KPI Definition** | KPI specifications | KPI book |
| **KPI Version** | KPI versioning | Change tracking |

### 4. **Automation & Orchestration**

| Entity | Purpose | Execution |
|--------|---------|-----------|
| **Agent** | Autonomous worker | Tool hub (MCP servers) |
| **Quest** | Task for agent/human | Agent dispatch |
| **Quest Assignment** | Quest allocation | Person assignment |
| **Quest Feedback** | Task outcome recording | Run completion |

### 5. **Infrastructure & Integration**

| Entity | Purpose | Gateway |
|--------|---------|---------|
| **GitLab Integration** | Repo management | gitlab_gateway.py |
| **GitLab Pipeline Run** | CI/CD execution tracking | Pipeline status |
| **Ingest Run** | Data ingestion job | ingest_service.py |
| **Ingest Finding** | Data quality results | Finding severity |
| **Delivery File** | Asset documentation | file storage (uploaded/external) |

### 6. **Feature Flags & Rollout**

| Feature | Configuration | Scope |
|---------|---------------|-------|
| **Feature Rollout** | feature_rollout.py | Per-organization profile |
| **UI Rollout Profile** | config/ui_rollout_profiles.json | Org override support |
| **Tool Domain Activation** | tool_hub_profiles.json | Startup-time profile selection |

---

## Core Technology Stack

### Backend Framework & Database

```
Framework:     FastAPI 0.115.0+
ASGI Server:   Uvicorn 0.30.0+ (with auto-reload)
ORM:           SQLModel 0.0.22+ (SQLAlchemy 2.0.30+)
Database:      PostgreSQL 16 (prod), SQLite (desktop mode)
Migrations:    Alembic 1.13.2+ (auto-versioned)
Python:        3.11+ (required)
```

### Authentication & Security

```
JWT:           python-jose 3.3.0+ with cryptography
Password Hash: bcrypt 5.0.0+
Email Valid:   email-validator 2.2.0+
Form Parse:    python-multipart 0.0.9+
Sanitize:      bleach 6.2.0+ (XSS prevention)
```

### HTTP & Data

```
HTTP Client:   httpx 0.27.0+
Config:        pydantic-settings 2.4.0+
Markdown:      markdown 3.7+ (for content rendering)
YAML:          PyYAML 6.0.2+
Templates:     Jinja2 3.1.4+ (HTML rendering)
```

### Testing

```
Framework:     pytest 8.3.0+
Browser:       playwright 1.45.0+, pytest-playwright 0.5.0+
Markers:       e2e tests separately tagged
```

### Code Quality

```
Linting:       ruff 0.6.0+ (line-length=100)
Type Check:    mypy 1.11.0+ (py311, selective ignore)
Docs:          mkdocs 1.6.0+, mkdocs-material 9.5.0+
```

### Container & Deployment

```
Container:     Docker (Python 3.11-slim base)
Compose:       Docker Compose v3.9+
Image Build:   Multi-stage (copy src/ + docs_site/)
Env:           .env file for secrets
Port:          8000 (internal), 8000 (external)
```

### External Integrations

```
Celonis API:   Contracts in celonis_contracts.py
GitLab API:    Gateway in gitlab_gateway.py
MCP (LLM):     Model Context Protocol servers (experimental)
Email:         SMTP via email_service.py
Local Knowledge: Local wiki query API
```

---

## Database Schema Overview

### Core Tables (Organization-Scoped)

**Organization** (Global)
- `id` (UUID, PK)
- `name`, `slug` (unique)
- `created_at`

**Person** (Global)
- `id` (UUID, PK)
- `email` (unique), `name`
- `hashed_password`, `role_global`
- `created_at`

**OrganizationMembership**
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `person_id` (FK, idx)
- `role` (owner, admin, member)
- `joined_at`

**Client** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `name`, `tenant_url`
- `sensitivity_level` (low, medium, high)
- `salesforce_url` (optional)
- `created_at`

**Project** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `client_id` (FK, idx)
- `name`, `status` (planned, active, closed)
- `celonis_package_url`, `celonis_app_url`
- `salesforce_url`
- `created_at`

**ProjectMembership**
- `id` (UUID, PK)
- `project_id` (FK)
- `person_id` (FK)
- `role` (lead, reviewer, contributor)
- `start_date`, `end_date`

**Asset** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `project_id` (FK)
- `asset_type` (data_model, kpi, view, action_flow, extractor, ml_job, other)
- `asset_status` (draft, in_review, approved, deprecated)
- `name`, `description`, `tags`
- `created_at`, `updated_at`

**Review** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `asset_id` (FK)
- `review_status` (draft, submitted, in_review, approved, changes_requested, closed)
- `submitted_by`, `reviewed_by`
- `submission_date`, `review_date`
- `comments`

**ReviewDecision**
- `id` (UUID, PK)
- `review_id` (FK)
- `decision_type` (approve, request_changes)
- `rationale`
- `decided_at`

**Template** (Org-Scoped)
- `id` (UUID, PK)
- `library_id` (FK)
- `title`, `category`, `description`
- `storage_type` (sharepoint, onedrive, uploaded_pptx)
- `storage_url`
- `prefill_schema_json` (JSON)
- `requires_review`, `is_active`
- `created_by`, `created_at`

**TemplateLibrary** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `name`, `scope` (global_scope, client_scope)
- `library_type` (template, document)
- `client_id` (FK, optional)
- `base_url`
- `created_at`

**TemplateInstantiation** (Org-Scoped)
- `id` (UUID, PK)
- `template_id` (FK)
- `project_id` (FK)
- `client_id` (FK)
- `author_id`, `reviewer_id`
- `generated_url`, `prefill_data_json` (JSON)
- `asset_id` (FK, optional)
- `review_request_id` (FK, optional)
- `created_at`

**Todo** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `title`, `description`
- `assigned_to`, `created_by`
- `status` (open, in_progress, done)
- `priority` (low, medium, high)
- `due_date`
- `created_at`, `completed_at`

**TimelineEvent** (Org-Scoped)
- `id` (UUID, PK)
- `organization_id` (FK, idx)
- `entity_type` (organization, client, project, person, asset, review, etc.)
- `entity_id` (FK, the entity being changed)
- `action` (created, updated, deleted, approved, etc.)
- `actor_id` (person who made change)
- `details_json` (JSON payload)
- `created_at`

**DeliveryFile** (Org-Scoped)
- `id` (UUID, PK)
- `name`, `description`
- `file_source` (uploaded, sharepoint_doc, onedrive_doc, external_link)
- `external_url`
- `stored_filename`, `mime_type`, `file_size_bytes`
- `library_id`, `client_id`, `project_id` (optional FKs)
- `uploaded_by`, `created_at`

### Extended Entities (20+ additional tables)

**Celonis Integration**
- CelonisConnection, CelonisSnapshot, CelonisDeploymentRequest, CelonisTokenCache

**KPI & Metrics**
- KpiDefinition, KpiVersion, KpiBook, KpiBookEntry

**Use-Cases & Roadmap**
- UseCase, UseCaseRoadmapItem, UseCaseViewsCache

**Forum Insights**
- ForumInsight, ForumInsightFinding

**Snapshots & Artifacts**
- AssetSnapshot, SnapshotArtifact, SnapshotChange, SnapshotGitStore

**Asset Sources & GitLab**
- AssetSource, GitLabRepo, GitLabPipelineRun

**Ingestion & Quality**
- IngestRun, IngestFinding

**Agents & Quests**
- Agent, Quest, QuestAssignment, QuestFeedback, TaskDependency

**Tokens & Permissions**
- UserToken, ClientToken, ProjectToken

### Database Indexes

Key indexes are on:
- `organization_id` (all org-scoped tables)
- `(organization_id, status)` (for filtering)
- `person_id`, `project_id`, `client_id`
- `(entity_type, entity_id)` for timeline queries
- Unique on email (Person), slug (Organization)

---

## API Routes & Endpoints

### Authentication Routes (`/auth`)
- `POST /auth/register` - User registration
- `POST /auth/login` - JWT login
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - Logout
- `POST /auth/forgot-password` - Password recovery
- `POST /auth/reset-password` - Password reset

### User & Organization Routes (`/people`, `/orgs`)
- `GET /orgs/mine` - User's organizations
- `GET /orgs/{org_id}` - Organization details
- `POST /orgs` - Create organization
- `GET /people/{person_id}` - Person details
- `GET /people` - List people in org
- `PUT /people/{person_id}` - Update person
- `POST /people/{person_id}/memberships` - Add to organization

### Client Management (`/clients`)
- `GET /clients` - List org clients
- `POST /clients` - Create client
- `GET /clients/{client_id}` - Client details
- `PUT /clients/{client_id}` - Update client
- `GET /clients/{client_id}/health` - Client health metrics

### Project Management (`/projects`)
- `GET /projects` - List org projects
- `POST /projects` - Create project
- `GET /projects/{project_id}` - Project details
- `PUT /projects/{project_id}` - Update project
- `POST /projects/{project_id}/assign` - Assign team member
- `GET /projects/{project_id}/timeline` - Project timeline

### Asset Management (`/assets`)
- `GET /assets` - List org assets
- `POST /assets` - Create asset
- `GET /assets/{asset_id}` - Asset details
- `PUT /assets/{asset_id}` - Update asset
- `DELETE /assets/{asset_id}` - Delete asset (soft delete)

### Review Workflow (`/reviews`)
- `GET /reviews` - List reviews
- `POST /reviews` - Create review
- `GET /reviews/{review_id}` - Review details
- `PUT /reviews/{review_id}` - Update review
- `POST /reviews/{review_id}/submit` - Submit for review
- `POST /reviews/{review_id}/approve` - Approve (must be different person)
- `POST /reviews/{review_id}/request-changes` - Request changes

### Template Management (`/templates`)
- `GET /templates` - List templates
- `POST /templates` - Create template
- `GET /templates/{template_id}` - Template details
- `PUT /templates/{template_id}` - Update template
- `POST /templates/{template_id}/instantiate` - Create from template

### Timeline & Activity (`/timeline`)
- `GET /timeline` - Org activity feed (paginated)
- `GET /timeline/{entity_type}/{entity_id}` - Entity-specific timeline
- Filters by `organization_id`, sortable by `created_at`

### Todo Management (`/todos`)
- `GET /todos` - List todos
- `POST /todos` - Create todo
- `GET /todos/{todo_id}` - Todo details
- `PUT /todos/{todo_id}` - Update todo
- `DELETE /todos/{todo_id}` - Delete todo

### File Management (`/files`)
- `POST /files/upload` - Upload file
- `POST /files/link` - Link external file
- `GET /files/{file_id}` - File details
- `GET /files/{file_id}/viewer-url` - Viewer link
- `GET /files/{file_id}/download` - Download link

### KPI Management (`/kpis`, `/kpi-book`)
- `GET /kpis` - List KPIs
- `POST /kpis` - Create KPI
- `GET /kpi-book` - KPI book
- `POST /kpi-book` - Add to KPI book
- `GET /kpi-book/{entry_id}` - Book entry details

### Snapshot Management (`/snapshots`)
- `GET /snapshots` - List snapshots
- `POST /snapshots` - Create snapshot
- `GET /snapshots/{snapshot_id}` - Snapshot details
- `GET /snapshots/{snapshot_id}/artifacts` - Snapshot artifacts
- `GET /snapshots/{snapshot_id}/detail` - Detailed content

### Use-Case & Forum Routes (`/use-cases`, `/forum-insights`)
- `GET /use-cases` - Use-case library
- `GET /forum-insights` - Forum discoveries
- `POST /forum-insights` - Log insight
- `PUT /forum-insights/{id}` - Update status

### Celonis Integration (`/celonis`, `/celonis-marketplace`)
- `GET /celonis/status` - Connection status
- `POST /celonis/configure` - Setup connection
- `POST /celonis/preflight` - Pre-deployment checks
- `POST /celonis/extract` - Extract asset
- `POST /celonis/import` - Import asset
- `GET /celonis-marketplace` - Marketplace packages

### Celonis Deployments (`/celonis-deployments`)
- `GET /celonis-deployments` - List deployment requests
- `POST /celonis-deployments` - Create request
- `GET /celonis-deployments/{id}` - Details
- `PUT /celonis-deployments/{id}/status` - Update status

### GitLab Integration (`/gitlab`)
- `GET /gitlab/repos` - List repos
- `POST /gitlab/sync` - Sync repo
- `GET /gitlab/pipelines` - Pipeline status

### Quest & Agent Management (`/quests`)
- `GET /quests` - List quests
- `POST /quests` - Create quest
- `POST /quests/{id}/assign` - Assign quest
- `POST /quests/{id}/complete` - Mark complete

### Tool Hub (`/tool-hub`)
- `GET /tool-hub/status` - Tool hub status
- `POST /tool-hub/start` - Start tool hub
- `POST /tool-hub/stop` - Stop tool hub

### Local Knowledge (`/local-knowledge`)
- `GET /local-knowledge/status` - Gateway status
- `POST /local-knowledge/query` - Query knowledge base

### Data Ingestion (`/ingest`)
- `POST /ingest/start` - Start ingestion
- `GET /ingest/{run_id}` - Ingest run status
- `GET /ingest/{run_id}/findings` - Quality findings

### Health & Documentation
- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc UI
- `GET /openapi.json` - OpenAPI spec
- `GET /docs-site/*` - MkDocs documentation

---

## Integration Points

### 1. **Celonis Integration**

**Services:**
- `celonis_contracts.py` - Defines API contracts
- `celonis_data_agent_service.py` - MCP-based data queries
- `celonis_deployment_service.py` - Deployment management
- `celonis_payload_extractors.py` - Parse Celonis responses

**Routes:**
- `/celonis/` - Configuration & actions
- `/celonis-marketplace/` - Package lookup
- `/celonis-deployments/` - Deployment tracking

**Startup Configuration:**
- `FORGE_CELONIS_API_TOKEN` (env var)
- `FORGE_CELONIS_BASE_URL` (env var)

**Tool Hub Integration:**
- MCP server: `celonis-data-agent-mcp`
- Domain: `celonis-agent`
- Health probe: HTTP GET (stdio transport)

---

### 2. **GitLab Integration**

**Services:**
- `gitlab_gateway.py` - GitLab API client

**Routes:**
- `/gitlab/` - Repo management & sync

**Startup Configuration:**
- `FORGE_GITLAB_BASE_URL` (env var)
- `FORGE_GITLAB_API_TOKEN` (env var)

**Use Cases:**
- Asset source tracking (pullable/mirrored repos)
- Pipeline run monitoring
- Code drop ingestion

---

### 3. **Local Knowledge Gateway**

**Services:**
- `local_knowledge_gateway.py` - Knowledge base client

**Routes:**
- `/local-knowledge/` - Query & status

**Tool Hub Integration:**
- Domain: `knowledge-hub`
- Tools: `local-wiki-query-api`, `local-knowledge-gateway`, `open-webui`
- Health probe: Process-based

**Use Cases:**
- Local Obsidian wiki integration
- LLM context augmentation
- Offline knowledge base

---

### 4. **Email & Notifications**

**Services:**
- `email_service.py` - SMTP-based email

**Configuration:**
- `FORGE_SMTP_HOST`, `FORGE_SMTP_PORT`
- `FORGE_SMTP_USER`, `FORGE_SMTP_PASSWORD`

**Triggers:**
- Password reset links
- Review notifications
- Task assignments

---

### 5. **MCP (Model Context Protocol) Servers**

**Enabled (Phase 1):**
- `foundry-api` (core platform, stdio)
- `celonis-data-agent-mcp` (Celonis queries, stdio)

**Planned (Phase 2):**
- `agentic-user-test-runner-mcp` (standardized testing)
- `agentic-bug-ledger-mcp` (defect tracking)

**Planned (Phase 3):**
- `agentic-evidence-mcp` (trace/screenshot retrieval)
- `agentic-deployment-readiness-mcp` (release gating)

---

## Build & Deployment

### Local Development Build

**Prerequisites:**
```powershell
python 3.11+
pip >= latest
PostgreSQL 16 (or use Docker Compose)
```

**Installation:**
```powershell
# Install editable package with dependencies
python -m pip install --upgrade pip
python -m pip install -e .

# Run database migrations (auto on startup)
alembic upgrade head
```

**Startup Options:**

1. **Full Tool Hub** (default):
   ```powershell
   .\START.ps1
   ```

2. **API Only**:
   ```powershell
   .\START.ps1 -Mode api-only
   ```

3. **Fast Reload** (no file watcher):
   ```powershell
   .\START.ps1 -Mode api-fast
   ```

4. **Specific Profile** (staged rollout):
   ```powershell
   .\START.ps1 -Profile pilot-core
   .\START.ps1 -Profile pilot-core-plus-knowledge
   .\START.ps1 -Profile integration-celonis
   ```

5. **Discovery Only**:
   ```powershell
   .\START.ps1 -Mode dry-run
   ```

6. **Stop All**:
   ```powershell
   .\START.ps1 -Mode stop
   ```

### Docker Compose Build

**Services:**
- `db` - PostgreSQL 16
- `api` - FastAPI application

**Startup:**
```bash
docker-compose up --build
# Server: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Environment:**
```env
FORGE_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/foundry
FORGE_CELONIS_API_TOKEN=...
FORGE_GITLAB_API_TOKEN=...
FORGE_SMTP_HOST=...
```

---

### Desktop Build (PyInstaller)

**Build Script:**
```powershell
.\scripts\build_desktop.ps1
# Output: build/FoundryDesktop/
```

**Features:**
- Single-file executable
- Bundled SQLite database
- Auto-browser launch
- Local file logging (AppData\Local\CelonisDeliveryForge\desktop.log)

**Startup:**
```powershell
# From built app
.\FoundryDesktop.exe
# Opens browser automatically at http://127.0.0.1:8000
```

---

### Production Build (Standalone)

**Build Script:**
```powershell
.\scripts\build_standalone.ps1
```

**Deployment:**
- Docker image or standalone binary
- External PostgreSQL database
- Environment variables for secrets
- Health check: `http://{host}:8000/health`

---

## Testing Framework

### Test Organization

```
tests/
├── conftest.py                           # Global pytest config & fixtures
├── Unit & Integration Tests (~40 files)
│   └── test_*.py                         # Pytest modules
├── e2e/                                  # End-to-end browser tests
│   ├── __init__.py
│   └── Playwright-based journey tests
```

### Testing Stack

```
Framework:     pytest 8.3.0+
Browser:       playwright 1.45.0+
Plugin:        pytest-playwright 0.5.0+
HTTP Client:   httpx 0.27.0+
```

### Key Test Categories

| Category | Purpose | Files |
|----------|---------|-------|
| **UI Tests** | Browser-based workflows | `test_*_ui.py` (~15 files) |
| **API Tests** | HTTP endpoint validation | `test_*_api.py` (~15 files) |
| **Service Tests** | Business logic | `test_*_service.py` (~5 files) |
| **Integration Tests** | External systems | `test_celonis_*`, `test_gitlab_*` |
| **E2E Tests** | End-to-end journeys | `tests/e2e/` |
| **Database Tests** | Schema & migrations | `test_startup_db_policy.py` |
| **Config Tests** | Feature rollout & profiles | `test_tool_hub_profile_activation.py` |

### Example Tests

- `test_account_ui.py` - Account page rendering & form submission
- `test_login_ui.py` - JWT login flow with browser
- `test_celonis_preflight_api.py` - Pre-deployment validation
- `test_snapshots_api.py` - Snapshot CRUD operations
- `test_e2e_artifact_helpers.py` - Artifact collection utilities
- `test_tool_hub_profile_activation.py` - Profile switching

### Running Tests

**All tests:**
```powershell
pytest
```

**By marker:**
```powershell
pytest -m e2e              # End-to-end only
```

**By file pattern:**
```powershell
pytest tests/test_api.py
```

**With coverage:**
```powershell
pytest --cov=foundry
```

---

## Documentation System

### Source Organization

**MkDocs Material Theme:**
- Config: `mkdocs.yml`
- Source: `docs/` (or `site_docs/`)
- Build: `docs_site/` (auto-generated HTML)

**Structure:**
```
docs/
├── index.md                    # Landing page
├── Master roadmaps & architecture docs
├── admin/                      # Admin guides
├── developer/                  # Developer guides
├── guides/                     # Workflow guides
├── user/                       # User documentation
├── troubleshooting/            # Troubleshooting
└── stylesheets/extra.css       # Custom styling
```

### Key Documentation Files

| File | Audience | Purpose |
|------|----------|---------|
| `README.md` | Everyone | Project intro & quick start |
| `QUICKSTART.md` | New users | 1-minute startup |
| `STARTUP.md` | Developers | Detailed setup |
| `master-roadmap.md` | Product | Phased roadmap |
| `agent-orchestration-operating-model.md` | Engineers | Agent architecture |
| `docs/developer/docs-architecture.md` | Engineers | Docs system |
| `docs/developer/integrations.md` | Engineers | External integrations |

### Build & Deployment

**Build HTML:**
```powershell
mkdocs build
# Output: docs_site/
```

**Serve Locally:**
```powershell
mkdocs serve
# Accessible at http://localhost:8000/
```

**In-App Access:**
- Route: `/docs-site/`
- Legacy redirect: `/docu/*.html` → `/docs-site/*`

---

## External Dependencies & Submodules

### External Resources Structure

```
external resources/
├── Code from Celonis/
│   ├── swagger.json                         # API spec
│   ├── image-processing/                    # Image extraction
│   │   └── document_extraction_pipeline/
│   ├── dm-load-optimization/                # Data model optimization
│   │   └── app/src/
│   └── m-20-ocpm-bootstrapper/              # OCPM bootstrapper
│       └── tests/, app/
│
├── Code by Florian/
│   └── celonis-data-agent/                  # MCP server
│       └── celonis_data_agent/
│           ├── __init__.py
│           ├── server.py                    # MCP entry point
│           └── ... (tool implementations)
│
├── Projects at Work/
│   └── pyCelonis-tools/                     # PyCelonis utilities
│       ├── scripts/
│       │   ├── extractors/
│       │   ├── exports/
│       │   ├── consulting/
│       │   ├── migration/
│       │   └── ... (tools)
│       └── workspace/
│
└── local-knowledge-model/
    └── obsidian-llm-wiki-local/             # Obsidian integration
        └── src/obsidian_llm_wiki/
            ├── __init__.py
            └── pipeline/
```

### Git Submodules

The project uses git submodules for:
- `external resources/Code by Florian/celonis-data-agent` (MCP server)
- Managed via `scripts/add_upstream_submodule.ps1` and `sync_florian_submodules.ps1`

---

## Configuration & Runtime Modes

### Startup Modes

| Mode | Purpose | Tools Started |
|------|---------|---------------|
| **hub** (default) | Full tool hub with API | All enabled tools by profile |
| **api-only** | FastAPI only (with reload) | foundry-api only |
| **api-fast** | FastAPI only (no reload watcher) | foundry-api only |
| **status** | Report tool status | None (query only) |
| **stop** | Gracefully stop all | Cleanup & shutdown |
| **dry-run** | Discovery without starting | Report what would run |

### Tool Hub Profiles

| Profile | Domains | Phases | Use Case |
|---------|---------|--------|----------|
| **full** | All | All | Full feature set |
| **pilot-core** | core-platform | Phase 1 | Small user test |
| **pilot-core-plus-knowledge** | core-platform, knowledge-hub | Phase 1 | Pilot + knowledge |
| **integration-celonis** | core-platform, celonis-agent | Phase 1 | Celonis-focused test |

### UI Rollout Profiles

**File:** `config/ui_rollout_profiles.json`

```json
{
  "org_profile_overrides": {
    "pilot-org-slug": "pilot-core",
    "enterprise-org": "full"
  },
  "feature_flags": {
    "agent_quests": true,
    "forum_insights": true,
    "snapshots": false  // Hide in pilot orgs
  }
}
```

### Environment Variables

**Database:**
```env
FORGE_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/foundry
# Default (desktop): sqlite:///AppData/Local/CelonisDeliveryForge/foundry.db
```

**Celonis:**
```env
FORGE_CELONIS_API_TOKEN=xxx
FORGE_CELONIS_BASE_URL=https://tenant.celonis.cloud
```

**GitLab:**
```env
FORGE_GITLAB_BASE_URL=https://gitlab.com
FORGE_GITLAB_API_TOKEN=xxx
```

**Email (SMTP):**
```env
FORGE_SMTP_HOST=smtp.example.com
FORGE_SMTP_PORT=587
FORGE_SMTP_USER=user@example.com
FORGE_SMTP_PASSWORD=xxx
FORGE_SMTP_FROM=noreply@example.com
```

**JWT & Security:**
```env
FORGE_JWT_SECRET=xxx (auto-generated if not set)
FORGE_JWT_ALGORITHM=HS256
FORGE_JWT_EXPIRY_HOURS=24
```

**Feature Flags:**
```env
FORGE_ENABLE_AGENT_FEATURES=true
FORGE_ENABLE_FORUM_INSIGHTS=true
FORGE_ENABLE_SNAPSHOTS=true
```

---

## Key Entry Points

### API Entry Point

**File:** `src/foundry/api/main.py`

```python
from fastapi import FastAPI
from foundry.api import routes

app = FastAPI(
    title="Celonis Delivery Forge",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Include 27 route modules
# Mount static files & documentation
# Lifespan events for startup/shutdown
```

**Startup Tasks:**
1. Initialize database (Alembic auto-migration)
2. Load settings from environment & `.env`
3. Mount UI static files & templates
4. Mount documentation site (`/docs-site`)
5. Register exception handlers
6. Health check endpoint ready

### Desktop Entry Point

**File:** `src/foundry/desktop/app.py`

```python
def run_desktop() -> None:
    # 1. Check if port is occupied
    # 2. Spawn uvicorn server (background thread)
    # 3. Wait for health check
    # 4. Open browser to dashboard
    # 5. Keep process alive
```

**Launcher:**
- `FoundryDesktop.spec` - PyInstaller spec for .exe build
- Desktop shortcuts to launch bundled app

### Startup Scripts

**PowerShell:** `START.ps1`
- Auto-dependency installation
- Mode selection (hub vs. API-only)
- Tool hub orchestration
- Graceful shutdown handling

**Batch:** `START.bat`
- Windows CMD wrapper for `START.ps1`

**Development:** `scripts/dev.ps1`
- Fast start/stop for iteration
- Test runners
- Repo cleanup utilities

---

## Summary

### Project Statistics

| Metric | Count |
|--------|-------|
| **Total Python Files** | ~464 |
| **API Routes** | 27 modules, 100+ endpoints |
| **Database Tables** | 50+ entities |
| **HTML Templates** | 40+ Jinja2 templates |
| **Test Files** | 40+ test modules |
| **Database Migrations** | 20+ Alembic versions |
| **Action Flow Templates** | 15+ specifications |
| **Documentation Pages** | 50+ Markdown files |
| **External Integration Points** | 5+ (Celonis, GitLab, MCP, Email, Knowledge) |

### Architecture Highlights

✅ **Multi-tenant SaaS-ready** - Organization-scoped data with tenant isolation  
✅ **Dual-control governance** - 4-eyes review workflow enforced  
✅ **Composable tools** - Tool hub orchestration with domain-scoped activation  
✅ **Extensible integrations** - MCP-based agent support, GitLab/Celonis connectors  
✅ **Developer-first documentation** - MkDocs with Material theme, comprehensive guides  
✅ **Local-first deployment** - Desktop app with bundled SQLite, Docker support  
✅ **Enterprise-grade security** - JWT auth, bcrypt passwords, XSS prevention  

### Current Focus Areas

🚧 **SaaS Multi-Tenancy** - Organization scoping for all API routes  
🚧 **Agent Orchestration** - MCP servers with governance gates  
🚧 **Use-Case Library** - Consolidated knowledge base  
📋 **Personal Workspace** - Per-user configuration & preferences  
📋 **Billing & Subscriptions** - Usage metering & plans  

---

**Report Generated:** May 10, 2026  
**Analyzer:** Comprehensive Repository Analysis Tool  
**Next Steps:** Use this report to understand module relationships, plan feature development, or document architecture decisions.
