from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlmodel import Session, select

from foundry.models import (
    CelonisSnapshot,
    CelonisConnection,
    Client,
    SnapshotApp,
    SnapshotDataModel,
    SnapshotDataPool,
    SnapshotJob,
    SnapshotKnowledgeModel,
    SnapshotPackage,
    SnapshotPackageDefinition,
    SnapshotRunStatus,
    SnapshotSpace,
    SnapshotTask,
    SnapshotTaskDetail,
    SnapshotTransformation,
)


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _jsonl_dump(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str))
            f.write("\n")


def _slugify(value: str) -> str:
    cleaned: list[str] = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "snapshot"


def _normalize_base_url(value: str) -> str:
    candidate = (value or "").strip()
    if not candidate:
        return ""
    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate
    return f"https://{candidate}"


def _tenant_slug(value: str) -> str:
    normalized = _normalize_base_url(value)
    if not normalized:
        return "tenant"
    parsed = urlparse(normalized)
    return _slugify(parsed.netloc or parsed.path or normalized)


def _asset_stem(name: str, asset_id: str) -> str:
    return f"{_slugify(name)}--{asset_id}"


def _write_asset_payload(base_dir: Path, stem: str, payload: dict[str, Any], raw_json: dict[str, Any]) -> None:
    _json_dump(base_dir / f"{stem}.json", payload)
    _json_dump(base_dir / f"{stem}.raw.json", raw_json)


def _snapshot_counts(
    *,
    space_rows: Sequence[SnapshotSpace],
    package_rows: Sequence[SnapshotPackage],
    package_definition_rows: Sequence[SnapshotPackageDefinition],
    task_rows: Sequence[SnapshotTask],
    task_detail_rows: Sequence[SnapshotTaskDetail],
    data_model_rows: Sequence[SnapshotDataModel],
    job_rows: Sequence[SnapshotJob],
    km_rows: Sequence[SnapshotKnowledgeModel],
    app_rows: Sequence[SnapshotApp],
    pool_rows: Sequence[SnapshotDataPool],
    transformation_rows: Sequence[SnapshotTransformation],
) -> dict[str, int]:
    return {
        "spaces": len(space_rows),
        "packages": len(package_rows),
        "package_definitions": len(package_definition_rows),
        "tasks": len(task_rows),
        "task_details": len(task_detail_rows),
        "data_models": len(data_model_rows),
        "jobs": len(job_rows),
        "knowledge_models": len(km_rows),
        "apps": len(app_rows),
        "data_pools": len(pool_rows),
        "transformations": len(transformation_rows),
    }


def _build_snapshot_mirror(
    session: Session,
    *,
    mirror_root: Path,
    snapshot: CelonisSnapshot,
    space_rows: Sequence[SnapshotSpace],
    package_rows: Sequence[SnapshotPackage],
    package_definition_rows: Sequence[SnapshotPackageDefinition],
    task_rows: Sequence[SnapshotTask],
    task_detail_rows: Sequence[SnapshotTaskDetail],
    data_model_rows: Sequence[SnapshotDataModel],
    job_rows: Sequence[SnapshotJob],
    km_rows: Sequence[SnapshotKnowledgeModel],
    app_rows: Sequence[SnapshotApp],
    pool_rows: Sequence[SnapshotDataPool],
    transformation_rows: Sequence[SnapshotTransformation],
    delta_report: dict[str, Any],
) -> Path:
    client = session.get(Client, snapshot.client_id)
    connection = session.exec(
        select(CelonisConnection).where(
            CelonisConnection.client_id == snapshot.client_id,
            CelonisConnection.is_active == True,  # noqa: E712
        )
    ).first()

    client_label = client.name if client else str(snapshot.client_id)
    tenant_source = ""
    if connection is not None:
        tenant_source = connection.tenant_base_url
    elif client is not None:
        tenant_source = client.tenant_url

    tenant_dir = mirror_root / _slugify(client_label) / _tenant_slug(tenant_source)
    studio_dir = tenant_dir / "Studio"
    apps_dir = tenant_dir / "Apps"
    data_integration_dir = tenant_dir / "Data Integration"
    knowledge_models_dir = tenant_dir / "Knowledge Models"
    (studio_dir / "Spaces").mkdir(parents=True, exist_ok=True)
    (studio_dir / "Packages").mkdir(parents=True, exist_ok=True)
    (apps_dir / "Published").mkdir(parents=True, exist_ok=True)
    (data_integration_dir / "Data Pools").mkdir(parents=True, exist_ok=True)
    (data_integration_dir / "Data Models").mkdir(parents=True, exist_ok=True)
    (knowledge_models_dir / "Items").mkdir(parents=True, exist_ok=True)

    counts = _snapshot_counts(
        space_rows=space_rows,
        package_rows=package_rows,
        package_definition_rows=package_definition_rows,
        task_rows=task_rows,
        task_detail_rows=task_detail_rows,
        data_model_rows=data_model_rows,
        job_rows=job_rows,
        km_rows=km_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
    )
    _json_dump(
        tenant_dir / "tenant-manifest.json",
        {
            "snapshot_id": str(snapshot.id),
            "client_id": str(snapshot.client_id),
            "client_name": client_label,
            "tenant_url": tenant_source,
            "generated_at": datetime.utcnow().isoformat(),
            "counts": counts,
            "delta_counts": {
                asset_name: payload["counts"]
                for asset_name, payload in delta_report["assets"].items()
            },
        },
    )

    space_dir_map: dict[str, Path] = {}
    for row in space_rows:
        stem = _asset_stem(row.name, row.space_id)
        base_dir = studio_dir / "Spaces" / stem
        space_dir_map[row.space_id] = base_dir
        _write_asset_payload(
            base_dir,
            "space",
            {
                "kind": "space",
                "space_id": row.space_id,
                "name": row.name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    package_dir_map: dict[str, Path] = {}
    for row in package_rows:
        stem = _asset_stem(row.name, row.package_id)
        parent_dir = space_dir_map.get(row.space_id or "")
        if parent_dir is None:
            parent_dir = studio_dir / "Packages" / "unassigned"
        package_dir = parent_dir / "Packages" / stem
        package_dir_map[row.package_id] = package_dir
        _write_asset_payload(
            package_dir,
            "package",
            {
                "kind": "package",
                "package_id": row.package_id,
                "package_key": row.key,
                "name": row.name,
                "space_id": row.space_id,
                "space_name": row.space_name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    for row in task_rows:
        stem = _asset_stem(row.name, row.task_id)
        task_type_slug = _slugify(row.task_type or "unknown")
        base_dir = package_dir_map.get(row.package_id or "")
        if base_dir is None:
            base_dir = studio_dir / "Packages" / "unassigned"
        asset_dir = base_dir / "Assets" / task_type_slug
        _write_asset_payload(
            asset_dir,
            stem,
            {
                "kind": "task",
                "task_id": row.task_id,
                "name": row.name,
                "task_type": row.task_type,
                "package_id": row.package_id,
                "description": row.description,
                "pql_formula": row.pql_formula,
                "change_type": row.change_type.value,
                "content_hash": row.content_hash,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    for row in package_definition_rows:
        package_dir = package_dir_map.get(row.package_id)
        if package_dir is None:
            package_dir = studio_dir / "Packages" / "unassigned"
        definition_dir = package_dir / "Definitions"
        definition_name = row.definition_id or "studio.config.yaml"
        definition_path = definition_dir / definition_name
        definition_path.parent.mkdir(parents=True, exist_ok=True)
        definition_path.write_text(row.raw_yaml or "", encoding="utf-8")
        _json_dump(
            definition_dir / f"{definition_name}.parsed.json",
            {
                "kind": "package_definition",
                "definition_id": definition_name,
                "package_id": row.package_id,
                "package_key": row.package_key,
                "source_endpoint": row.source_endpoint,
                "parse_error": row.parse_error,
                "change_type": row.change_type.value,
                "content_hash": row.content_hash,
                "snapshot_id": str(snapshot.id),
                "parsed_json": row.parsed_json,
            },
        )

    task_detail_map: dict[str, SnapshotTaskDetail] = {}
    for row in task_detail_rows:
        task_detail_map[row.task_id] = row

    for row in task_rows:
        detail = task_detail_map.get(row.task_id)
        if detail is None:
            continue
        task_type_slug = _slugify(row.task_type or "unknown")
        base_dir = package_dir_map.get(row.package_id or "")
        if base_dir is None:
            base_dir = studio_dir / "Packages" / "unassigned"
        detail_dir = base_dir / "Assets" / task_type_slug / "Details"
        stem = _asset_stem(row.name, row.task_id)
        _json_dump(
            detail_dir / f"{stem}.detail.json",
            {
                "kind": "task_detail",
                "task_id": row.task_id,
                "task_type": row.task_type,
                "package_id": row.package_id,
                "source_endpoint": detail.source_endpoint,
                "error_message": detail.error_message,
                "detail": detail.detail_json,
                "references": detail.references_json,
                "dependencies": detail.dependencies_json,
                "snapshot_id": str(snapshot.id),
            },
        )

    _json_dump(
        data_integration_dir / "data-integration-manifest.json",
        {
            "snapshot_id": str(snapshot.id),
            "data_pools": len(pool_rows),
            "jobs": len(job_rows),
            "transformations": len(transformation_rows),
            "data_models": len(data_model_rows),
        },
    )
    pool_dir_map: dict[str, Path] = {}
    for row in pool_rows:
        stem = _asset_stem(row.name, row.pool_id)
        pool_dir = data_integration_dir / "Data Pools" / stem
        pool_dir_map[row.pool_id] = pool_dir
        _write_asset_payload(
            pool_dir,
            "pool",
            {
                "kind": "data_pool",
                "pool_id": row.pool_id,
                "name": row.name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    for row in job_rows:
        stem = _asset_stem(row.name, row.job_id)
        base_dir = pool_dir_map.get(row.pool_id or "")
        if base_dir is None:
            base_dir = data_integration_dir / "Data Pools" / "unassigned"
        _write_asset_payload(
            base_dir / "Jobs",
            stem,
            {
                "kind": "job",
                "job_id": row.job_id,
                "name": row.name,
                "pool_id": row.pool_id,
                "pool_name": row.pool_name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    for row in transformation_rows:
        stem = _asset_stem(row.name, row.transformation_id)
        base_dir = pool_dir_map.get(row.pool_id or "")
        if base_dir is None:
            base_dir = data_integration_dir / "Data Pools" / "unassigned"
        _write_asset_payload(
            base_dir / "Transformations",
            stem,
            {
                "kind": "transformation",
                "transformation_id": row.transformation_id,
                "name": row.name,
                "pool_id": row.pool_id,
                "pool_name": row.pool_name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    for row in data_model_rows:
        stem = _asset_stem(row.name, row.data_model_id)
        _write_asset_payload(
            data_integration_dir / "Data Models",
            stem,
            {
                "kind": "data_model",
                "data_model_id": row.data_model_id,
                "name": row.name,
                "space_id": row.space_id,
                "space_name": row.space_name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    _json_dump(
        apps_dir / "apps-manifest.json",
        {
            "snapshot_id": str(snapshot.id),
            "apps": len(app_rows),
        },
    )
    for row in app_rows:
        stem = _asset_stem(row.name, row.app_id)
        _write_asset_payload(
            apps_dir / "Published",
            stem,
            {
                "kind": "app",
                "app_id": row.app_id,
                "name": row.name,
                "space_id": row.space_id,
                "space_name": row.space_name,
                "package_key": row.package_key,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    _json_dump(
        knowledge_models_dir / "knowledge-models-manifest.json",
        {
            "snapshot_id": str(snapshot.id),
            "knowledge_models": len(km_rows),
        },
    )
    for row in km_rows:
        stem = _asset_stem(row.name, row.km_id)
        _write_asset_payload(
            knowledge_models_dir / "Items",
            stem,
            {
                "kind": "knowledge_model",
                "knowledge_model_id": row.km_id,
                "name": row.name,
                "space_id": row.space_id,
                "space_name": row.space_name,
                "change_type": row.change_type.value,
                "snapshot_id": str(snapshot.id),
            },
            row.raw_json,
        )

    return tenant_dir


def _serialize_rows(rows: Sequence[object], fields: list[str]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        out.append({field: getattr(row, field) for field in fields})
    return out


def _hash_payload(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def _get_previous_snapshot(session: Session, snapshot: CelonisSnapshot) -> CelonisSnapshot | None:
    rows = session.exec(
        select(CelonisSnapshot).where(
            CelonisSnapshot.client_id == snapshot.client_id,
            CelonisSnapshot.status == SnapshotRunStatus.completed,
        )
    ).all()
    candidates = [row for row in rows if row.id != snapshot.id]
    if not candidates:
        return None
    ordered = sorted(candidates, key=lambda row: row.created_at or datetime.min, reverse=True)
    return ordered[0]


def _build_record_map(
    rows: Sequence[Any],
    *,
    id_attr: str,
    name_attr: str,
    hash_attr: str | None = None,
) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        record_id = str(getattr(row, id_attr, "") or "")
        if not record_id:
            continue
        if hash_attr:
            content_hash = str(getattr(row, hash_attr, "") or "")
        else:
            content_hash = _hash_payload(getattr(row, "raw_json", {}))
        out[record_id] = {
            "id": record_id,
            "name": str(getattr(row, name_attr, "") or record_id),
            "hash": content_hash,
        }
    return out


def _diff_maps(
    *,
    current_map: dict[str, dict[str, str]],
    previous_map: dict[str, dict[str, str]],
) -> dict[str, Any]:
    added: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    modified: list[dict[str, str]] = []
    unchanged: list[dict[str, str]] = []

    current_ids = set(current_map.keys())
    previous_ids = set(previous_map.keys())

    for record_id in sorted(current_ids - previous_ids):
        added.append(current_map[record_id])

    for record_id in sorted(previous_ids - current_ids):
        removed.append(previous_map[record_id])

    for record_id in sorted(current_ids & previous_ids):
        current_record = current_map[record_id]
        previous_record = previous_map[record_id]
        if current_record["hash"] != previous_record["hash"]:
            modified.append(current_record)
        else:
            unchanged.append(current_record)

    return {
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "unchanged": len(unchanged),
        },
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
    }


def _collect_refs(payload: Any, keys: set[str], *, max_depth: int = 7) -> set[str]:
    refs: set[str] = set()

    def _walk(node: Any, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_lower = str(key).lower()
                if key_lower in keys:
                    if isinstance(value, str) and value.strip():
                        refs.add(value.strip())
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and item.strip():
                                refs.add(item.strip())
                _walk(value, depth + 1)
        elif isinstance(node, list):
            for item in node:
                _walk(item, depth + 1)

    _walk(payload, 0)
    return refs


def _build_relationship_graph(
    package_rows: Sequence[SnapshotPackage],
    package_definition_rows: Sequence[SnapshotPackageDefinition],
    task_rows: Sequence[SnapshotTask],
    data_model_rows: Sequence[SnapshotDataModel],
    job_rows: Sequence[SnapshotJob],
    km_rows: Sequence[SnapshotKnowledgeModel],
    space_rows: Sequence[SnapshotSpace] = (),
    app_rows: Sequence[SnapshotApp] = (),
    pool_rows: Sequence[SnapshotDataPool] = (),
    transformation_rows: Sequence[SnapshotTransformation] = (),
) -> dict[str, list[dict[str, str]]]:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []

    package_ids = {row.package_id for row in package_rows}
    data_model_ids = {row.data_model_id for row in data_model_rows}
    km_ids = {row.km_id for row in km_rows}
    space_ids = {row.space_id for row in space_rows}
    pool_ids = {row.pool_id for row in pool_rows}

    for row in space_rows:
        nodes.append({"node_id": f"space:{row.space_id}", "kind": "space", "name": row.name})
    for row in package_rows:
        nodes.append({"node_id": f"package:{row.package_id}", "kind": "package", "name": row.name})
    for row in package_definition_rows:
        label = row.definition_id or "studio.config.yaml"
        nodes.append({"node_id": f"package_definition:{row.package_id}:{label}", "kind": "package_definition", "name": label})
    for row in task_rows:
        nodes.append({"node_id": f"task:{row.task_id}", "kind": "task", "name": row.name})
    for row in data_model_rows:
        nodes.append({"node_id": f"data_model:{row.data_model_id}", "kind": "data_model", "name": row.name})
    for row in job_rows:
        nodes.append({"node_id": f"job:{row.job_id}", "kind": "job", "name": row.name})
    for row in km_rows:
        nodes.append({"node_id": f"knowledge_model:{row.km_id}", "kind": "knowledge_model", "name": row.name})
    for row in app_rows:
        nodes.append({"node_id": f"app:{row.app_id}", "kind": "app", "name": row.name})
    for row in pool_rows:
        nodes.append({"node_id": f"pool:{row.pool_id}", "kind": "data_pool", "name": row.name})
    for row in transformation_rows:
        nodes.append({"node_id": f"transformation:{row.transformation_id}", "kind": "transformation", "name": row.name})

    # package → space
    for pkg in package_rows:
        if pkg.space_id and pkg.space_id in space_ids:
            edges.append({"from": f"space:{pkg.space_id}", "to": f"package:{pkg.package_id}", "type": "contains_package"})

    # task → package
    for task in task_rows:
        if task.package_id and task.package_id in package_ids:
            edges.append({"from": f"package:{task.package_id}", "to": f"task:{task.task_id}", "type": "contains_task"})

        dm_refs = _collect_refs(task.raw_json, {"datamodelid", "data_model_id"})
        for dm_id in sorted(dm_refs):
            if dm_id in data_model_ids:
                edges.append({"from": f"task:{task.task_id}", "to": f"data_model:{dm_id}", "type": "references_data_model"})

        km_refs = _collect_refs(task.raw_json, {"knowledgemodelid", "knowledge_model_id", "kmid"})
        for km_id in sorted(km_refs):
            if km_id in km_ids:
                edges.append({"from": f"task:{task.task_id}", "to": f"knowledge_model:{km_id}", "type": "references_knowledge_model"})

    for definition in package_definition_rows:
        definition_name = definition.definition_id or "studio.config.yaml"
        edges.append(
            {
                "from": f"package:{definition.package_id}",
                "to": f"package_definition:{definition.package_id}:{definition_name}",
                "type": "contains_definition",
            }
        )

    for job in job_rows:
        dm_refs = _collect_refs(job.raw_json, {"datamodelid", "data_model_id"})
        for dm_id in sorted(dm_refs):
            if dm_id in data_model_ids:
                edges.append({"from": f"job:{job.job_id}", "to": f"data_model:{dm_id}", "type": "uses_data_model"})
        if job.pool_id and job.pool_id in pool_ids:
            edges.append({"from": f"pool:{job.pool_id}", "to": f"job:{job.job_id}", "type": "contains_job"})

    for km in km_rows:
        dm_refs = _collect_refs(km.raw_json, {"datamodelid", "data_model_id"})
        for dm_id in sorted(dm_refs):
            if dm_id in data_model_ids:
                edges.append({"from": f"knowledge_model:{km.km_id}", "to": f"data_model:{dm_id}", "type": "models_on_data_model"})

    for app in app_rows:
        if app.space_id and app.space_id in space_ids:
            edges.append({"from": f"space:{app.space_id}", "to": f"app:{app.app_id}", "type": "contains_app"})
        if app.package_key and app.package_key in package_ids:
            edges.append({"from": f"package:{app.package_key}", "to": f"app:{app.app_id}", "type": "published_as_app"})

    for tf in transformation_rows:
        if tf.pool_id and tf.pool_id in pool_ids:
            edges.append({"from": f"pool:{tf.pool_id}", "to": f"transformation:{tf.transformation_id}", "type": "contains_transformation"})

    unique_edges: dict[tuple[str, str, str], dict[str, str]] = {}
    for edge in edges:
        unique_edges[(edge["from"], edge["to"], edge["type"])] = edge

    return {
        "nodes": sorted(nodes, key=lambda row: (row["kind"], row["node_id"])),
        "edges": sorted(unique_edges.values(), key=lambda row: (row["type"], row["from"], row["to"])),
    }


def _build_delta(
    *,
    current_snapshot: CelonisSnapshot,
    previous_snapshot: CelonisSnapshot | None,
    package_rows: Sequence[SnapshotPackage],
    package_definition_rows: Sequence[SnapshotPackageDefinition],
    task_rows: Sequence[SnapshotTask],
    data_model_rows: Sequence[SnapshotDataModel],
    job_rows: Sequence[SnapshotJob],
    km_rows: Sequence[SnapshotKnowledgeModel],
    space_rows: Sequence[SnapshotSpace] = (),
    app_rows: Sequence[SnapshotApp] = (),
    pool_rows: Sequence[SnapshotDataPool] = (),
    transformation_rows: Sequence[SnapshotTransformation] = (),
    prev_package_rows: Sequence[SnapshotPackage] = (),
    prev_package_definition_rows: Sequence[SnapshotPackageDefinition] = (),
    prev_task_rows: Sequence[SnapshotTask] = (),
    prev_data_model_rows: Sequence[SnapshotDataModel] = (),
    prev_job_rows: Sequence[SnapshotJob] = (),
    prev_km_rows: Sequence[SnapshotKnowledgeModel] = (),
    prev_space_rows: Sequence[SnapshotSpace] = (),
    prev_app_rows: Sequence[SnapshotApp] = (),
    prev_pool_rows: Sequence[SnapshotDataPool] = (),
    prev_transformation_rows: Sequence[SnapshotTransformation] = (),
) -> dict[str, Any]:
    package_diff = _diff_maps(
        current_map=_build_record_map(package_rows, id_attr="package_id", name_attr="name"),
        previous_map=_build_record_map(prev_package_rows, id_attr="package_id", name_attr="name"),
    )
    task_diff = _diff_maps(
        current_map=_build_record_map(task_rows, id_attr="task_id", name_attr="name", hash_attr="content_hash"),
        previous_map=_build_record_map(prev_task_rows, id_attr="task_id", name_attr="name", hash_attr="content_hash"),
    )
    package_definition_diff = _diff_maps(
        current_map=_build_record_map(
            package_definition_rows,
            id_attr="package_id",
            name_attr="definition_id",
            hash_attr="content_hash",
        ),
        previous_map=_build_record_map(
            prev_package_definition_rows,
            id_attr="package_id",
            name_attr="definition_id",
            hash_attr="content_hash",
        ),
    )
    data_model_diff = _diff_maps(
        current_map=_build_record_map(data_model_rows, id_attr="data_model_id", name_attr="name"),
        previous_map=_build_record_map(prev_data_model_rows, id_attr="data_model_id", name_attr="name"),
    )
    job_diff = _diff_maps(
        current_map=_build_record_map(job_rows, id_attr="job_id", name_attr="name"),
        previous_map=_build_record_map(prev_job_rows, id_attr="job_id", name_attr="name"),
    )
    km_diff = _diff_maps(
        current_map=_build_record_map(km_rows, id_attr="km_id", name_attr="name"),
        previous_map=_build_record_map(prev_km_rows, id_attr="km_id", name_attr="name"),
    )
    space_diff = _diff_maps(
        current_map=_build_record_map(space_rows, id_attr="space_id", name_attr="name"),
        previous_map=_build_record_map(prev_space_rows, id_attr="space_id", name_attr="name"),
    )
    app_diff = _diff_maps(
        current_map=_build_record_map(app_rows, id_attr="app_id", name_attr="name"),
        previous_map=_build_record_map(prev_app_rows, id_attr="app_id", name_attr="name"),
    )
    pool_diff = _diff_maps(
        current_map=_build_record_map(pool_rows, id_attr="pool_id", name_attr="name"),
        previous_map=_build_record_map(prev_pool_rows, id_attr="pool_id", name_attr="name"),
    )
    transformation_diff = _diff_maps(
        current_map=_build_record_map(transformation_rows, id_attr="transformation_id", name_attr="name"),
        previous_map=_build_record_map(prev_transformation_rows, id_attr="transformation_id", name_attr="name"),
    )

    return {
        "snapshot_id": str(current_snapshot.id),
        "previous_snapshot_id": str(previous_snapshot.id) if previous_snapshot else None,
        "computed_at": datetime.utcnow().isoformat(),
        "assets": {
            "spaces": space_diff,
            "packages": package_diff,
            "package_definitions": package_definition_diff,
            "tasks": task_diff,
            "data_models": data_model_diff,
            "jobs": job_diff,
            "knowledge_models": km_diff,
            "apps": app_diff,
            "data_pools": pool_diff,
            "transformations": transformation_diff,
        },
    }


def _append_replay_steps(
    steps: list[dict[str, Any]],
    *,
    asset_type: str,
    action: str,
    items: Sequence[dict[str, str]],
    order_start: int,
) -> int:
    order = order_start
    for item in items:
        steps.append(
            {
                "order": order,
                "action": action,
                "asset_type": asset_type,
                "asset_id": item.get("id"),
                "name": item.get("name"),
                "reason": f"delta:{action}",
            }
        )
        order += 1
    return order


def build_snapshot_delta_report(
    session: Session,
    *,
    snapshot_id: UUID,
) -> dict[str, Any]:
    snapshot = session.get(CelonisSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError("Snapshot not found")

    package_rows = session.exec(select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot_id)).all()
    package_definition_rows = session.exec(select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == snapshot_id)).all()
    task_rows = session.exec(select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)).all()
    task_detail_rows = session.exec(select(SnapshotTaskDetail).where(SnapshotTaskDetail.snapshot_id == snapshot_id)).all()
    data_model_rows = session.exec(select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == snapshot_id)).all()
    job_rows = session.exec(select(SnapshotJob).where(SnapshotJob.snapshot_id == snapshot_id)).all()
    km_rows = session.exec(select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == snapshot_id)).all()
    space_rows = session.exec(select(SnapshotSpace).where(SnapshotSpace.snapshot_id == snapshot_id)).all()
    app_rows = session.exec(select(SnapshotApp).where(SnapshotApp.snapshot_id == snapshot_id)).all()
    pool_rows = session.exec(select(SnapshotDataPool).where(SnapshotDataPool.snapshot_id == snapshot_id)).all()
    transformation_rows = session.exec(select(SnapshotTransformation).where(SnapshotTransformation.snapshot_id == snapshot_id)).all()

    previous_snapshot = _get_previous_snapshot(session, snapshot)
    if previous_snapshot is not None:
        prev_package_rows = session.exec(select(SnapshotPackage).where(SnapshotPackage.snapshot_id == previous_snapshot.id)).all()
        prev_package_definition_rows = session.exec(select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == previous_snapshot.id)).all()
        prev_task_rows = session.exec(select(SnapshotTask).where(SnapshotTask.snapshot_id == previous_snapshot.id)).all()
        prev_data_model_rows = session.exec(select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == previous_snapshot.id)).all()
        prev_job_rows = session.exec(select(SnapshotJob).where(SnapshotJob.snapshot_id == previous_snapshot.id)).all()
        prev_km_rows = session.exec(select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == previous_snapshot.id)).all()
        prev_space_rows = session.exec(select(SnapshotSpace).where(SnapshotSpace.snapshot_id == previous_snapshot.id)).all()
        prev_app_rows = session.exec(select(SnapshotApp).where(SnapshotApp.snapshot_id == previous_snapshot.id)).all()
        prev_pool_rows = session.exec(select(SnapshotDataPool).where(SnapshotDataPool.snapshot_id == previous_snapshot.id)).all()
        prev_transformation_rows = session.exec(select(SnapshotTransformation).where(SnapshotTransformation.snapshot_id == previous_snapshot.id)).all()
    else:
        prev_package_rows = prev_package_definition_rows = prev_task_rows = prev_data_model_rows = prev_job_rows = prev_km_rows = []
        prev_space_rows = prev_app_rows = prev_pool_rows = prev_transformation_rows = []

    return _build_delta(
        current_snapshot=snapshot,
        previous_snapshot=previous_snapshot,
        package_rows=package_rows,
        package_definition_rows=package_definition_rows,
        task_rows=task_rows,
        data_model_rows=data_model_rows,
        job_rows=job_rows,
        km_rows=km_rows,
        space_rows=space_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
        prev_package_rows=prev_package_rows,
        prev_package_definition_rows=prev_package_definition_rows,
        prev_task_rows=prev_task_rows,
        prev_data_model_rows=prev_data_model_rows,
        prev_job_rows=prev_job_rows,
        prev_km_rows=prev_km_rows,
        prev_space_rows=prev_space_rows,
        prev_app_rows=prev_app_rows,
        prev_pool_rows=prev_pool_rows,
        prev_transformation_rows=prev_transformation_rows,
    )


def build_snapshot_replay_plan(
    session: Session,
    *,
    snapshot_id: UUID,
) -> dict[str, Any]:
    snapshot = session.get(CelonisSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError("Snapshot not found")

    delta = build_snapshot_delta_report(session, snapshot_id=snapshot_id)
    previous_snapshot = _get_previous_snapshot(session, snapshot)

    steps: list[dict[str, Any]] = []
    order = 1
    assets = delta["assets"]

    order = _append_replay_steps(
        steps,
        asset_type="package",
        action="upsert",
        items=[*assets["packages"]["added"], *assets["packages"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="package_definition",
        action="upsert",
        items=[*assets["package_definitions"]["added"], *assets["package_definitions"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="data_model",
        action="upsert",
        items=[*assets["data_models"]["added"], *assets["data_models"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="data_pool",
        action="upsert",
        items=[*assets["data_pools"]["added"], *assets["data_pools"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="transformation",
        action="upsert",
        items=[*assets["transformations"]["added"], *assets["transformations"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="job",
        action="upsert",
        items=[*assets["jobs"]["added"], *assets["jobs"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="knowledge_model",
        action="upsert",
        items=[*assets["knowledge_models"]["added"], *assets["knowledge_models"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="app",
        action="upsert",
        items=[*assets["apps"]["added"], *assets["apps"]["modified"]],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="task",
        action="upsert",
        items=[*assets["tasks"]["added"], *assets["tasks"]["modified"]],
        order_start=order,
    )

    order = _append_replay_steps(
        steps,
        asset_type="task",
        action="delete",
        items=assets["tasks"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="app",
        action="delete",
        items=assets["apps"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="knowledge_model",
        action="delete",
        items=assets["knowledge_models"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="transformation",
        action="delete",
        items=assets["transformations"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="job",
        action="delete",
        items=assets["jobs"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="data_pool",
        action="delete",
        items=assets["data_pools"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="data_model",
        action="delete",
        items=assets["data_models"]["removed"],
        order_start=order,
    )
    order = _append_replay_steps(
        steps,
        asset_type="package",
        action="delete",
        items=assets["packages"]["removed"],
        order_start=order,
    )
    _append_replay_steps(
        steps,
        asset_type="package_definition",
        action="delete",
        items=assets["package_definitions"]["removed"],
        order_start=order,
    )

    return {
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": previous_snapshot.id if previous_snapshot else None,
        "generated_at": datetime.utcnow(),
        "dry_run": True,
        "summary": {
            "steps_total": len(steps),
            "upserts": len([step for step in steps if step["action"] == "upsert"]),
            "deletes": len([step for step in steps if step["action"] == "delete"]),
        },
        "steps": steps,
    }


def _generate_docs(
    docs_dir: Path,
    snapshot: CelonisSnapshot,
    package_rows: Sequence[SnapshotPackage],
    task_rows: Sequence[SnapshotTask],
    data_model_rows: Sequence[SnapshotDataModel],
    job_rows: Sequence[SnapshotJob],
    km_rows: Sequence[SnapshotKnowledgeModel],
    delta_report: dict[str, Any],
    graph: dict[str, list[dict[str, str]]],
    space_rows: Sequence[SnapshotSpace] = (),
    app_rows: Sequence[SnapshotApp] = (),
    pool_rows: Sequence[SnapshotDataPool] = (),
    transformation_rows: Sequence[SnapshotTransformation] = (),
) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)

    counts = {
        "spaces": len(space_rows),
        "packages": len(package_rows),
        "tasks": len(task_rows),
        "data_models": len(data_model_rows),
        "jobs": len(job_rows),
        "knowledge_models": len(km_rows),
        "apps": len(app_rows),
        "data_pools": len(pool_rows),
        "transformations": len(transformation_rows),
    }

    index_md = [
        f"# Snapshot Documentation - {snapshot.id}",
        "",
        f"- Client ID: {snapshot.client_id}",
        f"- Status: {snapshot.status.value}",
        f"- Started: {snapshot.started_at}",
        f"- Finished: {snapshot.finished_at}",
        f"- Generated At: {datetime.utcnow().isoformat()}",
        "",
        "## Asset Counts",
        "",
    ]
    for key, value in counts.items():
        index_md.append(f"- {key}: {value}")

    (docs_dir / "index.md").write_text("\n".join(index_md), encoding="utf-8")

    inventory_md = [
        "# Inventory",
        "",
        "## Spaces",
    ]
    for row in space_rows:
        inventory_md.append(f"- {row.name} ({row.space_id}) [{row.change_type.value}]")

    inventory_md.append("\n## Packages")
    for row in package_rows:
        inventory_md.append(f"- {row.name} ({row.package_id}) [{row.change_type.value}]")

    inventory_md.append("\n## Tasks")
    for row in task_rows:
        inventory_md.append(f"- {row.name} ({row.task_id}) type={row.task_type or 'unknown'}")

    inventory_md.append("\n## Data Models")
    for row in data_model_rows:
        inventory_md.append(f"- {row.name} ({row.data_model_id})")

    inventory_md.append("\n## Jobs")
    for row in job_rows:
        inventory_md.append(f"- {row.name} ({row.job_id})")

    inventory_md.append("\n## Knowledge Models")
    for row in km_rows:
        inventory_md.append(f"- {row.name} ({row.km_id})")

    inventory_md.append("\n## Apps")
    for row in app_rows:
        inventory_md.append(f"- {row.name} ({row.app_id}) [{row.change_type.value}]")

    inventory_md.append("\n## Data Pools")
    for row in pool_rows:
        inventory_md.append(f"- {row.name} ({row.pool_id}) [{row.change_type.value}]")

    inventory_md.append("\n## Transformations")
    for row in transformation_rows:
        pool_label = f" pool={row.pool_id}" if row.pool_id else ""
        inventory_md.append(f"- {row.name} ({row.transformation_id}){pool_label}")

    (docs_dir / "inventory.md").write_text("\n".join(inventory_md), encoding="utf-8")

    changes_md = [
        "# Change Summary",
        "",
        "## Delta Counts",
        "",
    ]
    for asset_name, payload in delta_report["assets"].items():
        counts_row = payload["counts"]
        changes_md.append(
            f"- {asset_name}: +{counts_row['added']} ~{counts_row['modified']} -{counts_row['removed']} ={counts_row['unchanged']}"
        )

    changes_md.append("\n## Package Change Flags")
    for row in package_rows:
        changes_md.append(f"- {row.name}: {row.change_type.value}")

    changes_md.append("\n## Task Change Flags")
    for row in task_rows:
        changes_md.append(f"- {row.name}: {row.change_type.value}")

    (docs_dir / "changes.md").write_text("\n".join(changes_md), encoding="utf-8")

    relationships_md = [
        "# Relationship Graph",
        "",
        f"- Nodes: {len(graph['nodes'])}",
        f"- Edges: {len(graph['edges'])}",
        "",
        "## Edges",
    ]
    for edge in graph["edges"]:
        relationships_md.append(f"- {edge['from']} --{edge['type']}--> {edge['to']}")
    if not graph["edges"]:
        relationships_md.append("- No explicit relationships could be inferred from available payload metadata.")

    (docs_dir / "relationships.md").write_text("\n".join(relationships_md), encoding="utf-8")

    errors_md = [
        "# Extraction Errors",
        "",
    ]
    if snapshot.error_message:
        errors_md.append(f"- Snapshot error: {snapshot.error_message}")
    else:
        errors_md.append("- No snapshot-level errors recorded.")

    (docs_dir / "errors.md").write_text("\n".join(errors_md), encoding="utf-8")


def build_snapshot_export(
    session: Session,
    *,
    snapshot_id: UUID,
    base_output_dir: Path,
) -> dict:
    snapshot = session.get(CelonisSnapshot, snapshot_id)
    if snapshot is None:
        raise ValueError("Snapshot not found")

    package_rows = session.exec(select(SnapshotPackage).where(SnapshotPackage.snapshot_id == snapshot_id)).all()
    package_definition_rows = session.exec(select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == snapshot_id)).all()
    task_rows = session.exec(select(SnapshotTask).where(SnapshotTask.snapshot_id == snapshot_id)).all()
    task_detail_rows = session.exec(select(SnapshotTaskDetail).where(SnapshotTaskDetail.snapshot_id == snapshot_id)).all()
    data_model_rows = session.exec(select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == snapshot_id)).all()
    job_rows = session.exec(select(SnapshotJob).where(SnapshotJob.snapshot_id == snapshot_id)).all()
    km_rows = session.exec(select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == snapshot_id)).all()
    space_rows = session.exec(select(SnapshotSpace).where(SnapshotSpace.snapshot_id == snapshot_id)).all()
    app_rows = session.exec(select(SnapshotApp).where(SnapshotApp.snapshot_id == snapshot_id)).all()
    pool_rows = session.exec(select(SnapshotDataPool).where(SnapshotDataPool.snapshot_id == snapshot_id)).all()
    transformation_rows = session.exec(select(SnapshotTransformation).where(SnapshotTransformation.snapshot_id == snapshot_id)).all()

    previous_snapshot = _get_previous_snapshot(session, snapshot)
    if previous_snapshot is not None:
        prev_package_rows = session.exec(select(SnapshotPackage).where(SnapshotPackage.snapshot_id == previous_snapshot.id)).all()
        prev_package_definition_rows = session.exec(select(SnapshotPackageDefinition).where(SnapshotPackageDefinition.snapshot_id == previous_snapshot.id)).all()
        prev_task_rows = session.exec(select(SnapshotTask).where(SnapshotTask.snapshot_id == previous_snapshot.id)).all()
        prev_data_model_rows = session.exec(select(SnapshotDataModel).where(SnapshotDataModel.snapshot_id == previous_snapshot.id)).all()
        prev_job_rows = session.exec(select(SnapshotJob).where(SnapshotJob.snapshot_id == previous_snapshot.id)).all()
        prev_km_rows = session.exec(select(SnapshotKnowledgeModel).where(SnapshotKnowledgeModel.snapshot_id == previous_snapshot.id)).all()
        prev_space_rows = session.exec(select(SnapshotSpace).where(SnapshotSpace.snapshot_id == previous_snapshot.id)).all()
        prev_app_rows = session.exec(select(SnapshotApp).where(SnapshotApp.snapshot_id == previous_snapshot.id)).all()
        prev_pool_rows = session.exec(select(SnapshotDataPool).where(SnapshotDataPool.snapshot_id == previous_snapshot.id)).all()
        prev_transformation_rows = session.exec(select(SnapshotTransformation).where(SnapshotTransformation.snapshot_id == previous_snapshot.id)).all()
    else:
        prev_package_rows = prev_package_definition_rows = prev_task_rows = prev_data_model_rows = prev_job_rows = prev_km_rows = []
        prev_space_rows = prev_app_rows = prev_pool_rows = prev_transformation_rows = []

    delta_report = _build_delta(
        current_snapshot=snapshot,
        previous_snapshot=previous_snapshot,
        package_rows=package_rows,
        package_definition_rows=package_definition_rows,
        task_rows=task_rows,
        data_model_rows=data_model_rows,
        job_rows=job_rows,
        km_rows=km_rows,
        space_rows=space_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
        prev_package_rows=prev_package_rows,
        prev_package_definition_rows=prev_package_definition_rows,
        prev_task_rows=prev_task_rows,
        prev_data_model_rows=prev_data_model_rows,
        prev_job_rows=prev_job_rows,
        prev_km_rows=prev_km_rows,
        prev_space_rows=prev_space_rows,
        prev_app_rows=prev_app_rows,
        prev_pool_rows=prev_pool_rows,
        prev_transformation_rows=prev_transformation_rows,
    )
    relationship_graph = _build_relationship_graph(
        package_rows,
        package_definition_rows,
        task_rows,
        data_model_rows,
        job_rows,
        km_rows,
        space_rows=space_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
    )

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    export_dir = base_output_dir / f"snapshot_{snapshot_id}_{ts}"
    data_dir = export_dir / "data"
    docs_dir = export_dir / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)

    asset_counts = _snapshot_counts(
        space_rows=space_rows,
        package_rows=package_rows,
        package_definition_rows=package_definition_rows,
        task_rows=task_rows,
        task_detail_rows=task_detail_rows,
        data_model_rows=data_model_rows,
        job_rows=job_rows,
        km_rows=km_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
    )

    _json_dump(
        export_dir / "manifest.json",
        {
            "snapshot_id": str(snapshot_id),
            "client_id": str(snapshot.client_id),
            "generated_at": datetime.utcnow().isoformat(),
            "status": snapshot.status.value,
            "previous_snapshot_id": str(previous_snapshot.id) if previous_snapshot else None,
            "counts": asset_counts,
            "delta_counts": {
                asset_name: payload["counts"]
                for asset_name, payload in delta_report["assets"].items()
            },
            "relationship_graph": {
                "nodes": len(relationship_graph["nodes"]),
                "edges": len(relationship_graph["edges"]),
            },
        },
    )

    _json_dump(data_dir / "delta.json", delta_report)
    _json_dump(data_dir / "relationships.json", relationship_graph)

    _jsonl_dump(
        data_dir / "spaces.jsonl",
        _serialize_rows(space_rows, ["id", "snapshot_id", "client_id", "space_id", "name", "change_type", "raw_json", "created_at"]),
    )
    _jsonl_dump(
        data_dir / "packages.jsonl",
        _serialize_rows(
            package_rows,
            ["id", "snapshot_id", "client_id", "package_id", "name", "key", "space_id", "space_name", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "package_definitions.jsonl",
        _serialize_rows(
            package_definition_rows,
            [
                "id",
                "snapshot_id",
                "client_id",
                "package_id",
                "package_key",
                "definition_id",
                "source_endpoint",
                "raw_yaml",
                "parsed_json",
                "parse_error",
                "change_type",
                "content_hash",
                "created_at",
            ],
        ),
    )
    _jsonl_dump(
        data_dir / "tasks.jsonl",
        _serialize_rows(
            task_rows,
            ["id", "snapshot_id", "client_id", "package_id", "task_id", "name", "task_type", "description", "pql_formula", "change_type", "content_hash", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "task_details.jsonl",
        _serialize_rows(
            task_detail_rows,
            [
                "id",
                "snapshot_id",
                "client_id",
                "task_id",
                "package_id",
                "task_type",
                "source_endpoint",
                "detail_json",
                "references_json",
                "dependencies_json",
                "error_message",
                "created_at",
            ],
        ),
    )
    _jsonl_dump(
        data_dir / "data_models.jsonl",
        _serialize_rows(
            data_model_rows,
            ["id", "snapshot_id", "client_id", "data_model_id", "name", "space_id", "space_name", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "jobs.jsonl",
        _serialize_rows(
            job_rows,
            ["id", "snapshot_id", "client_id", "job_id", "name", "pool_id", "pool_name", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "knowledge_models.jsonl",
        _serialize_rows(
            km_rows,
            ["id", "snapshot_id", "client_id", "km_id", "name", "space_id", "space_name", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "apps.jsonl",
        _serialize_rows(
            app_rows,
            ["id", "snapshot_id", "client_id", "app_id", "name", "space_id", "space_name", "package_key", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "data_pools.jsonl",
        _serialize_rows(
            pool_rows,
            ["id", "snapshot_id", "client_id", "pool_id", "name", "change_type", "raw_json", "created_at"],
        ),
    )
    _jsonl_dump(
        data_dir / "transformations.jsonl",
        _serialize_rows(
            transformation_rows,
            ["id", "snapshot_id", "client_id", "transformation_id", "name", "pool_id", "pool_name", "change_type", "raw_json", "created_at"],
        ),
    )

    _generate_docs(
        docs_dir,
        snapshot,
        package_rows,
        task_rows,
        data_model_rows,
        job_rows,
        km_rows,
        delta_report,
        relationship_graph,
        space_rows=space_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
    )

    mirror_dir = _build_snapshot_mirror(
        session,
        mirror_root=export_dir / "mirror",
        snapshot=snapshot,
        space_rows=space_rows,
        package_rows=package_rows,
        package_definition_rows=package_definition_rows,
        task_rows=task_rows,
        task_detail_rows=task_detail_rows,
        data_model_rows=data_model_rows,
        job_rows=job_rows,
        km_rows=km_rows,
        app_rows=app_rows,
        pool_rows=pool_rows,
        transformation_rows=transformation_rows,
        delta_report=delta_report,
    )

    bundle_path = export_dir.with_suffix(".zip")
    with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as zf:
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.relative_to(export_dir))

    return {
        "snapshot_id": snapshot_id,
        "export_dir": str(export_dir.resolve()),
        "mirror_dir": str(mirror_dir.resolve()),
        "bundle_path": str(bundle_path.resolve()),
        "docs_path": str(docs_dir.resolve()),
        "generated_at": datetime.utcnow(),
        "asset_counts": asset_counts,
        "delta_counts": {
            asset_name: payload["counts"]
            for asset_name, payload in delta_report["assets"].items()
        },
        "relationship_graph": {
            "nodes": len(relationship_graph["nodes"]),
            "edges": len(relationship_graph["edges"]),
        },
    }
