param(
    [Parameter(Mandatory = $true)]
    [string]$TaskId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("Discovery", "WorkshopPrep", "KPIDesign", "IssueTriage", "SteeringPack", "RiskReview", "ClientComms", "FollowUp")]
    [string]$Preset,

    [string]$Owner = "Delivery Forge core team",
    [string]$Agent = "codex",
    [string]$BaseBranch = "main"
)

$ErrorActionPreference = "Stop"

function Get-Slug {
    param([string]$Text)
    $slug = $Text.ToLowerInvariant()
    $slug = [regex]::Replace($slug, "[^a-z0-9]+", "-")
    $slug = $slug.Trim("-")
    if ([string]::IsNullOrWhiteSpace($slug)) {
        return "run"
    }
    return $slug
}

function Join-Lines {
    param([string[]]$Items)

    $out = @()
    foreach ($i in $Items) {
        $out += "- $i"
    }
    return ($out -join [Environment]::NewLine)
}

function Join-Plan {
    param([string[]]$Items)

    $out = @()
    for ($i = 0; $i -lt $Items.Count; $i++) {
        $num = $i + 1
        $out += "$num. $($Items[$i])"
    }
    return ($out -join [Environment]::NewLine)
}

function Get-PresetDefinition {
    param([string]$Name)

    switch ($Name) {
        "Discovery" {
            return @{
                Title = "client discovery synthesis"
                Lane = "consulting-discovery"
                Scope = "Synthesize requirements, constraints, and pain points from notes into decision-ready backlog inputs."
                Success = @(
                    "At least 10 discovery notes are normalized into themes with owner and impact.",
                    "Top 5 opportunities are ranked by business value and implementation effort.",
                    "Open questions list is ready for client validation session."
                )
                Stop = @(
                    "Input notes are incomplete or conflicting with no source trace.",
                    "Key stakeholder requirements cannot be attributed to evidence."
                )
                Plan = @(
                    "Collect current meeting notes and artifacts into one source list.",
                    "Produce theme map, opportunity ranking, and open questions.",
                    "Create stakeholder review summary and next-step proposal."
                )
                NextAction = "Gather latest workshop notes and start synthesis pass."
            }
        }
        "WorkshopPrep" {
            return @{
                Title = "workshop preparation and agenda"
                Lane = "consulting-workshop"
                Scope = "Prepare structured workshop agenda, prompts, and expected outcomes for client alignment."
                Success = @(
                    "Agenda covers objectives, timing, decisions, and owners for each segment.",
                    "Decision prompts are prepared for all unresolved topics.",
                    "Pre-read pack is available at least 24 hours before workshop."
                )
                Stop = @(
                    "Required participants are unknown or unavailable.",
                    "Workshop objective cannot be tied to delivery milestone."
                )
                Plan = @(
                    "Draft agenda and decision prompts.",
                    "Align agenda with project milestone and risks.",
                    "Publish pre-read and confirm attendee readiness."
                )
                NextAction = "Draft first agenda version and circulate for internal review."
            }
        }
        "KPIDesign" {
            return @{
                Title = "kpi definition and acceptance pack"
                Lane = "consulting-kpi"
                Scope = "Define KPI specification with formula intent, data assumptions, and acceptance criteria."
                Success = @(
                    "KPI definition includes metric purpose, owner, and decision usage.",
                    "Data model assumptions and edge cases are explicitly documented.",
                    "Acceptance criteria are testable with sample records."
                )
                Stop = @(
                    "Source data ownership is unresolved.",
                    "Formula intent conflicts with stakeholder expectations."
                )
                Plan = @(
                    "Draft KPI spec and decision context.",
                    "Validate assumptions with data and process owners.",
                    "Finalize acceptance criteria and sign-off notes."
                )
                NextAction = "Create KPI draft for highest-priority business question."
            }
        }
        "IssueTriage" {
            return @{
                Title = "issue triage and resolution routing"
                Lane = "consulting-operations"
                Scope = "Classify incoming issues, assign severity, and route to actionable owners with SLA intent."
                Success = @(
                    "New issues are tagged by severity, domain, and owner.",
                    "Critical blockers have mitigation path and escalation owner.",
                    "SLA-oriented next actions are logged for every active issue."
                )
                Stop = @(
                    "Issue owner cannot be identified.",
                    "Severity assessment lacks reproducible evidence."
                )
                Plan = @(
                    "Collect issue queue snapshot.",
                    "Classify and prioritize by impact and urgency.",
                    "Route issues with clear action, owner, and due date."
                )
                NextAction = "Run first triage pass on open issue backlog."
            }
        }
        "SteeringPack" {
            return @{
                Title = "steering committee status pack"
                Lane = "consulting-steering"
                Scope = "Build concise steering package with progress, risks, decisions needed, and timeline confidence."
                Success = @(
                    "Status pack covers achievements, blockers, and milestone confidence.",
                    "Decision requests are specific and owner-assigned.",
                    "Risk heatmap reflects current reality with mitigation status."
                )
                Stop = @(
                    "Milestone status cannot be supported by evidence.",
                    "Decision owners are unclear for critical items."
                )
                Plan = @(
                    "Assemble weekly delivery evidence.",
                    "Draft steering narrative and decision asks.",
                    "Validate with internal lead before client steering."
                )
                NextAction = "Collect this week delivery highlights and risk changes."
            }
        }
        "RiskReview" {
            return @{
                Title = "risk and dependency review"
                Lane = "consulting-risk"
                Scope = "Review delivery risks and dependencies with mitigation actions, triggers, and owners."
                Success = @(
                    "Top risks are ranked by probability and impact.",
                    "Every critical risk has mitigation owner and trigger condition.",
                    "Dependency map is updated with blocked and at-risk items."
                )
                Stop = @(
                    "Risk owners unavailable for confirmation.",
                    "Dependency status cannot be verified from source systems."
                )
                Plan = @(
                    "Refresh risk register and dependency list.",
                    "Validate owner commitments for mitigations.",
                    "Publish updated risk summary with escalation flags."
                )
                NextAction = "Run risk review with workstream owners and capture mitigation updates."
            }
        }
        "ClientComms" {
            return @{
                Title = "client communication drafting"
                Lane = "consulting-communications"
                Scope = "Prepare clear client updates for progress, decisions, and escalations with consistent tone."
                Success = @(
                    "Update message includes progress, blockers, and clear next steps.",
                    "Decisions needed are explicit with due dates.",
                    "Communication is aligned with current delivery evidence."
                )
                Stop = @(
                    "Message cannot be backed by factual delivery status.",
                    "Escalation wording risks ambiguity or misalignment."
                )
                Plan = @(
                    "Draft update with factual progress summary.",
                    "Review wording for clarity and accountability.",
                    "Send or stage for lead approval with action tracking."
                )
                NextAction = "Draft this week client update from latest run evidence."
            }
        }
        "FollowUp" {
            return @{
                Title = "meeting follow-up and action tracker"
                Lane = "consulting-follow-up"
                Scope = "Convert meeting outcomes into owner-assigned actions, dates, and validation checkpoints."
                Success = @(
                    "Meeting decisions are converted into tracked actions within 24 hours.",
                    "Every action has owner, due date, and expected artifact.",
                    "Follow-up summary is distributed and acknowledged by stakeholders."
                )
                Stop = @(
                    "Action ownership is disputed or missing.",
                    "Meeting notes do not provide sufficient decision clarity."
                )
                Plan = @(
                    "Extract decisions and action items from notes.",
                    "Assign owners and deadlines with validation checkpoints.",
                    "Publish follow-up summary and monitor acknowledgements."
                )
                NextAction = "Process latest meeting notes and publish action tracker draft."
            }
        }
        default {
            throw "Unknown preset: $Name"
        }
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Could not resolve git repository root."
}

$presetDef = Get-PresetDefinition -Name $Preset
$title = "$($presetDef.Title)"
$slug = Get-Slug -Text "$TaskId-$Preset-$title"
$runId = "$TaskId-$slug"
$branchName = "agent/$runId"
$worktreePath = Join-Path $repoRoot ".worktrees/$runId"
$runDir = Join-Path $repoRoot ".orchestration/runs"
$runCardPath = Join-Path $runDir "$runId.md"

if (-not (Test-Path $runDir)) {
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
}

if (Test-Path $runCardPath) {
    throw "Run card already exists: $runCardPath"
}

$existingBranch = git branch --list $branchName
if ([string]::IsNullOrWhiteSpace($existingBranch)) {
    git worktree add -b $branchName $worktreePath $BaseBranch
} else {
    git worktree add $worktreePath $branchName
}

$createdAtUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$successLines = Join-Lines -Items $presetDef.Success
$stopLines = Join-Lines -Items $presetDef.Stop
$planLines = Join-Plan -Items $presetDef.Plan

$card = @"
# Agent Run Card

run_id: $runId
status: TODO
created_at: $createdAtUtc
owner: $Owner
agent: $Agent
lane: $($presetDef.Lane)
base_branch: $BaseBranch
run_branch: $branchName
worktree_path: $worktreePath

## Task
- Title: $title
- Scope: $($presetDef.Scope)
- Non-goals:

## Success Criteria
$successLines

## Stop Conditions
$stopLines

## Plan
$planLines

## Evidence
- Tests:
- Logs:
- Screenshots:
- Diff summary:

### Evidence Checklist
- [ ] Tests link added and pass/fail result recorded.
- [ ] Logs or command output link added.
- [ ] Screenshot or screen recording link added.
- [ ] Diff summary includes impacted files and risk notes.
- [ ] Baseline vs pilot metric delta recorded.

## Review Decision
- Reviewer:
- Decision: pending
- Notes:

## Next Action
- $($presetDef.NextAction)
"@

$card | Set-Content -Path $runCardPath -Encoding UTF8

Write-Host "Created consultant run card: $runCardPath"
Write-Host "Created worktree: $worktreePath"
Write-Host "Branch: $branchName"
Write-Host "Preset: $Preset"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Fill Reviewer field and move to IN PROGRESS"
Write-Host "2. Execute preset plan and collect evidence"
Write-Host "3. Move through IN REVIEW and DONE with close_agent_run.ps1"
