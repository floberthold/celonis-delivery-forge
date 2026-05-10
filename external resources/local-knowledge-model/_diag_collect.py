from pathlib import Path
from obsidian_llm_wiki.config import Config
from obsidian_llm_wiki.pipeline.ingest import collect_ingest_paths

vault = Path(r"C:\coding\celonis-delivery-forge\external resources\local-knowledge-model\my-obsidian-wiki")
config = Config.from_vault(vault)
paths = collect_ingest_paths(config)
needle = vault / "raw" / "Celonis Docs" / "6b) The Big Book of Action Flows_EXTERNAL (Updated)" / "group-001-004.md"
print("total", len(paths))
print("contains needle", needle in paths)
print("first celonis entries", [p.as_posix() for p in paths if "6b) The Big Book of Action Flows_EXTERNAL (Updated)" in p.as_posix()][:5])
