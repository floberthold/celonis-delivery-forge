from foundry.mcp._stub_server import run_stub_server


def main() -> int:
    return run_stub_server(
        tool_id="agentic-evidence-retrieval-mcp",
        purpose="Return evidence references for failing user journeys (traces, screenshots, logs).",
    )


if __name__ == "__main__":
    raise SystemExit(main())
