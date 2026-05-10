from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["ui"])


@router.get("/docu/user.html")
def docu_user(request: Request):
    return RedirectResponse(url="/docs-site/user/", status_code=307)


@router.get("/docu/developer.html")
def docu_developer(request: Request):
    return RedirectResponse(url="/docs-site/developer/", status_code=307)


@router.get("/docu/guide-admin-setup.html")
def docu_guide_admin_setup(request: Request):
    return RedirectResponse(url="/docs-site/admin/full-setup/", status_code=307)


@router.get("/docu/guide-account-flows.html")
def docu_guide_account_flows(request: Request):
    return RedirectResponse(url="/docs-site/guides/account-flows/", status_code=307)


@router.get("/docu/guide-delivery-walkthrough.html")
def docu_guide_delivery_walkthrough(request: Request):
    return RedirectResponse(url="/docs-site/guides/delivery-walkthrough/", status_code=307)


@router.get("/docu/guide-action-flow-templates.html")
def docu_guide_action_flow_templates(request: Request):
    return RedirectResponse(url="/docs-site/guides/action-flow-template-catalog/", status_code=307)
