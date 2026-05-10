from foundry.mcp._stub_server import run_stub_server


def main() -> int:
    return run_stub_server(
        tool_id="agentic-deployment-readiness-mcp",
        purpose="Check release readiness gates for deployment, approval, and quality criteria.",
    )


if __name__ == "__main__":
    raise SystemExit(main())
