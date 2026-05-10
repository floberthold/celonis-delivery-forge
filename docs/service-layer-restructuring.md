# Service Layer Restructuring Guide

**Priority:** 🟠 High  
**Estimated Effort:** 30-40 hours  
**Timeline:** Phase 1 (parallel to route refactoring)  
**Risk:** Medium (affects business logic)

---

## Current State

## Published Mapping (2026-05-10)

Initial service-to-domain allocation is now published and validated:

- `config/service_domain_mapping.json`
- `docs/service-domain-mapping.md`
- `tests/test_service_domain_mapping.py`

Scaffolding milestone implemented:

- `src/foundry/services/platform/__init__.py`
- `src/foundry/services/delivery/__init__.py`
- `src/foundry/services/celonis/__init__.py`
- `src/foundry/services/knowledge/__init__.py`
- `src/foundry/services/integrations/__init__.py`
- `src/foundry/services/orchestration/__init__.py`
- `src/foundry/services/shared/__init__.py`
- `tests/test_service_domain_package_scaffolding.py`

Low-risk migration kickoff (compatibility shims retained):

- `feature_rollout.py` moved to `services/platform/feature_rollout.py`
- `email_service.py` moved to `services/integrations/email_service.py`
- `template_seed.py` moved to `services/delivery/template_seed.py`
- `use_case_views.py` moved to `services/knowledge/use_case_views.py`
- `trycelonis_demo_rebuild.py` moved to `services/integrations/trycelonis_demo_rebuild.py`
- `ingest_service.py` moved to `services/integrations/ingest_service.py`
- `florian_script_seed.py` moved to `services/delivery/florian_script_seed.py`
- `activity_log.py` moved to `services/delivery/activity_log.py`
- `project_service.py` moved to `services/delivery/project_service.py`
- `review_service.py` moved to `services/delivery/review_service.py`
- `template_service.py` moved to `services/delivery/template_service.py`
- `todo_service.py` moved to `services/delivery/todo_service.py`
- `celonis_contracts.py` moved to `services/celonis/celonis_contracts.py`
- `celonis_data_agent_service.py` moved to `services/celonis/celonis_data_agent_service.py`
- `celonis_deployment_service.py` moved to `services/celonis/celonis_deployment_service.py`
- `celonis_payload_extractors.py` moved to `services/celonis/celonis_payload_extractors.py`
- `snapshot_service.py` moved to `services/celonis/snapshot_service.py`
- `snapshot_coverage_service.py` moved to `services/celonis/snapshot_coverage_service.py`
- `snapshot_detail_extractors.py` moved to `services/celonis/snapshot_detail_extractors.py`
- `snapshot_export_service.py` moved to `services/celonis/snapshot_export_service.py`
- `snapshot_git_service.py` moved to `services/celonis/snapshot_git_service.py`
- Legacy imports preserved via shim modules for backward compatibility

High-coupling cutover update:

- Root high-coupling service modules were removed after import migration to celonis-domain modules.
- Route and test imports now reference `foundry.services.celonis.*` paths directly.

Validation evidence (targeted):

- `tests/test_service_low_risk_shims.py`
- `tests/test_ingest_repo_sync_api.py`
- `tests/test_foundry_admin_ui.py`
- `tests/test_tenant_setup_wizard_ui.py`
- `tests/test_client_health_ui.py`
- `tests/test_ui_templates_routes.py`
- `tests/test_celonis_ui_route_presence.py`
- `tests/test_celonis_data_agent_contracts.py`
- `tests/test_snapshot_detail_extraction.py`
- `tests/test_snapshots_api.py`

This mapping is used as the migration source of truth for Phase 1b sequencing.

### Service Inventory

**Current `src/foundry/services/` directory contains ~25 modules:**

```
services/
├── auth.py                    (Authentication & JWT)
├── organization.py            (Organization management)
├── user.py                    (User management)
├── project.py                 (Project operations)
├── asset.py                   (Asset management)
├── review.py                  (Review workflows)
├── deployment.py              (Deployment tracking)
├── template.py                (Template management)
├── kpi.py                     (KPI calculations)
├── snapshot.py                (Snapshot operations)
├── celonis_service.py          (Celonis API integration)
├── celonis_data_agent.py       (AI agent integration)
├── celonis_contracts.py        (MCP contracts)
├── gitlab_service.py           (GitLab integration)
├── email_service.py            (Email notifications)
├── file_storage.py            (File operations)
├── feature_rollout.py          (Feature gates)
├── tool_hub.py                (Tool orchestration)
├── timeline.py                (Activity logging)
├── todo.py                    (Todo management)
├── cache.py                   (Caching layer)
├── database.py                (Database utilities)
├── error_handler.py           (Error handling)
├── observability.py           (Logging/monitoring)
├── utils.py                   (Misc utilities)
└── __init__.py
```

**Total: ~25 files, estimated 8,000-10,000 lines**

### Problems

1. **Unclear Boundaries**: Hard to know which service owns what
2. **Potential Duplication**: Error handling and validation might be duplicated
3. **Tangled Dependencies**: Services likely depend on each other in circular ways
4. **Mixed Concerns**: Some services do too much
5. **No Clear Ownership**: No obvious DRI for each domain
6. **Hard to Extract**: Difficult to make modules independent
7. **Testing**: Service interdependencies make unit testing hard

---

## Proposed Architecture

### Domain-Scoped Organization

```
services/
├── __init__.py                           [Exports and initialization]
├── platform/
│   ├── __init__.py
│   ├── organization.py                   [Organization CRUD & settings]
│   ├── user.py                           [User management & provisioning]
│   ├── auth.py                           [Authentication & JWT]
│   ├── permission.py                     [Permission evaluation]
│   └── tenant.py                         [Multi-tenancy enforcement]
├── delivery/
│   ├── __init__.py
│   ├── project.py                        [Project management]
│   ├── asset.py                          [Asset library & versioning]
│   ├── review.py                         [Review workflows]
│   ├── deployment.py                     [Deployment tracking]
│   ├── template.py                       [Template management]
│   ├── timeline.py                       [Activity logging]
│   └── todo.py                           [Todo management]
├── celonis/
│   ├── __init__.py
│   ├── tenant_extraction.py              [Celonis tenant management]
│   ├── snapshot.py                       [Snapshot operations]
│   ├── kpi.py                            [KPI calculations]
│   ├── data_agent.py                     [AI data agent wrapper]
│   ├── contracts.py                      [MCP invocation contracts]
│   └── health.py                         [Health probe implementation]
├── knowledge/
│   ├── __init__.py
│   ├── gateway.py                        [Local knowledge gateway]
│   ├── obsidian.py                       [Obsidian wiki sync]
│   ├── use_case.py                       [Use case management]
│   └── forum.py                          [Forum integration]
├── integrations/
│   ├── __init__.py
│   ├── gitlab.py                         [GitLab integration adapter]
│   ├── email.py                          [Email notifications]
│   └── file_storage.py                   [File operations]
├── orchestration/
│   ├── __init__.py
│   ├── tool_hub.py                       [Tool registry & lifecycle]
│   └── mcp.py                            [MCP server management]
├── shared/
│   ├── __init__.py
│   ├── error_handling.py                 [Common error patterns]
│   ├── observability.py                  [Logging & monitoring]
│   ├── cache.py                          [Caching layer]
│   ├── database.py                       [DB utilities]
│   └── validation.py                     [Common validators]
└── factories.py                           [Service factory for DI]
```

**Benefits:**
- ✅ Clear domain boundaries
- ✅ Easy to understand which module does what
- ✅ Better for future extraction to submodules
- ✅ Easier to test (domain-scoped dependencies)
- ✅ Clear ownership per domain

---

## Service Interface Standards

### Every Service Should Have

1. **Clear Responsibilities**: One domain concern
2. **Dependency Injection**: Accept dependencies in `__init__`
3. **Error Handling**: Raise domain-specific exceptions
4. **Logging**: Log important operations
5. **Type Hints**: Full type annotations
6. **Docstrings**: Class and method documentation
7. **Tests**: Unit test coverage >80%

### Standard Service Template

```python
# src/foundry/services/delivery/project.py
"""
Project management service.

Handles all project-related operations including creation, updates,
querying, and deletion. Enforces organization scoping.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from src.foundry.models import Project, Organization, User
from src.foundry.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from src.foundry.services.shared.error_handling import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ValidationError
)
from src.foundry.services.platform.permission import PermissionService

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects within organizations."""
    
    def __init__(
        self,
        db: Session,
        permission_service: PermissionService
    ):
        """Initialize project service.
        
        Args:
            db: Database session
            permission_service: Permission checker
        """
        self.db = db
        self.permission_service = permission_service
    
    async def create_project(
        self,
        org_id: str,
        user_id: str,
        data: ProjectCreate
    ) -> Project:
        """Create new project.
        
        Args:
            org_id: Organization ID
            user_id: User creating project
            data: Project data
            
        Returns:
            Created project
            
        Raises:
            PermissionDeniedError: User lacks permission
            ValidationError: Invalid data
        """
        # Check permissions
        if not await self.permission_service.can_create_project(user_id, org_id):
            raise PermissionDeniedError("Cannot create projects in this org")
        
        # Validate organization exists
        org = self.db.query(Organization).filter_by(id=org_id).first()
        if not org:
            raise ResourceNotFoundError(f"Organization {org_id} not found")
        
        # Create project
        project = Project(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            created_by=user_id
        )
        self.db.add(project)
        self.db.commit()
        
        logger.info(f"Project created: {project.id} in org {org_id}")
        return project
    
    async def get_project(
        self,
        project_id: str,
        org_id: str,
        user_id: str
    ) -> Project:
        """Get project by ID with permission check.
        
        Args:
            project_id: Project ID
            org_id: Organization ID
            user_id: User requesting
            
        Returns:
            Project
            
        Raises:
            ResourceNotFoundError: Project not found
            PermissionDeniedError: User lacks access
        """
        project = self.db.query(Project).filter_by(
            id=project_id,
            organization_id=org_id
        ).first()
        
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")
        
        if not await self.permission_service.can_view_project(user_id, project_id):
            raise PermissionDeniedError("Cannot view this project")
        
        return project
    
    async def list_projects(
        self,
        org_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Project]:
        """List projects accessible to user.
        
        Args:
            org_id: Organization ID
            user_id: User requesting
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of projects
        """
        query = self.db.query(Project).filter_by(organization_id=org_id)
        
        # Apply permission filtering (if needed)
        # Could filter to only projects user has access to
        
        return query.offset(skip).limit(limit).all()
    
    async def update_project(
        self,
        project_id: str,
        org_id: str,
        user_id: str,
        data: ProjectUpdate
    ) -> Project:
        """Update project.
        
        Args:
            project_id: Project ID
            org_id: Organization ID
            user_id: User making update
            data: Update data
            
        Returns:
            Updated project
            
        Raises:
            ResourceNotFoundError: Project not found
            PermissionDeniedError: User lacks permission
        """
        project = await self.get_project(project_id, org_id, user_id)
        
        # Check update permission
        if not await self.permission_service.can_edit_project(user_id, project_id):
            raise PermissionDeniedError("Cannot edit this project")
        
        # Update fields
        for field, value in data.dict(exclude_unset=True).items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Project updated: {project_id}")
        return project
    
    async def delete_project(
        self,
        project_id: str,
        org_id: str,
        user_id: str
    ) -> None:
        """Delete project.
        
        Args:
            project_id: Project ID
            org_id: Organization ID
            user_id: User deleting
            
        Raises:
            ResourceNotFoundError: Project not found
            PermissionDeniedError: User lacks permission
        """
        project = await self.get_project(project_id, org_id, user_id)
        
        if not await self.permission_service.can_delete_project(user_id, project_id):
            raise PermissionDeniedError("Cannot delete this project")
        
        self.db.delete(project)
        self.db.commit()
        
        logger.info(f"Project deleted: {project_id}")
```

---

## Dependency Injection Pattern

### Service Factory

```python
# src/foundry/services/factories.py
"""Service factory for dependency injection."""

from sqlalchemy.orm import Session
from src.foundry.services.platform import (
    OrganizationService,
    UserService,
    AuthService
)
from src.foundry.services.delivery import (
    ProjectService,
    AssetService,
    ReviewService
)
from src.foundry.services.celonis import (
    TenantExtractionService,
    SnapshotService
)


class ServiceFactory:
    """Factory for creating service instances with DI."""
    
    def __init__(self, db: Session):
        self.db = db
        self._services = {}
    
    def get_organization_service(self) -> OrganizationService:
        """Get or create organization service."""
        if 'organization' not in self._services:
            self._services['organization'] = OrganizationService(self.db)
        return self._services['organization']
    
    def get_project_service(self) -> ProjectService:
        """Get or create project service."""
        if 'project' not in self._services:
            permission_service = self.get_permission_service()
            self._services['project'] = ProjectService(
                self.db,
                permission_service
            )
        return self._services['project']
    
    def get_permission_service(self):
        """Get permission service."""
        if 'permission' not in self._services:
            from src.foundry.services.platform import PermissionService
            self._services['permission'] = PermissionService(self.db)
        return self._services['permission']
    
    # ... more services ...
```

### Usage in Routes

```python
# src/foundry/api/routes/ui/projects.py
from fastapi import APIRouter, Depends, Request
from src.foundry.services.factories import ServiceFactory

router = APIRouter(prefix="/ui/projects", tags=["ui_projects"])


def get_service_factory(db = Depends(get_db)) -> ServiceFactory:
    """Get service factory."""
    return ServiceFactory(db)


@router.get("/")
async def list_projects(
    request: Request,
    current_user = Depends(get_current_user),
    services = Depends(get_service_factory)
):
    """List projects for organization."""
    org_id = request.org_id  # From multi-tenancy middleware
    
    project_service = services.get_project_service()
    projects = await project_service.list_projects(org_id, current_user.id)
    
    return render_template("projects/list.html", projects=projects)
```

---

## Error Handling Standardization

### Domain-Specific Error Classes

```python
# src/foundry/services/shared/error_handling.py
"""Standard error classes for services."""


class DomainError(Exception):
    """Base class for domain errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self):
        """Convert to dict for API response."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(DomainError):
    """Validation failed."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR", details={"field": field}, **kwargs)


class ResourceNotFoundError(DomainError):
    """Resource not found."""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"{resource_type} {resource_id} not found"
        super().__init__(message, code="NOT_FOUND", **kwargs)


class PermissionDeniedError(DomainError):
    """User lacks permission."""
    
    def __init__(self, action: str = None, resource: str = None, **kwargs):
        message = f"Permission denied"
        if action and resource:
            message += f" to {action} {resource}"
        super().__init__(message, code="PERMISSION_DENIED", **kwargs)


class ConflictError(DomainError):
    """Resource conflict (e.g., duplicate name)."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="CONFLICT", **kwargs)


class ExternalServiceError(DomainError):
    """External service integration failed."""
    
    def __init__(self, service: str, message: str, **kwargs):
        full_message = f"{service} error: {message}"
        super().__init__(full_message, code="EXTERNAL_SERVICE_ERROR", **kwargs)
```

### Exception Handlers in Routes

```python
# src/foundry/api/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from src.foundry.services.shared.error_handling import DomainError

app = FastAPI()


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """Handle domain errors."""
    status_code = 400
    
    if exc.code == "NOT_FOUND":
        status_code = 404
    elif exc.code == "PERMISSION_DENIED":
        status_code = 403
    elif exc.code == "CONFLICT":
        status_code = 409
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )
```

---

## Migration Plan

### Week 1: Planning & Structure

- [ ] Review all 25 service modules
- [ ] Map service responsibilities
- [ ] Identify dependencies and circular refs
- [ ] Create new directory structure
- [ ] Create service factory skeleton

### Week 2: Extract Platform Services

- [ ] Move auth.py → platform/auth.py
- [ ] Move organization.py → platform/organization.py
- [ ] Move user.py → platform/user.py
- [ ] Create platform/__init__.py exports
- [ ] Update imports in tests

### Week 2-3: Extract Delivery Services

- [ ] Move project.py → delivery/project.py
- [ ] Move asset.py → delivery/asset.py
- [ ] Move review.py → delivery/review.py
- [ ] Move deployment.py → delivery/deployment.py
- [ ] Create delivery/__init__.py exports
- [ ] Update imports in tests

### Week 3: Extract Celonis Services

- [ ] Create celonis/ directory
- [ ] Move celonis_service.py → celonis/tenant_extraction.py
- [ ] Move snapshot.py → celonis/snapshot.py
- [ ] Move kpi.py → celonis/kpi.py
- [ ] Move celonis_data_agent.py → celonis/data_agent.py
- [ ] Move celonis_contracts.py → celonis/contracts.py
- [ ] Create celonis/__init__.py exports

### Week 3: Extract Shared Services

- [ ] Move error_handler.py → shared/error_handling.py
- [ ] Move observability.py → shared/observability.py
- [ ] Move cache.py → shared/cache.py
- [ ] Move database.py → shared/database.py
- [ ] Create shared/__init__.py exports

### Week 4: Update All Imports

- [ ] Find all service imports across codebase
- [ ] Update to new module paths
- [ ] Run linter to find missed imports
- [ ] Update API route files
- [ ] Update test imports

### Week 4: Test & Verify

- [ ] Run full test suite
- [ ] Check for import errors
- [ ] Verify service initialization
- [ ] Test API endpoints
- [ ] Performance check (startup time)

---

## Testing Strategy

### Unit Tests Per Service

```python
# tests/unit/services/delivery/test_project_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.orm import Session

from src.foundry.services.delivery import ProjectService
from src.foundry.services.platform import PermissionService
from src.foundry.models import Project, Organization
from src.foundry.services.shared.error_handling import (
    PermissionDeniedError,
    ResourceNotFoundError
)


@pytest.fixture
def db_session():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def permission_service():
    """Mock permission service."""
    return Mock(spec=PermissionService)


@pytest.fixture
def project_service(db_session, permission_service):
    """Project service instance."""
    return ProjectService(db_session, permission_service)


@pytest.mark.asyncio
async def test_create_project_success(project_service, db_session, permission_service):
    """Test successful project creation."""
    # Setup
    permission_service.can_create_project = AsyncMock(return_value=True)
    
    org = Organization(id="org-1", name="Test Org")
    db_session.query().filter_by().first.return_value = org
    
    # Execute
    result = await project_service.create_project(
        org_id="org-1",
        user_id="user-1",
        data=ProjectCreate(name="Test Project")
    )
    
    # Assert
    assert result.name == "Test Project"
    assert result.organization_id == "org-1"
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_project_no_permission(project_service, permission_service):
    """Test project creation without permission."""
    permission_service.can_create_project = AsyncMock(return_value=False)
    
    with pytest.raises(PermissionDeniedError):
        await project_service.create_project(
            org_id="org-1",
            user_id="user-1",
            data=ProjectCreate(name="Test")
        )


@pytest.mark.asyncio
async def test_get_project_not_found(project_service, db_session):
    """Test getting non-existent project."""
    db_session.query().filter_by().first.return_value = None
    
    with pytest.raises(ResourceNotFoundError):
        await project_service.get_project(
            project_id="proj-999",
            org_id="org-1",
            user_id="user-1"
        )
```

---

## Success Criteria

✅ Complete when:

1. All 25 services reorganized into 6 domains
2. All imports updated across codebase
3. Service factory working for DI
4. Error handling standardized
5. All tests passing
6. Documentation updated
7. No circular dependencies
8. Startup time unchanged/improved

---

## Benefits

### Development
- ✅ Easier to find related code
- ✅ Clearer service responsibilities
- ✅ Better for onboarding
- ✅ Faster code reviews

### Maintainability
- ✅ Easier to modify services
- ✅ Easier to add new features
- ✅ Better isolation for testing
- ✅ Fewer merge conflicts

### Architecture
- ✅ Clear domain boundaries
- ✅ Foundation for submodule extraction
- ✅ Better dependency management
- ✅ Scalable for future growth

---

**Timeline:** Week 2-4 of refactoring plan  
**Priority:** High (foundation for future extraction)  
**Ownership:** Architecture Lead + Team  
**Dependencies:** Phase 1 contracts must be defined

