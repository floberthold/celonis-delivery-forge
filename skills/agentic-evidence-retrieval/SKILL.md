---
name: agentic-evidence-retrieval
description: Retrieve evidence artifacts for failing user journeys including traces, screenshots, browser logs, and execution metadata.
---

# Agentic Evidence Retrieval Skill

Use this skill when an agent needs to:

- Access traces and execution records from failing test journeys.
- Retrieve screenshots from key decision points in failed flows.
- Query browser console and server logs for a specific failure.
- Export complete evidence packages for analysis or reproduction.
- Correlate evidence across multiple failure instances.

## Tool usage order

1. Retrieve evidence for a journey:
   - Full: `python -m foundry.mcp.agentic_evidence retrieve --journey-id <id> --scope full`
   - Summary: `python -m foundry.mcp.agentic_evidence retrieve --journey-id <id> --scope summary`
2. Export evidence package:
   - `python -m foundry.mcp.agentic_evidence export --journey-id <id> --format zip`
3. Analyze evidence metadata and logs.

## Expected outputs

- Journey execution traces with timing information.
- Screenshots at decision points or failure moments.
- Logs (browser console, server output, test framework output).
- Metadata (environment, timestamps, reproducer steps).

## Safety rules

- Do not store personally identifiable information in evidence exports.
- Preserve all evidence timestamps for causality analysis.
- Include full call stacks and error messages for debugging.
- Document evidence collection scope and filters used.
