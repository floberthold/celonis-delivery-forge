from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session, select

from foundry.api.deps import get_current_person
from foundry.db import get_session
from foundry.models import EntityType, GlobalRole, Organization, OrganizationMembership, OrganizationRole, Person
from foundry.security import hash_password
from foundry.services.activity_log import log_created, log_updated
from .shared import redirect_dashboard as _redirect_dashboard
from .shared import redirect_ui as _redirect_ui

router = APIRouter(tags=["ui"])


def _enum_or_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    return str(value)


def _is_global_admin(person: Person | None) -> bool:
    return bool(person and person.role_global == GlobalRole.admin)


def _parse_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except Exception as exc:
        raise ValueError(f"Invalid {field_name}") from exc


def _get_org_membership(
    session: Session,
    person_id: UUID,
    organization_id: UUID,
) -> OrganizationMembership | None:
    return session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.person_id == person_id,
            OrganizationMembership.organization_id == organization_id,
        )
    ).first()


@router.get("/foundry-admin-ui", include_in_schema=False)
def foundry_admin_ui(
    request: Request,
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_dashboard(err="Global admin access required")

    from . import _build_foundry_admin_context, _build_foundry_admin_user_context, templates

    context = _build_foundry_admin_context(session)
    user_context = _build_foundry_admin_user_context(session)
    return templates.TemplateResponse(request, "foundry_admin.html",
        {
            "request": request,
            "ok_message": request.query_params.get("ok"),
            "error_message": request.query_params.get("err"),
            "rows": context["rows"],
            "totals": context["totals"],
            "user_rows": user_context["user_rows"],
            "org_options": user_context["org_options"],
            "global_role_options": user_context["global_role_options"],
            "org_role_options": user_context["org_role_options"],
        },
    )


@router.post("/foundry-admin-ui/users/create", include_in_schema=False)
def foundry_admin_create_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role_global: str = Form("member"),
    organization_id: str = Form(""),
    org_role: str = Form("member"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_ui("/foundry-admin-ui", err="Global admin access required")

    from . import _validate_registration_password

    try:
        normalized_name = name.strip()
        normalized_email = email.strip().lower()
        if not normalized_name:
            return _redirect_ui("/foundry-admin-ui", err="Name is required")
        if not normalized_email:
            return _redirect_ui("/foundry-admin-ui", err="Email is required")

        _validate_registration_password(password, confirm_password)

        existing = session.exec(select(Person).where(Person.email == normalized_email)).first()
        if existing is not None:
            return _redirect_ui("/foundry-admin-ui", err="Email already exists")

        person = Person(
            name=normalized_name,
            email=normalized_email,
            hashed_password=hash_password(password),
            role_global=GlobalRole(role_global),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        linked_org_id: UUID | None = None
        if organization_id.strip():
            parsed_org_id = _parse_uuid(organization_id, "organization_id")
            organization = session.get(Organization, parsed_org_id)
            if organization is None:
                return _redirect_ui("/foundry-admin-ui", err="Organization not found")
            membership = OrganizationMembership(
                organization_id=organization.id,
                person_id=person.id,
                role=OrganizationRole(org_role),
            )
            session.add(membership)
            session.commit()
            linked_org_id = organization.id

        log_created(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_person.id,
            organization_id=linked_org_id,
            metadata={
                "email": person.email,
                "role_global": _enum_or_value(person.role_global, "member"),
            },
        )
        return _redirect_ui("/foundry-admin-ui", ok=f"Created user '{person.email}'")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/foundry-admin-ui", err=f"Create user failed: {exc}")


@router.post("/foundry-admin-ui/users/update", include_in_schema=False)
def foundry_admin_update_user(
    person_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role_global: str = Form(...),
    password: str = Form(""),
    confirm_password: str = Form(""),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_ui("/foundry-admin-ui", err="Global admin access required")

    from . import _validate_registration_password

    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        person = session.get(Person, parsed_person_id)
        if person is None:
            return _redirect_ui("/foundry-admin-ui", err="User not found")

        normalized_name = name.strip()
        normalized_email = email.strip().lower()
        if not normalized_name:
            return _redirect_ui("/foundry-admin-ui", err="Name is required")
        if not normalized_email:
            return _redirect_ui("/foundry-admin-ui", err="Email is required")

        existing = session.exec(select(Person).where(Person.email == normalized_email)).first()
        if existing and existing.id != person.id:
            return _redirect_ui("/foundry-admin-ui", err="Email already exists")

        person.name = normalized_name
        person.email = normalized_email
        person.role_global = GlobalRole(role_global)

        has_password_input = bool(password.strip() or confirm_password.strip())
        if has_password_input:
            _validate_registration_password(password, confirm_password)
            person.hashed_password = hash_password(password)

        session.add(person)
        session.commit()
        session.refresh(person)

        log_updated(
            session,
            entity_type=EntityType.person,
            entity_id=person.id,
            actor_id=current_person.id,
            metadata={
                "email": person.email,
                "role_global": _enum_or_value(person.role_global, "member"),
                "password_updated": has_password_input,
            },
        )
        return _redirect_ui("/foundry-admin-ui", ok=f"Updated user '{person.email}'")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/foundry-admin-ui", err=f"Update user failed: {exc}")


@router.post("/foundry-admin-ui/memberships/create", include_in_schema=False)
def foundry_admin_create_membership(
    person_id: str = Form(...),
    organization_id: str = Form(...),
    role: str = Form("member"),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_ui("/foundry-admin-ui", err="Global admin access required")

    try:
        parsed_person_id = _parse_uuid(person_id, "person_id")
        parsed_org_id = _parse_uuid(organization_id, "organization_id")
        person = session.get(Person, parsed_person_id)
        organization = session.get(Organization, parsed_org_id)
        if person is None:
            return _redirect_ui("/foundry-admin-ui", err="User not found")
        if organization is None:
            return _redirect_ui("/foundry-admin-ui", err="Organization not found")

        existing = _get_org_membership(session, parsed_person_id, parsed_org_id)
        if existing is not None:
            return _redirect_ui("/foundry-admin-ui", err="Membership already exists")

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole(role),
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)

        log_created(
            session,
            entity_type=EntityType.membership,
            entity_id=membership.id,
            actor_id=current_person.id,
            organization_id=organization.id,
            metadata={"person_id": str(person.id), "role": _enum_or_value(membership.role, "member")},
        )
        return _redirect_ui("/foundry-admin-ui", ok="Organization membership added")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/foundry-admin-ui", err=f"Add membership failed: {exc}")


@router.post("/foundry-admin-ui/memberships/update", include_in_schema=False)
def foundry_admin_update_membership(
    membership_id: str = Form(...),
    role: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_ui("/foundry-admin-ui", err="Global admin access required")

    try:
        parsed_membership_id = _parse_uuid(membership_id, "membership_id")
        membership = session.get(OrganizationMembership, parsed_membership_id)
        if membership is None:
            return _redirect_ui("/foundry-admin-ui", err="Membership not found")

        membership.role = OrganizationRole(role)
        session.add(membership)
        session.commit()

        log_updated(
            session,
            entity_type=EntityType.membership,
            entity_id=membership.id,
            actor_id=current_person.id,
            organization_id=membership.organization_id,
            metadata={"role": _enum_or_value(membership.role, "member")},
        )
        return _redirect_ui("/foundry-admin-ui", ok="Organization membership updated")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/foundry-admin-ui", err=f"Update membership failed: {exc}")


@router.post("/foundry-admin-ui/memberships/delete", include_in_schema=False)
def foundry_admin_delete_membership(
    membership_id: str = Form(...),
    session: Session = Depends(get_session),
    current_person: Person = Depends(get_current_person),
):
    if not _is_global_admin(current_person):
        return _redirect_ui("/foundry-admin-ui", err="Global admin access required")

    try:
        parsed_membership_id = _parse_uuid(membership_id, "membership_id")
        membership = session.get(OrganizationMembership, parsed_membership_id)
        if membership is None:
            return _redirect_ui("/foundry-admin-ui", err="Membership not found")

        if membership.role in {OrganizationRole.owner, OrganizationRole.admin}:
            remaining_privileged = session.exec(
                select(OrganizationMembership)
                .where(
                    OrganizationMembership.organization_id == membership.organization_id,
                    OrganizationMembership.id != membership.id,
                    OrganizationMembership.role.in_([OrganizationRole.owner, OrganizationRole.admin]),
                )
            ).first()
            if remaining_privileged is None:
                return _redirect_ui(
                    "/foundry-admin-ui",
                    err="Cannot remove the last owner/admin from an organization",
                )

        session.delete(membership)
        session.commit()
        return _redirect_ui("/foundry-admin-ui", ok="Organization membership removed")
    except Exception as exc:
        session.rollback()
        return _redirect_ui("/foundry-admin-ui", err=f"Delete membership failed: {exc}")

