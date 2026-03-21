param(
    [string]$Status,
    [switch]$Json,
    [switch]$Detailed,
    [switch]$Summary
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = (git rev-parse --show-toplevel).Trim()
    if (-not $root) {
        throw "Could not resolve git repository root."
    }
    return $root
}

function Get-FrontMatterValue {
    param(
        [string]$Content,
        [string]$Field
    )

    $pattern = "(?m)^" + [regex]::Escape($Field) + ":\s*(.+)$"
    $match = [regex]::Match($Content, $pattern)
    if (-not $match.Success) {
        return ""
    }
    return $match.Groups[1].Value.Trim()
}

function Read-RunCard {
    param([string]$Path)

    $raw = Get-Content -Path $Path -Raw
    return [PSCustomObject]@{
        run_id = Get-FrontMatterValue -Content $raw -Field "run_id"
        status = Get-FrontMatterValue -Content $raw -Field "status"
        owner = Get-FrontMatterValue -Content $raw -Field "owner"
        agent = Get-FrontMatterValue -Content $raw -Field "agent"
        lane = Get-FrontMatterValue -Content $raw -Field "lane"
        created_at = Get-FrontMatterValue -Content $raw -Field "created_at"
        updated_at = Get-FrontMatterValue -Content $raw -Field "updated_at"
        base_branch = Get-FrontMatterValue -Content $raw -Field "base_branch"
        run_branch = Get-FrontMatterValue -Content $raw -Field "run_branch"
        worktree_path = Get-FrontMatterValue -Content $raw -Field "worktree_path"
        card_path = $Path
    }
}

function Get-RunSummary {
    param([array]$Runs)

    $total = $Runs.Count
    $byStatus = @()

    if ($total -gt 0) {
        $byStatus = $Runs |
            Group-Object -Property status |
            Sort-Object Name |
            ForEach-Object {
                [PSCustomObject]@{
                    status = $_.Name
                    count = $_.Count
                    percent = [math]::Round((($_.Count * 100.0) / $total), 1)
                }
            }
    }

    return [PSCustomObject]@{
        total = $total
        by_status = $byStatus
    }
}

$repoRoot = Get-RepoRoot
$runsDir = Join-Path $repoRoot ".orchestration/runs"

if (-not (Test-Path $runsDir)) {
    Write-Output "No runs directory found at $runsDir"
    exit 0
}

$cards = Get-ChildItem -Path $runsDir -Filter "*.md" -File | Sort-Object Name
if (-not $cards -or $cards.Count -eq 0) {
    Write-Output "No run cards found in $runsDir"
    exit 0
}

$runs = @()
foreach ($card in $cards) {
    $runs += Read-RunCard -Path $card.FullName
}

if (-not [string]::IsNullOrWhiteSpace($Status)) {
    $statusNorm = $Status.Trim().ToUpperInvariant()
    $runs = $runs | Where-Object { ($_.status).ToUpperInvariant() -eq $statusNorm }
}

if ($runs.Count -eq 0) {
    if ($Json -and $Summary) {
        Get-RunSummary -Runs $runs | ConvertTo-Json -Depth 5
        exit 0
    }

    if ($Json) {
        $runs | ConvertTo-Json -Depth 4
        exit 0
    }

    Write-Output "No runs match the provided filters."
    exit 0
}

if ($Summary) {
    $summaryResult = Get-RunSummary -Runs $runs

    if ($Json) {
        $summaryResult | ConvertTo-Json -Depth 5
        exit 0
    }

    Write-Output "Total runs: $($summaryResult.total)"
    $summaryResult.by_status | Format-Table status, count, percent -AutoSize
    exit 0
}

if ($Json) {
    $runs | ConvertTo-Json -Depth 4
    exit 0
}

if ($Detailed) {
    $runs |
        Sort-Object status, updated_at, created_at |
        Format-Table run_id, status, owner, agent, lane, base_branch, run_branch, created_at, updated_at, worktree_path, card_path -AutoSize
    exit 0
}

$runs |
    Sort-Object status, updated_at, created_at |
    Format-Table run_id, status, owner, agent, lane, run_branch, updated_at -AutoSize
