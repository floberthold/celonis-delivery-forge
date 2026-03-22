# ruff: noqa: E402

import os
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select

# Ensure this test uses an isolated SQLite database.
os.environ["FORGE_DATABASE_URL"] = "sqlite:///./tmp_quests_api_test.db"

import foundry.db as db_module

db_module._set_engine(os.environ["FORGE_DATABASE_URL"])

from foundry.api.main import app
from foundry.models import (
    ActivityLog,
    Client,
    EntityType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    Person,
    Project,
    Quest,
    QuestPriority,
    QuestSource,
    QuestStatus,
)
from foundry.security import create_access_token, hash_password

engine = db_module.engine


DB_FILE = Path("tmp_quests_api_test.db")


def _reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _seed_org_fixture() -> tuple[UUID, UUID, UUID, UUID]:
    with Session(engine) as session:
        person = Person(
            email="quest-tester@example.com",
            name="Quest Tester",
            hashed_password=hash_password("secret"),
        )
        session.add(person)
        session.commit()
        session.refresh(person)

        organization = Organization(name="Quest Test Org", slug="quest-test-org")
        session.add(organization)
        session.commit()
        session.refresh(organization)

        membership = OrganizationMembership(
            organization_id=organization.id,
            person_id=person.id,
            role=OrganizationRole.owner,
        )
        session.add(membership)
        session.commit()

        client = Client(
            organization_id=organization.id,
            name="Quest Test Client",
            tenant_url="https://quest-test.celonis.cloud",
        )
        session.add(client)
        session.commit()
        session.refresh(client)

        project = Project(
            organization_id=organization.id,
            name="Quest Test Project",
            client_id=client.id,
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        return person.id, organization.id, client.id, project.id


def test_quest_lifecycle_and_activity_logging() -> None:
    _reset_db()

    person_id, organization_id, client_id, project_id = _seed_org_fixture()
    auth_token = create_access_token(str(person_id), organization_id=str(organization_id))

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_response = api_client.post(
            "/quests/",
            json={
                "title": "Initial Quest",
                "description": "Initial description",
                "source": "user_authored",
                "priority": "medium",
                "status": "suggested",
                    "project_id": str(project_id),
                    "client_id": str(client_id),
            },
        )
        assert create_response.status_code == 200, create_response.text
        quest_id = create_response.json()["id"]
        quest_uuid = UUID(quest_id)

        update_response = api_client.patch(
            f"/quests/{quest_id}",
            json={
                "title": "Updated Quest",
                "status": "active",
                "priority": "high",
            },
        )
        assert update_response.status_code == 200, update_response.text

        pause_response = api_client.post(f"/quests/{quest_id}/pause")
        assert pause_response.status_code == 200, pause_response.text
        assert pause_response.json()["status"] == "blocked"

        reprioritize_response = api_client.post(
            f"/quests/{quest_id}/reprioritize",
            json={"priority": "critical"},
        )
        assert reprioritize_response.status_code == 200, reprioritize_response.text
        assert reprioritize_response.json()["priority"] == "critical"

        replace_response = api_client.post(
            f"/quests/{quest_id}/replace",
            json={
                "title": "Replacement Quest",
                "description": "Replacement desc",
                "priority": "high",
            },
        )
        assert replace_response.status_code == 200, replace_response.text
        replacement_id = replace_response.json()["id"]
        replacement_uuid = UUID(replacement_id)
        assert replacement_id != quest_id

        objective_response = api_client.post(
            f"/quests/{quest_id}/objectives",
            json={"title": "Prepare data model", "details": "Define baseline objective"},
        )
        assert objective_response.status_code == 200, objective_response.text
        objective_id = objective_response.json()["id"]

        objective_update_response = api_client.patch(
            f"/quests/{quest_id}/objectives/{objective_id}",
            json={"is_done": True},
        )
        assert objective_update_response.status_code == 200, objective_update_response.text
        assert objective_update_response.json()["is_done"] is True

        assignment_response = api_client.post(
            f"/quests/{quest_id}/assignments",
            json={
                "assignee_person_id": str(person_id),
                "role": "lead",
                "state": "assigned",
            },
        )
        assert assignment_response.status_code == 200, assignment_response.text
        assignment_id = assignment_response.json()["id"]

        assignment_update_response = api_client.patch(
            f"/quests/{quest_id}/assignments/{assignment_id}",
            json={"state": "in_progress"},
        )
        assert assignment_update_response.status_code == 200, assignment_update_response.text
        assert assignment_update_response.json()["state"] == "in_progress"

        assignment_delete_response = api_client.delete(
            f"/quests/{quest_id}/assignments/{assignment_id}"
        )
        assert assignment_delete_response.status_code == 200, assignment_delete_response.text

        objective_delete_response = api_client.delete(
            f"/quests/{quest_id}/objectives/{objective_id}"
        )
        assert objective_delete_response.status_code == 200, objective_delete_response.text

        feedback_response = api_client.post(
            f"/quests/{replacement_id}/feedback",
            json={
                "feedback_type": "accepted",
                "note": "Looks good",
                "metadata_json": {"origin": "test"},
            },
        )
        assert feedback_response.status_code == 200, feedback_response.text

        delete_response = api_client.delete(f"/quests/{replacement_id}")
        assert delete_response.status_code == 200, delete_response.text
        assert delete_response.json()["deleted"] is True

    with Session(engine) as session:
        original = session.get(Quest, quest_uuid)
        assert original is not None
        assert original.status == QuestStatus.archived

        replacement = session.get(Quest, replacement_uuid)
        assert replacement is None

        activity_rows = list(
            session.exec(
                select(ActivityLog).where(
                    ActivityLog.entity_type == EntityType.quest,
                    ActivityLog.organization_id == organization_id,
                )
            ).all()
        )
        actions = {row.action for row in activity_rows}
        assert "quest.created" in actions
        assert "quest.updated" in actions
        assert "quest.paused" in actions
        assert "quest.reprioritized" in actions
        assert "quest.replaced" in actions
        assert "quest.feedback_added" in actions
        assert "quest.deleted" in actions
        assert "quest.objective_added" in actions
        assert "quest.objective_updated" in actions
        assert "quest.objective_deleted" in actions
        assert "quest.assignment_added" in actions
        assert "quest.assignment_updated" in actions
        assert "quest.assignment_deleted" in actions


def test_quest_list_filters() -> None:
    _reset_db()

    person_id, organization_id, client_id, project_id = _seed_org_fixture()
    auth_token = create_access_token(str(person_id), organization_id=str(organization_id))

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        payloads = [
            {
                "title": "Suggested Quest",
                "source": QuestSource.user_authored.value,
                "status": QuestStatus.suggested.value,
                "priority": QuestPriority.medium.value,
                "project_id": str(project_id),
                "client_id": str(client_id),
            },
            {
                "title": "Blocked Quest",
                "source": QuestSource.agent_suggested.value,
                "status": QuestStatus.blocked.value,
                "priority": QuestPriority.high.value,
                "project_id": str(project_id),
                "client_id": str(client_id),
            },
        ]

        for payload in payloads:
            response = api_client.post("/quests/", json=payload)
            assert response.status_code == 200, response.text

        blocked_response = api_client.get("/quests/", params={"status": "blocked"})
        assert blocked_response.status_code == 200
        blocked_rows = blocked_response.json()
        assert len(blocked_rows) == 1
        assert blocked_rows[0]["title"] == "Blocked Quest"

        project_response = api_client.get("/quests/", params={"project_id": str(project_id)})
        assert project_response.status_code == 200
        assert len(project_response.json()) == 2


def test_archived_quest_cannot_transition_back_to_active() -> None:
    _reset_db()

    person_id, organization_id, client_id, project_id = _seed_org_fixture()
    auth_token = create_access_token(str(person_id), organization_id=str(organization_id))

    with TestClient(app) as api_client:
        api_client.cookies.set("foundry_access_token", auth_token)

        create_response = api_client.post(
            "/quests/",
            json={
                "title": "Archive Me",
                "source": "user_authored",
                "status": "suggested",
                "priority": "medium",
                "project_id": str(project_id),
                "client_id": str(client_id),
            },
        )
        assert create_response.status_code == 200, create_response.text
        quest_id = create_response.json()["id"]

        replace_response = api_client.post(
            f"/quests/{quest_id}/replace",
            json={
                "title": "Replacement Quest",
                "description": "replacement",
                "priority": "high",
            },
        )
        assert replace_response.status_code == 200, replace_response.text

        invalid_update_response = api_client.patch(
            f"/quests/{quest_id}",
            json={"status": "active"},
        )
        assert invalid_update_response.status_code == 400, invalid_update_response.text
        assert "Invalid quest status transition" in invalid_update_response.json()["detail"]


if DB_FILE.exists():
    try:
        DB_FILE.unlink()
    except PermissionError:
        pass
