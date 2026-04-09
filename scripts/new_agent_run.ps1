param(
    [Parameter(Mandatory = $true)]
    [string]$TaskId,

    [Parameter(Mandatory = $true)]
    [string]$Title,

    [string]$Agent = "codex",
    [string]$Lane = "default",
    [string]$Owner = "TBD",
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

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Could not resolve git repository root."
}

$slug = Get-Slug -Text "$TaskId-$Title"
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

$card = @"
# Agent Run Card

run_id: $runId
status: TODO
created_at: $createdAtUtc
owner: $Owner
agent: $Agent
lane: $Lane
base_branch: $BaseBranch
run_branch: $branchName
worktree_path: $worktreePath

## Task
- Title: $Title
- Scope:
- Non-goals:

## Success Criteria
- 

## Stop Conditions
- 

## Plan
1. 
2. 
3. 

## Evidence
- Tests:
- Logs:
- Screenshots:
- Diff summary:

## Review Decision
- Reviewer:
- Decision:
- Notes:

## Next Action
- 
"@

$card | Set-Content -Path $runCardPath -Encoding UTF8

Write-Host "Created run card: $runCardPath"
Write-Host "Created worktree: $worktreePath"
Write-Host "Branch: $branchName"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Open worktree and implement the scoped task"
Write-Host "2. Fill evidence section in the run card"
Write-Host "3. Move status to IN REVIEW when ready for human decision"
