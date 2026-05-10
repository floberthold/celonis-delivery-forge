# Code Quality & Cleanup Roadmap

**Status:** Actionable recommendations  
**Total Effort:** 120-160 hours (4-5 weeks)  
**Timeline:** Phases 1-6 over 12 weeks  
**Risk Level:** Medium-High (affects all team members)

---

## Overview

Based on comprehensive analysis of the 5.5M-line codebase, this document provides a prioritized roadmap for improving code quality and reducing complexity. The actual project code (27K lines) is well-structured, but three areas require immediate attention.

---

## Priority Matrix

```
                   IMPACT
                    High
                     │
                     │  Critical Route Refactoring
                     │  Service Layer Reorg
           ┌─────────┼─────────┐
           │         │         │
       Low │ External Resources External Cleanup
           │         │
           │─────────┼─────────┤ Effort
                     │
                     Docs Consolidation
```

---

## Phase-by-Phase Roadmap

### ✅ Phase 0: Foundation (Weeks 1)

**Objective:** Establish governance and planning  
**Effort:** 8-10 hours

#### Tasks

- [ ] Create code quality committee (1-2 people)
- [ ] Review this roadmap with team
- [ ] Define code review standards
- [ ] Setup static analysis tools
- [ ] Create branch protection rules

#### Deliverables

- [ ] CODE_QUALITY.md (standards doc)
- [ ] DEVELOPMENT.md (contributor guide)
- [ ] Static analysis baseline report
- [ ] Team review notes

#### Tools to Setup

```bash
# Code quality tools
pip install pylint flake8 black isort mypy radon vulture

# Pre-commit hooks
pip install pre-commit
# Create .pre-commit-config.yaml
```

**Estimated Checklist:** 10 items

---

### 🔴 Phase 1: Architecture Contracts (Weeks 2-3)

**Objective:** Define clear integration boundaries  
**Effort:** 30-40 hours  
**Critical Path Item:** Blocks all future phases

#### Priority 1: API Contract Standardization

Define standard request/response formats:

```python
# src/foundry/schemas/contracts.py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class ErrorResponse(BaseModel):
    """Standard error response."""
    code: str                          # e.g., "VALIDATION_ERROR"
    message: str                       # Human-readable message
    details: Optional[Dict[str, Any]]  # Additional context
    request_id: str                    # Tracing ID

class HealthResponse(BaseModel):
    """Standard health probe response."""
    status: str                        # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: str
    components: Dict[str, str]         # Component-specific status
```

#### Priority 2: Error Classification

```python
# src/foundry/services/shared/error_codes.py
"""Standard error codes across platform."""

# Validation
VALIDATION_FAILED = "E001"
MISSING_REQUIRED_FIELD = "E002"
INVALID_FORMAT = "E003"

# Authorization
UNAUTHORIZED = "E401"
FORBIDDEN = "E403"

# Not Found
RESOURCE_NOT_FOUND = "E404"
ORGANIZATION_NOT_FOUND = "E404.1"
PROJECT_NOT_FOUND = "E404.2"

# Conflicts
DUPLICATE_NAME = "E409.1"
RESOURCE_ALREADY_EXISTS = "E409.2"

# Integration
EXTERNAL_SERVICE_ERROR = "E502"
CELONIS_API_ERROR = "E502.1"
GITLAB_API_ERROR = "E502.2"

# Internal
INTERNAL_SERVER_ERROR = "E500"
DATABASE_ERROR = "E500.1"
CONFIGURATION_ERROR = "E500.2"
```

#### Priority 3: Multi-Tenancy Contract

```python
# src/foundry/schemas/tenancy.py
class TenancyContext(BaseModel):
    """Standard tenancy context."""
    organization_id: str               # Required on all requests
    user_id: str                       # Current user
    request_id: str                    # Distributed tracing ID
    features: List[str]                # Enabled features for org
```

#### Priority 4: MCP Tool Contract

```python
# src/foundry/services/celonis/contracts.py
class MCPToolInvocation(BaseModel):
    """Standard MCP tool invocation."""
    tool_id: str
    version: str                       # Tool version
    timeout_ms: int                    # Execution timeout
    parameters: Dict[str, Any]
    
class MCPToolResponse(BaseModel):
    """Standard tool response."""
    success: bool
    duration_ms: int
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    fallback: Optional[Dict[str, Any]]  # Fallback value if timeout
```

#### Deliverables

- [x] Error codes standardization
- [x] API contract documentation
- [x] Health probe specification
- [x] MCP invocation contract (shared DTOs added)
- [x] Multi-tenancy enforcement spec (tenancy context contract type added)
- [x] Observability/logging standards (shared structured error detail contract in Celonis route)

Implemented artifacts (2026-05-10):

- `src/foundry/contracts.py`
- `src/foundry/error_codes.py`
- `src/foundry/api/main.py`
- `src/foundry/api/routes/local_knowledge.py`
- `tests/test_shared_api_contracts.py`
- `tests/test_startup_db_policy.py`
- `tests/test_local_knowledge_health_contracts.py`
- `src/foundry/api/routes/celonis.py`
- `site_docs/developer/api-contracts.md`

**Status:** 🚧 In progress

---

### 🔴 Phase 1a: UI Route Refactoring (Weeks 2-4)

**Objective:** Split monolithic ui.py (9,810 lines)  
**Effort:** 40-60 hours  
**Priority:** CRITICAL  
**See:** [refactoring-ui-routes.md](refactoring-ui-routes.md)

#### Milestones

- Week 2: Structure & planning
- Week 3: Extract first batch of routes
- Week 4: Complete extraction & testing

#### Key Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Largest file | 9,810 lines | <1,500 lines |
| Avg file size | 9,810 | 900 lines |
| Test coverage | ~70% | >85% |
| Build time | 3-5s | 2-3s |

Implemented tranche (2026-05-10):

- Extracted `/local-knowledge-ui/status` from `src/foundry/api/routes/ui.py` to `src/foundry/api/routes/ui_knowledge_status.py`.
- Router wiring added in `src/foundry/api/main.py`.
- Coverage updated in `tests/test_local_knowledge_ui.py`.
- Introduced package skeleton via `src/foundry/api/routes/ui/__init__.py`.
- Extracted shared redirect/query helpers to `src/foundry/api/routes/ui/shared.py`.
- Extracted initial navigation routes to `src/foundry/api/routes/ui/navigation.py` with tests in `tests/test_ui_navigation_routes.py`.
- Extracted first integrations route slices to `src/foundry/api/routes/ui/integrations.py` (`/methodology-ui`, `/celonis-tool-hub-ui`) with coverage in `tests/test_ui_integrations_routes.py` and `tests/test_celonis_tool_hub_ui.py`.
- Extracted first templates route slice to `src/foundry/api/routes/ui/template_management.py` (`/templates-ui`) with coverage in `tests/test_ui_templates_routes.py`.
- Extracted docu/admin redirect slice to `src/foundry/api/routes/ui/docu_redirects.py` (`/docu/*.html`) with coverage in `tests/test_ui_docu_redirect_routes.py`.

**Status:** 🚧 In progress

---

### 🔴 Phase 1b: Service Layer Restructuring (Weeks 2-4)

**Objective:** Organize 25 services into 6 domains  
**Effort:** 30-40 hours  
**See:** [service-layer-restructuring.md](service-layer-restructuring.md)

#### New Structure

```
services/
├── platform/      (auth, users, orgs)
├── delivery/      (projects, assets, reviews)
├── celonis/       (tenant extraction, snapshots)
├── knowledge/     (KB, forums, use cases)
├── integrations/  (GitLab, email)
├── orchestration/ (tool hub, MCP)
└── shared/        (errors, logging, cache)
```

#### Tasks

- [x] Map current services to domains (published in `config/service_domain_mapping.json`)
- [x] Create new directory structure
- [ ] Extract services by domain
- [ ] Update all imports
- [ ] Test and verify

Low-risk migration kickoff (2026-05-10):

- Moved `feature_rollout.py` to `services/platform/feature_rollout.py` with legacy shim preserved
- Moved `email_service.py` to `services/integrations/email_service.py` with legacy shim preserved
- Moved `template_seed.py` to `services/delivery/template_seed.py` with legacy shim preserved
- Moved `use_case_views.py` to `services/knowledge/use_case_views.py` with legacy shim preserved
- Moved `trycelonis_demo_rebuild.py` to `services/integrations/trycelonis_demo_rebuild.py` with legacy shim preserved
- Moved `ingest_service.py` to `services/integrations/ingest_service.py` with legacy shim preserved
- Moved `florian_script_seed.py` to `services/delivery/florian_script_seed.py` with legacy shim preserved

**Status:** 📋 Not started

---

### 🔴 Phase 1c: Test Hardening (Weeks 3-4)

**Objective:** Comprehensive test coverage for profiles & MCP  
**Effort:** 20-30 hours

#### Test Coverage Goals

| Category | Current | Target |
|----------|---------|--------|
| Unit Tests | ~60% | >80% |
| Integration | ~50% | >75% |
| E2E Tests | ~40% | >70% |
| MCP Tests | ~30% | >85% |
| Profile Tests | ~20% | >90% |

#### New Test Suites

```python
tests/
├── test_profile_activation.py         # Profile gate tests
├── test_mcp_lifecycle.py              # Health/startup/shutdown
├── test_mcp_invocation.py             # Tool invocation contract
├── test_celonis_integration.py        # Celonis mock tests
├── test_ui_gate_coverage.py           # UI feature gate tests
└── test_regression_by_profile.py      # Smoke tests per profile
```

#### Implemented Subset (2026-05-10)

- [x] Profile activation coverage (`tests/test_tool_hub_profile_activation.py`)
- [x] Startup/catalog profile contract coverage (`tests/test_tool_hub_startup_catalog.py`)
- [x] Registry contract coverage (`tests/test_tool_hub_registry_contracts.py`)
- [x] Domain-profile UI gating coverage (`tests/test_ui_domain_profile_gating.py`)
- [x] Celonis data-agent contract coverage (`tests/test_celonis_data_agent_contracts.py`)
- [x] Cross-profile regression pack script (`scripts/run_profile_regression_pack.ps1`)
- [x] Regression artifact generation under `.orchestration/test-runs/profile-regression/`
- [x] Profile-aware Tool Hub `status` health summary output (`agentic/tool-hub/start_tool_hub.ps1`)
- [x] Status summary test coverage (`tests/test_tool_hub_startup_catalog.py`)
- [x] Profile seed strategy plan + runner (`config/profile_seed_plan.json`, `scripts/seed_profile_data.ps1`)
- [x] Profile seed strategy test coverage (`tests/test_profile_seed_data_strategy.py`)

Latest full-pack artifact:

- `./.orchestration/test-runs/profile-regression/regression-pack-20260510T145844Z.json`

**Status:** 🚧 In progress (major hardening complete; additional suite consolidation pending)

---

### 🟠 Phase 2: Celonis Extraction (Weeks 5-8)

**Objective:** Extract Celonis integration as first submodule  
**Effort:** 40-50 hours  
**Dependencies:** Phase 1 complete

#### Scope

Extract to separate repo/submodule:
- Tenant extraction logic
- Snapshot management
- KPI calculations
- AI data agent integration
- Health probes & contracts

#### Keep in Core

- UI routes for Celonis
- Database models (shared)
- Configuration (shared)

#### Deliverables

- [ ] Separate celonis-extraction submodule
- [ ] Clean API boundaries
- [x] MCP tool specifications (invocation metadata, approval-bound write semantics)
- [x] Celonis error/request observability contract for invoke routes
- [x] Extraction readiness checklist artifact (`docs/celonis-extraction-readiness-checklist.md`)
- [ ] Test coverage >85%
- [ ] Documentation

**Status:** 🚧 In progress (boundary hardening done; extraction split not started)

---

### 🟠 Phase 3: Additional Modularization (Weeks 9+)

**Objective:** Extract additional domains  
**Effort:** 30-40 hours per domain

#### Wave A: GitLab Integration

- [ ] Extract to separate module
- [ ] Define adapter interface
- [ ] Full test coverage

#### Wave B: Knowledge Hub

- [ ] Obsidian sync module
- [ ] Forum integration
- [ ] Use case management

#### Wave C: Snapshot Engine (After Phase 2)

- [ ] Separate from Celonis
- [ ] Standalone operation
- [ ] Clear contracts

**Status:** 📋 Not started

---

### 🟡 Phase 4: Deployment & Teamwork (Weeks 10+)

**Objective:** Establish submodule governance  
**Effort:** 15-20 hours

#### Tasks

- [ ] Define ownership per module
- [ ] Create SLA/release cycle
- [ ] Setup upgrade matrix
- [ ] Document deprecation policy

**Status:** 📋 Not started

---

### 🟡 Phase 5: Risk Mitigation (Weeks 11+)

**Objective:** Safe migration path  
**Effort:** 20-30 hours

#### Strategy

- [ ] Shared model approach (not DB split)
- [ ] Activity log as platform capability
- [ ] Clear rollback procedures
- [ ] Migration governance

**Status:** 📋 Not started

---

### 🟡 Phase 6: Repository Cleanup (Weeks 12+)

**Objective:** Remove bloat & consolidate docs  
**Effort:** 20-30 hours

#### Tasks

- [ ] Archive external resources
- [ ] Remove old documentation
- [ ] Clean build artifacts
- [ ] Consolidate docs (see [documentation-consolidation-plan.md](documentation-consolidation-plan.md))
- [ ] Update .gitignore

**Cleanup Checklist:**

```bash
# 1. Archive external resources
mv external\ resources/ .archive/external-resources/
echo "external resources/" >> .gitignore

# 2. Archive old docs
rm -f QUICKSTART.md STARTUP.md STARTUP_CHECKLIST.md
git add .
git commit -m "docs: consolidate docs per documentation-consolidation-plan.md"

# 3. Remove dead code
python -m vulture src/ | grep "defined at" > /tmp/unused.txt
# Manually review and remove

# 4. Clean build artifacts
git clean -fdx build/ dist/ docs_site/ site/
```

**Status:** 📋 Not started

---

## Quick Wins (Start Now)

### ✅ Low effort, high impact

These can be done immediately without waiting for phases:

```bash
# 1. Add basic linting
pip install pylint
pylint src/ --disable=all --enable=unused-import

# 2. Check for dead code
pip install vulture
vulture src/

# 3. Format code
pip install black isort
black src/
isort src/

# 4. Type checking
pip install mypy
mypy src/ --ignore-missing-imports

# 5. Complexity analysis
pip install radon
radon cc src/ -a
radon mi src/ -m

# 6. Create code guidelines
# Create docs/CODE_REVIEW_GUIDE.md
# Create docs/TESTING_STANDARDS.md
# Create docs/ERROR_HANDLING.md
```

**Effort:** 4-6 hours  
**Impact:** ⭐⭐⭐⭐  
**Risk:** ✅ Very low

---

## Complexity Hotspots Summary

### 🔴 Critical (Must Fix)

| Hotspot | File | Lines | Issue | Phase |
|---------|------|-------|-------|-------|
| UI Routes | src/foundry/api/routes/ui.py | 9,810 | Monolithic | 1a |
| Service Layer | src/foundry/services/ | 8,000+ | No domain organization | 1b |

### 🟠 High (Should Fix)

| Hotspot | File | Lines | Issue | Phase |
|---------|------|-------|-------|-------|
| External Resources | external resources/ | 4.3M | Repository bloat | 6 |

### 🟡 Medium (Nice to Fix)

| Hotspot | File | Lines | Issue | Phase |
|---------|------|-------|-------|-------|
| Documentation | scattered | 400K | Scattered & duplicate | 6 |
| Test Organization | tests/ | 8,281 | Structure could improve | 1c |

---

## Tools & Infrastructure

### Static Analysis Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/asottile/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/asottile/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/pylint
    rev: 2.17.0
    hooks:
      - id: pylint
```

### GitHub Actions for CI/CD

```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.10
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Lint
        run: pylint src/ --exit-zero
      - name: Format check
        run: black --check src/
      - name: Type check
        run: mypy src/ --ignore-missing-imports
      - name: Tests
        run: pytest tests/ -v --cov=src/
```

---

## Success Metrics

### Code Quality Metrics

Track these during refactoring:

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Avg file size | 392 lines | <500 lines | 1a,1b |
| Max file size | 9,810 lines | <1,500 lines | 1a |
| Cyclomatic complexity | High | <15 per function | 1-3 |
| Test coverage | ~60% | >80% | 1c |
| Build time | 3-5s | 2-3s | 1a |
| Startup time | Current | Same or better | 1b |

### Process Metrics

| Metric | Target |
|--------|--------|
| Code review time | <24 hours |
| PR merge time | <48 hours |
| Test pass rate | >99% |
| Main branch stability | 0 broken builds |
| Onboarding time | <2 hours to first commit |

---

## Communication Plan

### Weekly Status

**Every Friday:**
- Completion status of current phase
- Blockers and risks
- Metrics update
- Next week's focus

### Monthly Retrospective

**Last Friday of month:**
- What went well
- What was challenging
- Adjustments to roadmap
- Team feedback

### Stakeholder Updates

**Monthly newsletter:**
- Completed improvements
- Upcoming changes
- Impact on shipping velocity
- No breaking changes notice

---

## Risk Management

### High-Risk Items

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Breaking routes | Medium | High | Comprehensive testing before merge |
| Import chaos | Medium | Medium | IDE refactoring + linting |
| Performance regression | Low | High | Profiling before/after |
| Team resistance | Low | Medium | Clear benefits communication |
| Extended timeline | Medium | Medium | Buffer time in estimate |

### Mitigation Strategies

1. **Comprehensive Testing**: Run tests before every commit
2. **Gradual Rollout**: Beta test with internal users
3. **Rollback Plan**: Every phase has rollback procedure
4. **Communication**: Weekly status updates to team
5. **Documentation**: Update docs during refactoring

---

## Training & Onboarding

### New Contributors Should Learn

1. **Code Structure**: docs/CODE_STRUCTURE.md
2. **Development Setup**: docs/DEVELOPMENT.md
3. **Testing**: docs/TESTING_STANDARDS.md
4. **Code Review**: docs/CODE_REVIEW_GUIDE.md
5. **Error Handling**: docs/ERROR_HANDLING.md

### Estimated Learning Time

- **Reading docs**: 2-3 hours
- **Setting up environment**: 1-2 hours
- **First contribution**: 2-4 hours
- **Total**: ~1 working day

---

## Resource Planning

### Team Requirements

- **Tech Lead**: Code review, architecture decisions (20% time)
- **Senior Engineer**: Phase lead, mentoring (50% time)
- **Engineers (2-3)**: Implementation (100% time)
- **QA**: Test coverage, E2E testing (30% time)

### Total Effort

- **120-160 engineering hours** over 12 weeks
- **0-5 hours blocking change** per week for main team

---

## Documentation to Create

| Document | Status | Owner |
|----------|--------|-------|
| [codebase-metrics-and-analysis.md](codebase-metrics-and-analysis.md) | ✅ Done | Analysis |
| [refactoring-ui-routes.md](refactoring-ui-routes.md) | ✅ Done | Routes |
| [service-layer-restructuring.md](service-layer-restructuring.md) | ✅ Done | Services |
| [documentation-consolidation-plan.md](documentation-consolidation-plan.md) | ✅ Done | Docs |
| CODE_STRUCTURE.md | 📋 Todo | Tech Lead |
| DEVELOPMENT.md | 📋 Todo | Tech Lead |
| CODE_REVIEW_GUIDE.md | 📋 Todo | QA Lead |
| TESTING_STANDARDS.md | 📋 Todo | QA Lead |
| ERROR_HANDLING.md | 📋 Todo | Senior Eng |
| MCP_CONTRACTS.md | 📋 Todo | Arch Lead |

---

## Next Steps (This Week)

1. ✅ **Review** this roadmap with team
2. ✅ **Discuss** priorities and timeline
3. ⬜ **Setup** static analysis tools
4. ⬜ **Create** code quality standards doc
5. ⬜ **Plan** Phase 1 sprint

---

**Master Roadmap Document**  
**Last Updated:** May 10, 2026  
**Next Review:** After Phase 0 completion  
**Questions:** See [codebase-metrics-and-analysis.md](codebase-metrics-and-analysis.md) for analysis

