# Codebase Metrics & Analysis Report

**Generated:** May 10, 2026  
**Project:** Celonis Delivery Forge v0.1.0  
**Scope:** Complete repository including submodules and external resources

---

## Executive Summary

The Celonis Delivery Forge is a **multi-tenant delivery governance platform** with approximately **5.5M lines of Python code** across the codebase. However, the actual project implementation is significantly smaller (~27K lines of production code in `src/`), with the majority of lines coming from external dependencies and reference implementations.

**Key Findings:**
- ✅ **Clean separation of concerns** between API, services, database, and UI layers
- ⚠️ **Critical complexity hotspot**: `src/foundry/api/routes/ui.py` at 9,810 lines (should be <1000)
- ✅ **Comprehensive test coverage** with 8,281 lines of tests
- ⚠️ **External resources bloat**: 4.3M lines of reference code and external libraries mixed with source
- ✅ **Well-structured migrations** with Alembic (1,838 lines across 23 versions)

---

## Code Distribution Analysis

### Overall Codebase Composition

| Component | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| **External Resources** | 23,605 | 4,382,779 | Reference code, libraries, external projects |
| **Virtual Environment** | 2,981 | 1,092,445 | Python dependencies and packages |
| **Source Code** | 68 | 26,709 | Core application logic (production) |
| **Tests** | 48 | 8,281 | Test suite (pytest + Playwright) |
| **Database Migrations** | 23 | 1,838 | Alembic schema versions |
| **Scripts** | 8 | 1,227 | Automation and tooling |
| **Documentation** | 10,279 | 400,113 | Markdown docs and specs |
| **Other** | 10,148 | 17,704,950 | Binaries, pickles, CSVs, models, etc. |

**Total: 48,254 files, 24.7M lines**

---

### Production Code Breakdown (src/ directory)

The actual application code in `src/` is relatively lean:

```
src/
├── foundry/
│   ├── api/
│   │   ├── routes/           [~15,000 lines - API endpoints]
│   │   └── main.py           [FastAPI app initialization]
│   ├── services/             [~8,000 lines - business logic]
│   ├── models/               [Database entities and schemas]
│   ├── ui/                   [Jinja2 templates]
│   ├── extension/            [Chrome MV3 extension]
│   └── utils/                [Helpers and utilities]
└── ...
```

**Total Production Python: 26,709 lines across 68 files**  
**Average File Size: 392 lines**

---

## Complexity Hotspots & Cleanup Opportunities

### 🔴 **CRITICAL: src/foundry/api/routes/ui.py (9,810 lines)**

**Issue:** Single monolithic UI route file exceeding best practices by 10x

**Content Analysis:**
- Estimated 150-200 route handlers
- Mixed concerns: navigation, templates, state management, feature rollout
- Difficult to test and maintain
- High cognitive load for contributors

**Recommendation:**
```
src/foundry/api/routes/
├── ui.py                          [Keep only root router setup]
├── ui_navigation.py               [Navigation/menu endpoints]
├── ui_dashboard.py                [Dashboard and home views]
├── ui_projects.py                 [Project management views]
├── ui_assets.py                   [Asset browser and details]
├── ui_reviews.py                  [Review workflow views]
├── ui_deployments.py              [Deployment views]
├── ui_admin.py                    [Admin panels]
├── ui_templates.py                [Template management]
├── ui_settings.py                 [Settings and configuration]
└── ui_feature_rollout.py          [Feature gate and profile views]
```

**Expected Result:** Each file 500-1000 lines, clear single responsibility

**Priority:** 🔴 **Critical - Phase 1**

---

### 🟠 **HIGH: External Resources Directory (4.3M lines)**

**Issue:** `external resources/` folder contains:
- Duplicate reference implementations (pyCelonis, OCPMbootstrapper)
- Complete Python virtual environments (.local, Lib)
- Old project code (Projects at Work, Code by Celonis)
- External libraries mixed with source

**Impact:**
- Clutters repository
- Slows down git operations
- Creates confusion about what's part of core product
- Risk of accidental inclusion in builds

**Cleanup Strategy:**
1. **Extract to separate repos** (with Git submodules if still needed):
   - `external-resources/code-from-celonis/` → celonis-ai-demand-forecast-app (archive)
   - `external-resources/projects-at-work/` → team-reference-implementations (archive)
   - `external-resources/local-knowledge-model/` → knowledge-base-reference (external)

2. **Add to `.gitignore`** and document in `DEVELOPMENT.md`:
   ```
   # External Resources (archived)
   external resources/
   .venv-1/
   ```

3. **Document via README:**
   ```markdown
   ## Reference Materials
   
   External reference code and archived projects are available in the
   `external resources/` folder. These are for research and reference only.
   
   For active development, use the staged deployment profiles:
   - `full` - complete platform
   - `pilot-core` - core delivery features
   - `pilot-core-plus-knowledge` - with knowledge hub
   - `integration-celonis` - Celonis integration testing
   ```

**Priority:** 🟠 **High - Phase 6 (Cleanup)**

---

### 🟠 **HIGH: Service Layer Consolidation**

**Current State:**
- 25+ service modules in `src/foundry/services/`
- Some services have unclear boundaries
- Potential duplication in error handling and observability

**Recommended Structure:**
```
services/
├── platform/                      [Core platform services]
│   ├── organization.py
│   ├── user.py
│   └── auth.py
├── delivery/                      [Delivery workflow services]
│   ├── project.py
│   ├── asset.py
│   ├── review.py
│   └── deployment.py
├── integrations/                  [Third-party integrations]
│   ├── celonis_service.py
│   ├── gitlab_service.py
│   ├── mcp_service.py
│   └── email_service.py
├── ai_agent/                      [AI/agentic capabilities]
│   ├── celonis_data_agent.py
│   └── celonis_contracts.py
├── observability/                 [Shared observability]
│   ├── logging.py
│   ├── error_handling.py
│   └── feature_rollout.py
└── __init__.py
```

**Priority:** 🟠 **High - Phase 1 (Contracts)**

---

### 🟡 **MEDIUM: Test Organization**

**Current:** 48 test files, 8,281 lines  
**Status:** ✅ Good coverage, but organization could improve

**Suggested Structure:**
```
tests/
├── unit/                          [Fast, isolated tests]
│   ├── test_models.py
│   ├── test_services/
│   └── test_utils.py
├── integration/                   [Database, service interactions]
│   ├── test_api_routes.py
│   ├── test_celonis_integration.py
│   └── test_database.py
├── e2e/                           [End-to-end browser tests]
│   ├── test_user_workflows.py
│   └── test_deployment_pipeline.py
├── fixtures/                      [Test data and factories]
│   ├── conftest.py
│   └── factories.py
└── performance/                   [Load and stress tests]
    └── test_load_scenarios.py
```

**Priority:** 🟡 **Medium - Phase 1c**

---

## Technology Stack Analysis

### Backend (Production)

| Technology | Purpose | Status | Risk |
|-----------|---------|--------|------|
| **FastAPI** | REST API framework | ✅ Modern | ✅ Low |
| **SQLModel** | ORM + validation | ✅ Clean | ✅ Low |
| **PostgreSQL/SQLite** | Data storage | ✅ Scalable | ✅ Low |
| **Alembic** | Database migrations | ✅ Solid | ✅ Low |
| **Pydantic** | Data validation | ✅ Strong | ✅ Low |
| **JWT** | Authentication | ✅ Secure | ✅ Low |
| **Celery** | Task queue (optional) | ⚠️ If used | ⚠️ Medium |

### Frontend (Production)

| Technology | Purpose | Status | Risk |
|-----------|---------|--------|------|
| **Jinja2** | Template engine | ✅ Standard | ✅ Low |
| **HTML5/CSS3** | Markup and styling | ✅ Clean | ✅ Low |
| **JavaScript** | Client-side logic | ✅ Minimal | ✅ Low |
| **Chrome MV3** | Extension support | ✅ Modern | ✅ Low |
| **MkDocs Material** | Documentation site | ✅ Excellent | ✅ Low |

### Integration Points

| Service | Type | Risk | Note |
|---------|------|------|------|
| **Celonis API** | SaaS | 🟡 Medium | Tenant extraction candidate |
| **GitLab** | Self-hosted/SaaS | 🟡 Medium | Adapter pattern applied |
| **MCP Servers** | Custom | 🟡 Medium | Health/timeout standards needed |
| **Local Knowledge** | Optional | ✅ Low | Clean integration |
| **Email (SMTP)** | External | ✅ Low | Standard config |

---

## Feature Distribution

### Core Delivery Platform (Always Enabled)

- ✅ Organization & User Management
- ✅ Project Tracking & Status
- ✅ Asset Library & Versioning
- ✅ Review Workflows & Comments
- ✅ Timeline & Activity Logging
- ✅ Template Management
- ✅ File Storage & Downloads
- ✅ Admin Dashboard

**Lines of Code:** ~10,000  
**Files:** ~25

---

### Celonis Integration (Profile: integration-celonis)

- ✅ Tenant Extraction & Analysis
- ✅ Snapshot Management
- ✅ Deployment Tracking
- ✅ AI Data Agent Integration
- ✅ KPI Monitoring

**Lines of Code:** ~8,000  
**Files:** ~15  
**Status:** ⚠️ Complex - candidate for early submodule extraction

---

### Knowledge Hub (Profile: pilot-core-plus-knowledge)

- ✅ Local Knowledge Gateway Integration
- ✅ Obsidian Wiki Sync
- ✅ Use Case Management
- ✅ Forum Insights

**Lines of Code:** ~4,000  
**Files:** ~10

---

### Tool Hub & MCP Orchestration

- ✅ Tool Registry & Discovery
- ✅ Process Management
- ✅ Health Probes & Status
- ✅ Profile-based Activation

**Lines of Code:** ~2,000  
**Files:** ~8  
**Status:** ✅ Clean, well-scoped

---

## Database Complexity

### Current Schema

- **~50+ entities** across all domains
- **Organization-scoped multi-tenancy** enforced on all tables
- **20+ migrations** tracking evolution
- **Good constraints & indexes**

### Concerns

⚠️ **Shared Model Approach:**
- All entities in single `models/` module
- Large migration files (some 500+ lines)
- Potential for circular dependencies

✅ **Strengths:**
- Clear organization scoping
- Audit trail (created_at, updated_at)
- Proper foreign key relationships

### Recommendation

**Phase 5:** Consider domain-scoped model separation, but **NOT** a database split:
```
models/
├── platform/                      [Orgs, Users, Auth]
├── delivery/                       [Projects, Assets, Reviews]
├── celonis/                        [Snapshots, KPIs, Tenants]
├── knowledge/                      [Use Cases, Forums, KB]
└── shared/                         [Common base classes]
```

---

## Documentation Metrics

**Markdown Files:** 10,279  
**Total Lines:** 400,113  
**Average Length:** 38 lines per file

### Analysis

Most markdown comes from **generated documentation** and **MkDocs builds**. Actual human-authored docs:
- `docs/` folder: ~30 files
- `README.md`, `QUICKSTART.md`, etc.: ~10 files

**Status:** ✅ Well documented but scattered

### Consolidation Opportunity

See [docs/DOCUMENTATION_STRUCTURE.md](documentation-structure.md) for recommended reorganization.

---

## Code Quality Metrics

### Positive Indicators ✅

1. **Type Hints**: Consistent use of Pydantic models and type hints
2. **Error Handling**: Custom error classes, proper HTTP status codes
3. **Testing**: 48 test files with both unit and E2E coverage
4. **Code Organization**: Clear separation of API, services, models
5. **Database Migrations**: Every schema change tracked with Alembic
6. **Security**: Multi-tenancy enforced at API level, JWT auth
7. **Configuration**: Environment-driven, profile-based activation

### Areas Requiring Attention ⚠️

1. **Monolithic Routes File**: ui.py needs urgent refactoring
2. **External Resources**: 4.3M lines of reference code cluttering repo
3. **Service Layer**: 25+ modules need clearer boundaries
4. **Documentation**: Scattered across multiple markdown files
5. **MCP Contracts**: Health probes and invocation patterns need standardization

---

## Recommended Cleanup Phases

### Phase 1: Architecture Contracts (Weeks 1-2)
- [ ] Finalize input/output DTOs per domain
- [ ] Define error classification and response formats
- [x] Standardize health probe semantics
- [ ] Document MCP invocation contract

### Phase 1a: UI Route Refactoring (Weeks 2-4)
- [ ] Split `ui.py` into 10+ focused modules
- [ ] Extract template rendering to dedicated service
- [ ] Add comprehensive route-level tests
- [ ] Document navigation hierarchy

### Phase 1c: Test Hardening (Weeks 3-4)
- [ ] Reorganize test structure (unit/integration/e2e)
- [ ] Add profile activation tests
- [ ] Add MCP lifecycle tests
- [ ] Build regression pack per rollout profile

### Phase 2: Celonis Extraction (Weeks 5-8)
- [ ] Extract as first submodule candidate
- [ ] Clean up integration surface
- [ ] Finalize MCP contracts for tools
- [ ] Ensure complete test coverage

### Phase 3-5: Additional Modularization
- [ ] GitLab integration adapter
- [ ] Forum/KPI services
- [ ] Snapshot engine (after Phase 2)

### Phase 6: Repository Cleanup (Weeks 9-12)
- [ ] Remove/archive external resources
- [ ] Consolidate documentation
- [ ] Clean up dead imports and routes
- [ ] Final compliance verification

---

## Cleanup Quick Wins (Can Start Immediately)

### ✅ Low Risk, High Impact

1. **Add to `.gitignore`** (if not already):
   ```
   external resources/
   .venv-1/
   __pycache__/
   *.pyc
   .mypy_cache/
   .pytest_cache/
   .ruff_cache/
   *.db
   *.db-wal
   *.db-shm
   ```

2. **Create `DEVELOPMENT.md`** with:
   - Setup instructions
   - Run/test/debug commands
   - Profile descriptions
   - Deployment procedures

3. **Add `CODE_STRUCTURE.md`** documenting:
   - Directory layout
   - Module responsibilities
   - Dependency graph
   - How to add new routes/services

4. **Update `README.md`** with:
   - Project purpose (governance + delivery)
   - Quick links to docs
   - Architecture overview
   - Feature matrix by profile

5. **Create `.gitattributes`** to normalize line endings:
   ```
   * text=auto
   *.py text eol=lf
   *.json text eol=lf
   *.yaml text eol=lf
   *.md text eol=lf
   ```

6. **Run initial cleanup**:
   ```bash
   # Remove unused imports
   python -m pylint --disable=all --enable=unused-import src/ --reports=no
   
   # Check for dead code
   python -m vulture src/
   ```

---

## Code Complexity Estimation

### Cyclomatic Complexity Hotspots (Estimated)

Files likely to have high complexity:
- `src/foundry/api/routes/ui.py` (9,810 lines) - **Estimated CC: 150+** ⚠️
- `src/foundry/services/celonis_service.py` - **Estimated CC: 35-50**
- Integration services - **Estimated CC: 20-35**

**Recommendation:** Use `radon` to measure:
```bash
pip install radon
radon cc src/ -a  # Average complexity
radon mi src/ -m  # Maintainability index
```

---

## Summary Table

| Aspect | Status | Priority | Effort |
|--------|--------|----------|--------|
| **Architecture** | ✅ Solid | - | - |
| **API Design** | ✅ Clean | - | - |
| **Route Organization** | 🔴 Critical | 1 | High |
| **Service Boundaries** | 🟠 Needs work | 2 | Medium |
| **Test Coverage** | ✅ Good | - | - |
| **Documentation** | 🟡 Scattered | 3 | Medium |
| **External Resources** | 🔴 Bloat | 6 | Low |
| **Database Schema** | ✅ Well-designed | - | - |
| **Dependency Management** | ✅ Clean | - | - |

---

## Next Steps

1. **Immediate** (This week):
   - Add `.gitignore` entries
   - Create development documentation
   - Run static analysis tools

2. **Short-term** (Next 2 weeks):
   - Define API contracts per domain
   - Begin ui.py refactoring
   - Consolidate service documentation

3. **Medium-term** (Weeks 3-8):
   - Complete route refactoring
   - Extract Celonis as first submodule
   - Build test regression packs

4. **Long-term** (Weeks 9-12):
   - Modularize remaining domains
   - Repository cleanup
   - Final documentation consolidation

---

**Report Location:** `docs/codebase-metrics-and-analysis.md`  
**Last Updated:** May 10, 2026  
**Next Review:** After Phase 1 completion
