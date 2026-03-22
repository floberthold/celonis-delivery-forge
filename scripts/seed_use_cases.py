from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import foundry.db as db_module
from foundry.models import UseCase, UseCaseMaturity


SEED_USE_CASES: list[dict] = [
    {
        "title": "3P Enrichment with Process Intelligence",
        "summary": "Enrich third-party business objects with process scores, priority signals, anomaly flags, and KPI context from Celonis.",
        "problem_statement": "Operational systems often lack process-aware context, making prioritization and exception handling less effective.",
        "industry": "Cross-industry",
        "process_domain": "Operations",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["3p", "enrichment", "process intelligence", "kpi"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Process-Specific Recommendations in 3P Apps",
        "summary": "Deliver process-aware recommendations directly inside third-party applications to guide frontline decisions.",
        "problem_statement": "Users in operational tools need immediate next-best actions that reflect actual process state and risk.",
        "industry": "Cross-industry",
        "process_domain": "Operations",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["recommendations", "decision support", "3p"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Task-Level Process Status for 3P Applications",
        "summary": "Expose granular activity and task-level status information from Celonis inside external applications.",
        "problem_statement": "Case-level summaries are often too coarse for teams that need actionable activity status and bottleneck visibility.",
        "industry": "Cross-industry",
        "process_domain": "Operations",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["task status", "activity status", "3p"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Export Process Analytics to Third-Party Platforms",
        "summary": "Share process KPIs and transformation impact metrics with downstream systems and partner applications.",
        "problem_statement": "Process insights are most useful when distributed beyond Celonis into decisioning, reporting, and business workflows.",
        "industry": "Cross-industry",
        "process_domain": "Analytics",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["analytics export", "kpi sharing", "impact analysis"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "OOTB Business Intelligence Integration",
        "summary": "Expose self-discoverable Celonis knowledge metadata and service definitions to BI tools through structured access patterns.",
        "problem_statement": "Analytics teams need stable, discoverable interfaces for consuming process data in standard BI ecosystems.",
        "industry": "Cross-industry",
        "process_domain": "Analytics",
        "maturity": UseCaseMaturity.pilot,
        "tags_json": ["bi", "odata", "metadata", "semantic access"],
        "api_dependencies_json": ["Knowledge Model API", "OData Protocol"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Trigger Third-Party Procedures and Automations",
        "summary": "Use Celonis inefficiencies, anomaly signals, and case events to trigger downstream automations in external platforms.",
        "problem_statement": "Identified process issues lose value if they are not connected to execution mechanisms that can resolve them.",
        "industry": "Cross-industry",
        "process_domain": "Automation",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["automation", "subscription", "event trigger", "remediation"],
        "api_dependencies_json": ["Knowledge Model API", "Subscription API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Feed Live Dashboards with Process Intelligence",
        "summary": "Keep external dashboards synchronized with fresh process KPIs and operational objects from Celonis.",
        "problem_statement": "Static or delayed reporting reduces the usefulness of process intelligence in live operational steering.",
        "industry": "Cross-industry",
        "process_domain": "Analytics",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["dashboard", "live sync", "reporting"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Contextual Data Synchronization",
        "summary": "Synchronize third-party data lakes and operational stores with fresh process context from Celonis.",
        "problem_statement": "Downstream data products need current process context to remain relevant for analytics and automation.",
        "industry": "Cross-industry",
        "process_domain": "Data Integration",
        "maturity": UseCaseMaturity.validated,
        "tags_json": ["data sync", "data lake", "context propagation"],
        "api_dependencies_json": ["Knowledge Model API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Execute Celonis Tools from External GenAI Agents",
        "summary": "Allow external AI agents to execute informative and actionable Celonis tools within the relevant process context.",
        "problem_statement": "AI agents need governed access to process knowledge and actions to make context-aware decisions.",
        "industry": "Cross-industry",
        "process_domain": "AI",
        "maturity": UseCaseMaturity.pilot,
        "tags_json": ["genai", "agent tools", "mcp", "tool execution"],
        "api_dependencies_json": ["AI Agent API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Chat with Celonis GenAI Agents from Third-Party Apps",
        "summary": "Embed conversational Celonis agents into external applications for guided questions and decisions in process context.",
        "problem_statement": "Users increasingly expect conversational access to process knowledge without leaving their working application.",
        "industry": "Cross-industry",
        "process_domain": "AI",
        "maturity": UseCaseMaturity.pilot,
        "tags_json": ["chat", "genai", "assistant", "embedded experience"],
        "api_dependencies_json": ["AI Agent API"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Generate Semantic Tools from Celonis Knowledge",
        "summary": "Generate tools and OpenAPI-style contracts from Celonis process knowledge for third-party agents and applications.",
        "problem_statement": "Third-party agents need a structured semantic layer to understand available process entities, stats, and retrieval actions.",
        "industry": "Cross-industry",
        "process_domain": "AI",
        "maturity": UseCaseMaturity.pilot,
        "tags_json": ["semantic tools", "openapi", "knowledge model", "agent enablement"],
        "api_dependencies_json": ["Knowledge Model API", "Semantic Extensions"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
    {
        "title": "Centralized Searchable Use-Case Library",
        "summary": "Build a central searchable catalog of delivery use cases linked to projects, people, clients, industries, and visibility modes.",
        "problem_statement": "Delivery teams need one governed place to find reusable patterns, anonymized references, and client-specific examples.",
        "industry": "Cross-industry",
        "process_domain": "Knowledge Management",
        "maturity": UseCaseMaturity.idea,
        "tags_json": ["library", "search", "benchmarking", "knowledge reuse"],
        "api_dependencies_json": ["Internal (Forge)"],
        "is_anonymized_ready": True,
        "is_client_view_enabled": True,
        "is_industry_benchmark_eligible": True,
    },
]


def main() -> None:
    db_module.init_db()

    inserted = 0
    updated = 0

    with Session(db_module.engine) as session:
        existing_by_title = {
            row.title: row
            for row in session.exec(select(UseCase)).all()
        }

        for payload in SEED_USE_CASES:
            existing = existing_by_title.get(payload["title"])
            if existing is None:
                session.add(UseCase(**payload))
                inserted += 1
                continue

            for field_name, field_value in payload.items():
                setattr(existing, field_name, field_value)
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            updated += 1

        session.commit()

        total = len(session.exec(select(UseCase)).all())

    print(f"seeded_use_cases inserted={inserted} updated={updated} total={total}")


if __name__ == "__main__":
    main()