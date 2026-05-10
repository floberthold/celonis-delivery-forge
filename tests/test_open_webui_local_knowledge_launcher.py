from pathlib import Path


def test_open_webui_local_knowledge_launcher_sets_default_model() -> None:
    script_path = Path("scripts/start_open_webui_local_knowledge.ps1")
    content = script_path.read_text(encoding="utf-8")

    assert '$env:ENABLE_PERSISTENT_CONFIG = "false"' in content
    assert '$env:DEFAULT_MODELS = "local-wiki-query/smollm2:135m"' in content
    assert '$env:ENABLE_OLLAMA_API = "false"' in content
