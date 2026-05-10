# Documentation Consolidation & Integration Plan

**Status:** Recommended  
**Priority:** 🟡 Medium  
**Effort:** 20-30 hours  
**Timeline:** Phase 6 (after code refactoring)

---

## Current State Analysis

### Scattered Documentation

Current documentation spread across multiple locations:

```
├── README.md                           (476 lines)
├── QUICKSTART.md                       (122 lines)
├── STARTUP.md                          (199 lines)
├── STARTUP_CHECKLIST.md                (190 lines)
├── IMPLEMENTATION_SUMMARY.md           (370 lines)
├── docs/
│   ├── index.md                        (Master index)
│   ├── agent-feature-roadmap.md
│   ├── master-roadmap.md
│   ├── dev-roadmap.md
│   ├── domain-submodule-local-first-replatform.md
│   ├── extension-integration.md
│   ├── codebase-metrics-and-analysis.md    (NEW)
│   ├── refactoring-ui-routes.md            (NEW)
│   ├── admin/                          (Admin guides)
│   ├── guides/                         (User guides)
│   ├── troubleshooting/                (Troubleshooting)
│   ├── developer/                      (Developer docs)
│   └── adr/                            (Architecture decisions)
├── docs_site/                          (Built HTML)
└── docu/                               (Legacy HTML)
```

### Problems

1. ❌ **Duplication**: STARTUP.md, QUICKSTART.md, README.md overlap
2. ❌ **Inconsistency**: Different formats and styles
3. ❌ **Scattered**: Related information split across files
4. ❌ **Outdated**: Some docs not maintained with code changes
5. ❌ **Navigation**: Hard to find information
6. ❌ **Built artifacts**: docs_site/ and docu/ folders pollute repo

---

## Proposed Structure

### New Consolidated Documentation

```
docs/
├── README.md                           (Index & overview)
├── index.md                            (MkDocs home)
├── getting-started/
│   ├── overview.md                     (What is Celonis Delivery Forge?)
│   ├── quickstart.md                   (5-minute start)
│   ├── installation.md                 (Setup & requirements)
│   ├── first-run.md                    (First steps after install)
│   └── profiles.md                     (Feature profiles explained)
├── user/
│   ├── projects.md                     (Managing projects)
│   ├── assets.md                       (Asset library)
│   ├── reviews.md                      (Review workflows)
│   ├── deployments.md                  (Deployment tracking)
│   ├── templates.md                    (Using templates)
│   └── integrations/
│       ├── celonis.md                  (Celonis integration guide)
│       ├── gitlab.md                   (GitLab integration guide)
│       └── knowledge-hub.md            (Knowledge hub usage)
├── developer/
│   ├── setup.md                        (Development environment)
│   ├── architecture.md                 (System architecture)
│   ├── code-structure.md               (Directory & module guide)
│   ├── api-development.md              (Adding API endpoints)
│   ├── ui-development.md               (Adding UI routes)
│   ├── service-development.md          (Creating services)
│   ├── testing.md                      (Testing guide)
│   ├── database.md                     (Database & migrations)
│   ├── error-handling.md               (Error patterns)
│   └── deployment.md                   (Deployment strategies)
├── admin/
│   ├── organization-setup.md           (Org administration)
│   ├── user-management.md              (User provisioning)
│   ├── feature-rollout.md              (Feature gates & profiles)
│   ├── security.md                     (Security & compliance)
│   ├── backup-restore.md               (Backup procedures)
│   └── monitoring.md                   (Health & monitoring)
├── architecture/
│   ├── overview.md                     (System architecture)
│   ├── multi-tenancy.md                (Multi-tenancy design)
│   ├── data-flow.md                    (Data flow diagrams)
│   ├── security.md                     (Security architecture)
│   ├── scalability.md                  (Scalability & performance)
│   └── decisions/                      (ADRs)
├── roadmap/
│   ├── product-roadmap.md              (Feature roadmap)
│   ├── domain-submodules.md            (Domain extraction plan)
│   ├── agent-orchestration.md          (Agent roadmap)
│   └── celonis-integration.md          (Celonis roadmap)
├── troubleshooting/
│   ├── common-issues.md                (FAQ & common problems)
│   ├── startup-issues.md               (Startup troubleshooting)
│   ├── deployment-issues.md            (Deployment problems)
│   └── performance.md                  (Performance tuning)
├── quality/
│   ├── codebase-metrics.md             (Code metrics & analysis)
│   ├── complexity-hotspots.md          (Areas needing refactoring)
│   ├── refactoring-guide.md            (Refactoring strategies)
│   └── code-review.md                  (Code review standards)
└── mkdocs.yml                          (Updated config)
```

---

## Migration Strategy

### Phase 1: Consolidate Root-Level Docs (Week 1)

1. **Create single `README.md`** that includes:
   - What is Delivery Forge?
   - Key features overview
   - Quick links to docs
   - Links to other files

2. **Create `docs/getting-started/quickstart.md`**:
   - Move QUICKSTART.md content
   - Move STARTUP.md content
   - Move STARTUP_CHECKLIST.md content
   - Add visual flowchart

3. **Archive old files**:
   - Keep originals temporarily (rename to `.archived`)
   - Create DEPRECATION_NOTICE.md in each
   - Plan removal in Phase 7

### Phase 2: Reorganize Developer Docs (Week 2)

1. **Create `docs/developer/` structure**
2. **Extract from scattered docs**:
   - Architecture from docs/*.md → architecture/overview.md
   - Setup from README → developer/setup.md
   - Database info → developer/database.md

3. **Create new guides**:
   - API development patterns
   - UI route development
   - Service creation
   - Testing practices

### Phase 3: Consolidate Admin Docs (Week 2)

1. **Create `docs/admin/` structure**
2. **Move/consolidate**:
   - Organization setup
   - User management
   - Feature gates
   - Security guidance

### Phase 4: Create Architecture Decision Records (Week 1)

1. **Move existing ADRs** to `docs/architecture/decisions/`
2. **Create template** for future ADRs
3. **Document key decisions**:
   - Why SQLModel + Pydantic
   - Why multi-tenant design
   - Why Jinja2 templates
   - Why FastAPI

**Example ADR:**

```markdown
# ADR-001: Use FastAPI for REST API

**Status:** Accepted  
**Date:** 2024-01-15  
**Authors:** Development Team

## Decision

We will use FastAPI as the primary web framework for the REST API.

## Context

- Need modern Python async framework
- Require automatic OpenAPI documentation
- Need fast performance
- Require strong type hints

## Consequences

- ✅ Modern async/await support
- ✅ Automatic API documentation
- ✅ Fast performance
- ✅ Strong ecosystem
- ⚠️ Newer framework (less StackOverflow answers)

## Related

- Domain: Platform
- References: ADR-002 (Pydantic validation)
```

### Phase 5: Update MkDocs Configuration (Week 1)

Update `mkdocs.yml` for new structure:

```yaml
site_name: Celonis Delivery Forge Docs
site_description: Multi-tenant delivery governance platform
repo_url: https://github.com/celonis/delivery-forge
docs_dir: docs
site_dir: docs_site

theme:
  name: material
  features:
    - navigation.instant
    - navigation.sections
    - navigation.tabs
    - search.suggest
    - toc.integrate

nav:
  - Home: index.md
  - Getting Started:
      - Overview: getting-started/overview.md
      - Quickstart: getting-started/quickstart.md
      - Installation: getting-started/installation.md
      - Profiles: getting-started/profiles.md
  - User Guide:
      - Projects: user/projects.md
      - Assets: user/assets.md
      - Reviews: user/reviews.md
      - Integrations:
          - Celonis: user/integrations/celonis.md
          - GitLab: user/integrations/gitlab.md
          - Knowledge Hub: user/integrations/knowledge-hub.md
  - Developer Guide:
      - Setup: developer/setup.md
      - Architecture: developer/architecture.md
      - Code Structure: developer/code-structure.md
      - API Development: developer/api-development.md
      - UI Development: developer/ui-development.md
      - Testing: developer/testing.md
  - Admin Guide:
      - Organization Setup: admin/organization-setup.md
      - User Management: admin/user-management.md
      - Feature Rollout: admin/feature-rollout.md
      - Security: admin/security.md
  - Architecture:
      - System Design: architecture/overview.md
      - Data Flow: architecture/data-flow.md
      - Decisions: architecture/decisions/
  - Code Quality:
      - Metrics: quality/codebase-metrics.md
      - Complexity Hotspots: quality/complexity-hotspots.md
      - Refactoring Guide: quality/refactoring-guide.md
  - Roadmap:
      - Product Roadmap: roadmap/product-roadmap.md
      - Domain Submodules: roadmap/domain-submodules.md
  - Troubleshooting:
      - Common Issues: troubleshooting/common-issues.md
      - Startup Issues: troubleshooting/startup-issues.md
```

### Phase 6: Build & Deploy Docs Site (Week 3)

1. **Generate HTML**:
   ```bash
   mkdocs build
   ```

2. **Test locally**:
   ```bash
   mkdocs serve
   # Visit http://localhost:8000
   ```

3. **Deploy to docs_site/**:
   - Commit built artifacts
   - Or use CI/CD to auto-build on push

4. **Update navigation**:
   - Add link to docs in main README
   - Update extension popup
   - Update in-app help links

### Phase 7: Cleanup (Week 4)

1. **Remove archived files**:
   - Delete STARTUP.md, QUICKSTART.md originals
   - Delete STARTUP_CHECKLIST.md
   - Delete IMPLEMENTATION_SUMMARY.md

2. **Remove legacy docs**:
   - Delete docu/ folder
   - Update .gitignore for docs_site/ (or commit it)

3. **Update .gitignore**:
   ```
   # Built docs
   site/
   docs_site/
   
   # Old docs (archived)
   *.archived
   ```

---

## Content Guidelines

### Writing Style

- **Audience**: Developers, admins, end-users
- **Tone**: Professional, clear, concise
- **Length**: 1-3 pages per topic
- **Code**: Always include examples
- **Links**: Cross-reference related docs

### Structure Per Document

```markdown
# Title

**Status:** Status line (e.g., "Stable", "Beta", "Proposed")  
**Last Updated:** Date  
**Audience:** Who should read this

## Overview

One paragraph summary.

## Quick Start / Concepts

Essential information for quick understanding.

## Detailed Guide

Step-by-step instructions or deeper explanation.

## Examples

Code examples and use cases.

## Common Issues

FAQ and troubleshooting.

## See Also

Links to related documents.
```

### Code Examples

All code examples should:
- ✅ Be runnable
- ✅ Include imports
- ✅ Show output
- ✅ Have explanations
- ✅ Link to full examples in repo

```markdown
## Example: Creating a Project

\`\`\`python
from src.foundry.models import Project

# Create new project
project = Project(
    name="Acme Implementation",
    description="End-to-end process mining",
    organization_id="org-123"
)

# Project created successfully
print(f"Created: {project.id}")
\`\`\`

See [Full example](../examples/create-project.py).
```

---

## Integration with App

### In-App Help Links

Update app to link to documentation:

```python
# src/foundry/services/help_links.py
HELP_LINKS = {
    # Getting started
    "setup": "https://docs.example.com/getting-started/installation",
    "profiles": "https://docs.example.com/getting-started/profiles",
    
    # User guides
    "projects": "https://docs.example.com/user/projects",
    "assets": "https://docs.example.com/user/assets",
    
    # Integration guides
    "celonis_setup": "https://docs.example.com/user/integrations/celonis",
    "gitlab_setup": "https://docs.example.com/user/integrations/gitlab",
}
```

Update templates:

```html
<!-- src/foundry/ui/templates/base.html -->
<a href="{{ get_help_link('projects') }}" class="help-icon">?</a>
```

### Chrome Extension Help

Update extension manifest:

```json
{
  "homepage_url": "https://docs.example.com",
  "icons": {
    "16": "images/icon-16.png"
  }
}
```

---

## Metrics for Success

✅ Project complete when:

1. All docs consolidated into single docs/ structure
2. MkDocs builds successfully with no warnings
3. 100% of links are internal and work
4. Search works across all pages
5. Mobile-responsive design verified
6. Team reviews and approves structure
7. Deployed to docs_site/
8. In-app help links updated
9. Old documentation archived or deleted

---

## Timeline & Dependencies

| Phase | Week | Dependencies | Output |
|-------|------|--------------|--------|
| 1: Consolidate root | 1 | Phase 0 | Single README + quickstart |
| 2: Reorganize dev docs | 2 | Phase 1 | Developer guide structure |
| 3: Consolidate admin docs | 2 | Phase 1 | Admin guide structure |
| 4: ADRs | 1 | Phase 1 | Architecture decisions |
| 5: Update MkDocs | 1 | Phase 2 | mkdocs.yml |
| 6: Build & test | 3 | Phase 5 | Built docs site |
| 7: Cleanup | 4 | Phase 6 | Archived old docs |

**Critical Path:** ~4 weeks after code refactoring  
**Can be parallel with:** Code refactoring (Phases 1-3)

---

## Rollout Checklist

- [ ] Review current documentation and identify overlap
- [ ] Create new directory structure in docs/
- [ ] Move/consolidate content into new locations
- [ ] Create ADR template and migrate existing decisions
- [ ] Update mkdocs.yml with new navigation
- [ ] Write new developer guides (API, UI, services)
- [ ] Write new admin guides (setup, users, security)
- [ ] Test all internal links
- [ ] Build and preview docs locally
- [ ] Update in-app help link URLs
- [ ] Team review and approval
- [ ] Deploy to docs_site/
- [ ] Archive old documentation files
- [ ] Update main README with doc links
- [ ] Create docs update process document
- [ ] Train team on documentation standards

---

## Maintenance Plan

### Regular Updates

**Monthly:**
- Review new features added to code
- Update relevant documentation
- Fix any broken links

**Quarterly:**
- Audit documentation completeness
- Verify code examples still work
- Update roadmaps

**Annually:**
- Major documentation review
- Update style guide if needed
- Archive outdated sections

### Ownership

- **Getting Started**: Product Manager
- **User Guide**: UX Team + Product
- **Developer Guide**: Development Team
- **Admin Guide**: DevOps Team
- **Architecture**: Tech Lead
- **Roadmap**: Product Manager + Tech Lead

---

**Implementation Lead:** Documentation Owner  
**Timeline:** Phase 6 (4 weeks after code refactoring)  
**Budget:** ~30 hours engineering time  
**Related Files:** docs/mkdocs.yml, docs/index.md

