from __future__ import annotations

from foundry.services.email_service import send_email as old_send_email
from foundry.services.feature_rollout import (
    enabled_domains_for_org as old_enabled_domains_for_org,
    resolve_rollout_profile as old_resolve_rollout_profile,
)
from foundry.services.template_seed import (
    DEFAULT_LIBRARY_NAME as old_default_library_name,
    DEFAULT_TEMPLATES as old_default_templates,
    seed_default_templates as old_seed_default_templates,
)
from foundry.services.use_case_views import (
    to_industry_benchmark_summary as old_to_industry_benchmark_summary,
    to_view_payload as old_to_view_payload,
)
from foundry.services.trycelonis_demo_rebuild import (
    TryCelonisSyncResult as old_trycelonis_sync_result,
    sync_trycelonis_demos as old_sync_trycelonis_demos,
)
from foundry.services.ingest_service import (
    execute_code_drop_ingest as old_execute_code_drop_ingest,
    execute_repo_sync_ingest as old_execute_repo_sync_ingest,
)
from foundry.services.florian_script_seed import (
    import_florian_scripts_to_project as old_import_florian_scripts_to_project,
    register_florian_script_assets as old_register_florian_script_assets,
)
from foundry.services.integrations.email_service import send_email as new_send_email
from foundry.services.platform.feature_rollout import (
    enabled_domains_for_org as new_enabled_domains_for_org,
    resolve_rollout_profile as new_resolve_rollout_profile,
)
from foundry.services.delivery.template_seed import (
    DEFAULT_LIBRARY_NAME as new_default_library_name,
    DEFAULT_TEMPLATES as new_default_templates,
    seed_default_templates as new_seed_default_templates,
)
from foundry.services.knowledge.use_case_views import (
    to_industry_benchmark_summary as new_to_industry_benchmark_summary,
    to_view_payload as new_to_view_payload,
)
from foundry.services.integrations.trycelonis_demo_rebuild import (
    TryCelonisSyncResult as new_trycelonis_sync_result,
    sync_trycelonis_demos as new_sync_trycelonis_demos,
)
from foundry.services.integrations.ingest_service import (
    execute_code_drop_ingest as new_execute_code_drop_ingest,
    execute_repo_sync_ingest as new_execute_repo_sync_ingest,
)
from foundry.services.delivery.florian_script_seed import (
    import_florian_scripts_to_project as new_import_florian_scripts_to_project,
    register_florian_script_assets as new_register_florian_script_assets,
)


def test_email_service_shim_exports_new_symbol() -> None:
    assert old_send_email is new_send_email


def test_feature_rollout_shim_exports_new_symbols() -> None:
    assert old_enabled_domains_for_org is new_enabled_domains_for_org
    assert old_resolve_rollout_profile is new_resolve_rollout_profile


def test_template_seed_shim_exports_new_symbols() -> None:
    assert old_seed_default_templates is new_seed_default_templates
    assert old_default_library_name == new_default_library_name
    assert old_default_templates == new_default_templates


def test_use_case_views_shim_exports_new_symbols() -> None:
    assert old_to_view_payload is new_to_view_payload
    assert old_to_industry_benchmark_summary is new_to_industry_benchmark_summary


def test_trycelonis_rebuild_shim_exports_new_symbols() -> None:
    assert old_sync_trycelonis_demos is new_sync_trycelonis_demos
    assert old_trycelonis_sync_result is new_trycelonis_sync_result


def test_ingest_service_shim_exports_new_symbols() -> None:
    assert old_execute_code_drop_ingest is new_execute_code_drop_ingest
    assert old_execute_repo_sync_ingest is new_execute_repo_sync_ingest


def test_florian_script_seed_shim_exports_new_symbols() -> None:
    assert old_register_florian_script_assets is new_register_florian_script_assets
    assert old_import_florian_scripts_to_project is new_import_florian_scripts_to_project
