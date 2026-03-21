from collections import Counter

from foundry.models import UseCase
from foundry.schemas import (
    UseCaseIndustryBenchmarkBucketOut,
    UseCaseIndustryBenchmarkSummaryOut,
    UseCaseViewOut,
)


def to_view_payload(use_case: UseCase, *, view_mode: str) -> UseCaseViewOut:
    if view_mode == "internal":
        return UseCaseViewOut(
            id=use_case.id,
            title=use_case.title,
            summary=use_case.summary,
            problem_statement=use_case.problem_statement,
            industry=use_case.industry,
            process_domain=use_case.process_domain,
            maturity=use_case.maturity,
            tags_json=use_case.tags_json,
            api_dependencies_json=use_case.api_dependencies_json,
            owner_person_id=use_case.owner_person_id,
            client_id=use_case.client_id,
            project_id=use_case.project_id,
            view_mode="internal",
            created_at=use_case.created_at,
            updated_at=use_case.updated_at,
        )

    if view_mode == "anonymized":
        return UseCaseViewOut(
            id=use_case.id,
            title=use_case.title,
            summary=use_case.summary,
            problem_statement=None,
            industry=use_case.industry,
            process_domain=use_case.process_domain,
            maturity=use_case.maturity,
            tags_json=use_case.tags_json,
            api_dependencies_json=use_case.api_dependencies_json,
            owner_person_id=None,
            client_id=None,
            project_id=None,
            view_mode="anonymized",
            created_at=use_case.created_at,
            updated_at=use_case.updated_at,
        )

    if view_mode == "client":
        return UseCaseViewOut(
            id=use_case.id,
            title=use_case.title,
            summary=use_case.summary,
            problem_statement=use_case.problem_statement,
            industry=use_case.industry,
            process_domain=use_case.process_domain,
            maturity=use_case.maturity,
            tags_json=use_case.tags_json,
            api_dependencies_json=use_case.api_dependencies_json,
            owner_person_id=use_case.owner_person_id,
            client_id=use_case.client_id,
            project_id=use_case.project_id,
            view_mode="client",
            created_at=use_case.created_at,
            updated_at=use_case.updated_at,
        )

    if view_mode == "industry_benchmark":
        return UseCaseViewOut(
            id=use_case.id,
            title=use_case.title,
            summary=use_case.summary,
            problem_statement=None,
            industry=use_case.industry,
            process_domain=use_case.process_domain,
            maturity=use_case.maturity,
            tags_json=use_case.tags_json,
            api_dependencies_json=use_case.api_dependencies_json,
            owner_person_id=None,
            client_id=None,
            project_id=None,
            view_mode="industry_benchmark",
            created_at=use_case.created_at,
            updated_at=use_case.updated_at,
        )

    raise ValueError(f"Unsupported view_mode: {view_mode}")


def to_industry_benchmark_summary(use_cases: list[UseCase]) -> UseCaseIndustryBenchmarkSummaryOut:
    grouped_counts: dict[tuple[str, str, str], int] = {}
    tag_counter: Counter[str] = Counter()
    api_dependency_counter: Counter[str] = Counter()

    for use_case in use_cases:
        industry = use_case.industry or "unknown"
        process_domain = use_case.process_domain or "unknown"
        maturity = use_case.maturity.value
        grouped_counts[(industry, process_domain, maturity)] = grouped_counts.get((industry, process_domain, maturity), 0) + 1

        for tag in use_case.tags_json:
            normalized_tag = tag.strip().lower()
            if normalized_tag:
                tag_counter[normalized_tag] += 1

        for api_dependency in use_case.api_dependencies_json:
            normalized_dependency = api_dependency.strip().lower()
            if normalized_dependency:
                api_dependency_counter[normalized_dependency] += 1

    buckets = [
        UseCaseIndustryBenchmarkBucketOut(
            industry=industry,
            process_domain=process_domain,
            maturity=maturity,
            use_case_count=count,
        )
        for (industry, process_domain, maturity), count in grouped_counts.items()
    ]
    buckets.sort(
        key=lambda bucket: (
            -bucket.use_case_count,
            bucket.industry,
            bucket.process_domain,
            bucket.maturity.value,
        )
    )

    return UseCaseIndustryBenchmarkSummaryOut(
        total_use_cases=len(use_cases),
        bucket_count=len(buckets),
        buckets=buckets,
        top_tags=[name for name, _ in tag_counter.most_common(10)],
        top_api_dependencies=[name for name, _ in api_dependency_counter.most_common(10)],
    )
