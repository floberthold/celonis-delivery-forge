from dataclasses import dataclass


@dataclass
class CelonisImportResult:
    imported_assets: int
    skipped_assets: int


class CelonisReadOnlyImporter:
    def run(self, *, source_label: str, dry_run: bool = True) -> CelonisImportResult:
        if dry_run:
            return CelonisImportResult(imported_assets=0, skipped_assets=0)
        return CelonisImportResult(imported_assets=0, skipped_assets=0)
