# Critical Refactoring Guide: UI Route Module

**Priority:** 🔴 CRITICAL  
**Estimated Effort:** 40-60 hours  
**Risk Level:** Medium (requires comprehensive testing)  
**Timeline:** 2-3 weeks

---

## Problem Statement

The `src/foundry/api/routes/ui.py` file has grown to **9,810 lines**, making it:

- ❌ Impossible to review or understand at a glance
- ❌ Difficult to test individual endpoints
- ❌ Hard to locate specific functionality
- ❌ A bottleneck for parallel development
- ❌ Violates Python best practices (max ~1000 lines/file)
- ❌ Creates cognitive overload for contributors

### Current Structure

```python
# src/foundry/api/routes/ui.py (9,810 lines)

from fastapi import APIRouter, Request, Depends, HTTPException
# ... 200 imports ...

router = APIRouter()

# ~150-200 route handlers (all mixed together)

@router.get("/")
def get_dashboard(): ...

@router.get("/projects")
def get_projects(): ...

@router.post("/projects/{id}")
def update_project(): ...

# ... 9,800 more lines ...
```

---

## Proposed Solution

### Implemented Tranche (2026-05-10)

- Extracted `/local-knowledge-ui/status` from monolithic `ui.py` into dedicated route module:
    - `src/foundry/api/routes/ui_knowledge_status.py`
- Wired dedicated router in `src/foundry/api/main.py`.
- Added/updated tests in `tests/test_local_knowledge_ui.py`.

This establishes the migration pattern for subsequent route slices while preserving endpoint behavior.

### Step 1: Identify All Route Groups

Analyze current ui.py to categorize routes by domain:

| Category | Estimated Routes | Estimated Lines |
|----------|------------------|-----------------|
| Navigation & Home | 5-10 | 500-800 |
| Projects | 10-15 | 1,000-1,500 |
| Assets | 10-15 | 1,000-1,500 |
| Reviews | 10-15 | 1,000-1,500 |
| Deployments | 5-10 | 500-800 |
| Admin Panels | 10-15 | 1,000-1,500 |
| Settings | 5-10 | 500-800 |
| Templates | 5-10 | 500-800 |
| Feature Rollout | 5-10 | 500-800 |
| Utils/Health | 5-10 | 500-800 |

**Total: ~150-180 route handlers across ~9,800 lines**

---

### Step 2: New File Structure

Create focused modules with clear responsibilities:

```
src/foundry/api/routes/
├── __init__.py                          [Router registration]
├── ui/                                  [New subdirectory]
│   ├── __init__.py
│   ├── navigation.py                    [Home, nav, sidebar (500-800 lines)]
│   ├── projects.py                      [Project CRUD, listing (1,000-1,500)]
│   ├── assets.py                        [Asset browser, details (1,000-1,500)]
│   ├── reviews.py                       [Review workflow views (1,000-1,500)]
│   ├── deployments.py                   [Deployment tracking (500-800)]
│   ├── admin.py                         [Admin panels, settings (1,000-1,500)]
│   ├── templates.py                     [Template management (500-800)]
│   ├── feature_rollout.py               [Profile gates, feature flags (500-800)]
│   ├── integrations.py                  [Celonis, GitLab UI (1,000-1,500)]
│   └── health.py                        [Status, health checks (300-500)]
├── celonis.py                           [Keep existing]
├── gitlab.py                            [Keep existing]
├── api_tokens.py                        [Keep existing]
└── tool_hub.py                          [Keep existing]
```

**Result:** Each file 500-1,500 lines with clear single responsibility

---

### Step 3: Migration Strategy

#### Phase 1: Infrastructure (Week 1)

1. **Create new directory structure:**
   ```bash
   mkdir src/foundry/api/routes/ui
   touch src/foundry/api/routes/ui/__init__.py
   ```

2. **Create each new module with stubs:**
   ```python
   # src/foundry/api/routes/ui/navigation.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/ui/navigation", tags=["ui_navigation"])
   
   # Routes will be migrated here
   ```

3. **Update main router to include new modules:**
   ```python
   # src/foundry/api/routes/__init__.py
   from fastapi import APIRouter
   from . import celonis, gitlab, api_tokens, tool_hub
   from .ui import navigation, projects, assets, reviews, deployments, admin, templates, feature_rollout, integrations, health
   
   def get_api_router():
       router = APIRouter()
       
       # Include all route modules
       router.include_router(navigation.router)
       router.include_router(projects.router)
       # ... etc
       
       return router
   ```

#### Phase 2: Extract Routes by Category (Week 2)

For each category:

1. **Identify all matching route handlers** in ui.py
2. **Copy to new module**
3. **Extract shared dependencies** (template rendering, decorators, etc.)
4. **Update imports** in new module
5. **Write/copy tests** for the routes
6. **Test locally** to ensure routes still work

**Example - Navigation Routes:**

```python
# src/foundry/api/routes/ui/navigation.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from src.foundry.services.auth import get_current_user

router = APIRouter(prefix="", tags=["ui_navigation"])

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Home/dashboard view."""
    # ... implementation ...
    pass

@router.get("/sidebar", response_class=HTMLResponse)
async def get_sidebar(current_user = Depends(get_current_user)):
    """Sidebar navigation."""
    pass

@router.get("/nav-menu", response_class=HTMLResponse)
async def get_nav_menu(current_user = Depends(get_current_user)):
    """Top navigation menu."""
    pass
```

#### Phase 3: Create Template Rendering Service (Week 2)

Extract common template rendering logic:

```python
# src/foundry/services/ui_renderer.py
from fastapi import Request
from jinja2 import Template

class UIRenderer:
    """Centralized template rendering for UI routes."""
    
    def __init__(self, template_loader):
        self.loader = template_loader
    
    def render_dashboard(self, request: Request, user, data):
        """Render dashboard template."""
        template = self.loader.get_template("dashboard.html")
        return template.render(request=request, user=user, **data)
    
    def render_project_list(self, request: Request, projects):
        """Render projects list."""
        template = self.loader.get_template("projects/list.html")
        return template.render(request=request, projects=projects)
    
    # ... etc
```

Then use in routes:

```python
@router.get("/projects", response_class=HTMLResponse)
async def get_projects(
    request: Request,
    current_user = Depends(get_current_user),
    renderer = Depends(get_ui_renderer)
):
    projects = await get_user_projects(current_user)
    return renderer.render_project_list(request, projects)
```

#### Phase 4: Remove Old ui.py and Update References (Week 3)

1. **Verify all routes migrated** by comparing line-by-line
2. **Update imports** in:
   - `src/foundry/api/main.py`
   - Any other files importing from ui.py
3. **Run full test suite** to ensure nothing broke
4. **Delete old** `src/foundry/api/routes/ui.py`

---

### Step 4: File Size Goals

**Target Structure:**

| File | Target Lines | Status |
|------|--------------|--------|
| navigation.py | 600-800 | New |
| projects.py | 1,200-1,500 | New |
| assets.py | 1,200-1,500 | New |
| reviews.py | 1,200-1,500 | New |
| deployments.py | 600-800 | New |
| admin.py | 1,000-1,300 | New |
| templates.py | 600-800 | New |
| feature_rollout.py | 600-800 | New |
| integrations.py | 1,000-1,300 | New |
| health.py | 300-500 | New |
| **Total UI Routes** | **9,000-10,000** | Maintainable ✅ |

**Key Improvement:** Each file is **independently testable** and **can be understood in 1-2 hours**.

---

## Testing Strategy

### Unit Tests

Create test file for each route module:

```python
# tests/ui/test_projects.py
import pytest
from fastapi.testclient import TestClient
from src.foundry.api.main import app
from src.foundry.models import User, Organization

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(user):
    return {"Authorization": f"Bearer {user.token}"}

def test_get_projects_list(client, auth_headers):
    """Test fetching projects list."""
    response = client.get("/ui/projects", headers=auth_headers)
    assert response.status_code == 200
    assert "projects" in response.text

def test_get_project_detail(client, auth_headers, project):
    """Test fetching single project."""
    response = client.get(f"/ui/projects/{project.id}", headers=auth_headers)
    assert response.status_code == 200
    assert project.name in response.text

def test_create_project(client, auth_headers):
    """Test creating new project."""
    response = client.post(
        "/ui/projects",
        headers=auth_headers,
        data={"name": "New Project"}
    )
    assert response.status_code in [200, 201, 302]  # Redirect to detail
```

### Integration Tests

Test route interactions with database and services:

```python
# tests/integration/test_projects_workflow.py
def test_complete_project_workflow(client, auth_headers, db_session):
    """Test full project creation/edit/view workflow."""
    # Create
    create_response = client.post(
        "/ui/projects",
        headers=auth_headers,
        data={"name": "Integration Test"}
    )
    assert create_response.status_code in [200, 201, 302]
    
    # Verify in database
    project = db_session.query(Project).filter_by(name="Integration Test").first()
    assert project is not None
    
    # Update
    update_response = client.post(
        f"/ui/projects/{project.id}",
        headers=auth_headers,
        data={"name": "Updated Name"}
    )
    assert update_response.status_code in [200, 302]
    
    # Verify update
    assert project.name == "Updated Name"
```

### E2E Tests (Playwright)

```python
# tests/e2e/test_projects_ui.py
import pytest
from playwright.sync_api import expect

def test_projects_page_navigation(page, login_url):
    """Test navigating to projects page."""
    page.goto(login_url)
    page.fill("input[name='username']", "test@example.com")
    page.fill("input[name='password']", "password")
    page.click("button:has-text('Login')")
    
    # Navigate to projects
    page.click("text=Projects")
    expect(page).to_have_url("**/ui/projects")
    expect(page.locator("h1")).to_contain_text("Projects")
```

---

## Rollout Checklist

- [ ] **Week 1**: Create new directory structure and stub files
- [ ] **Week 1**: Update main router registration
- [ ] **Week 2**: Extract first 2-3 route modules (navigation, projects)
- [ ] **Week 2**: Create UI renderer service
- [ ] **Week 2**: Write unit tests for extracted modules
- [ ] **Week 2**: Extract remaining route modules
- [ ] **Week 3**: Update all imports
- [ ] **Week 3**: Run full test suite
- [ ] **Week 3**: Delete old ui.py file
- [ ] **Week 3**: Add comprehensive documentation
- [ ] **Code Review**: Team review of new structure
- [ ] **Merge**: Merge to main branch with deprecation notice
- [ ] **Release Notes**: Document migration in changelog

---

## Expected Benefits

### Code Quality
- ✅ Each file understandable in 1-2 hours
- ✅ Clear single responsibility per module
- ✅ Easier to locate functionality
- ✅ Reduced cognitive load

### Testing
- ✅ Easier to write focused unit tests
- ✅ Faster test execution (smaller scope)
- ✅ Better test isolation
- ✅ Clearer test intent

### Development
- ✅ Faster code reviews
- ✅ Easier to merge multiple features
- ✅ Better parallel development
- ✅ Clearer git history

### Maintenance
- ✅ Easier bug fixes
- ✅ Easier to understand dependencies
- ✅ Easier onboarding for new team members
- ✅ Better future extensibility

---

## Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| **Breaking routes during migration** | Medium | High | Comprehensive testing, parallel runs |
| **Missing routes** | Low | High | Line-by-line comparison before deletion |
| **Import errors** | Medium | Medium | IDE refactoring tools, linting |
| **Performance regression** | Low | Medium | Load testing before/after |
| **User impact** | Low | High | Beta testing with internal users |

---

## Documentation Updates Required

After refactoring:

1. **Update `CODE_STRUCTURE.md`:**
   - Document new UI route organization
   - Add file-by-file guide
   - Link to route examples

2. **Create `UI_ROUTES_GUIDE.md`:**
   - How to add new UI route
   - Common patterns and conventions
   - Template rendering examples

3. **Update `README.md`:**
   - Mention refactored structure
   - Link to developer guide

---

## Success Criteria

✅ Project complete when:

1. All 150+ routes moved to new modules
2. Average file size is 500-1,500 lines
3. Each module has >80% test coverage
4. All tests pass (unit, integration, E2E)
5. Documentation complete and reviewed
6. No functional changes to routes
7. Team approval obtained
8. Deployed to production without incidents

---

**Ownership:** Development Team  
**Timeline:** Weeks 2-3 of refactoring plan  
**Dependencies:** Phase 1 architecture contracts must be defined first  
**Related Issues:** Complexity hotspot #1

