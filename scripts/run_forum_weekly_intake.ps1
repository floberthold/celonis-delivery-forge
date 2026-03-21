param(
    [string]$BaseUrl = "http://127.0.0.1:8000",

    [Parameter(Mandatory = $true)]
    [string]$CreatedBy,

    [Parameter(Mandatory = $true)]
    [string]$ActorId,

    [string]$OwnerId,
    [string]$ReviewerId,
    [string]$Week,

    [string]$Reviewer = "Delivery Forge team",
    [string]$SearchTerms = "MLWB, integration, performance, governance",
    [int]$ThreadsScanned = 10,
    [int]$IdeasAdded = 10,
    [string]$Blockers = "none",

    [switch]$DryRun,
    [switch]$SkipSeed,
    [switch]$SkipLog,
    [switch]$VerifyCount
)

$ErrorActionPreference = "Stop"

if ($ThreadsScanned -lt 0 -or $IdeasAdded -lt 0) {
    throw "ThreadsScanned and IdeasAdded must be >= 0"
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Could not resolve git repository root."
}

$pythonExe = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe"
}

$seedScript = Join-Path $repoRoot "scripts/seed_forum_insights.py"
$logScript = Join-Path $repoRoot "scripts/update_forum_intake_log.py"

if ($Week) {
    $effectiveWeek = $Week
} else {
    $today = Get-Date
    $isoWeek = [System.Globalization.ISOWeek]::GetWeekOfYear($today)
    $isoYear = [System.Globalization.ISOWeek]::GetYear($today)
    $effectiveWeek = "{0}-W{1:D2}" -f $isoYear, $isoWeek
}

if (-not (Test-Path $seedScript)) {
    throw "Missing script: $seedScript"
}
if (-not (Test-Path $logScript)) {
    throw "Missing script: $logScript"
}

$seedArgs = @(
    $seedScript,
    "--base-url", $BaseUrl,
    "--created-by", $CreatedBy,
    "--actor-id", $ActorId
)
if ($OwnerId) {
    $seedArgs += @("--owner-id", $OwnerId)
}
if ($ReviewerId) {
    $seedArgs += @("--reviewer-id", $ReviewerId)
}
if ($Week) {
    $seedArgs += @("--target-week", $Week)
}
if ($DryRun) {
    $seedArgs += "--dry-run"
}

$logArgs = @(
    $logScript,
    "--reviewer", $Reviewer,
    "--search-terms", $SearchTerms,
    "--threads-scanned", $ThreadsScanned,
    "--ideas-added", $IdeasAdded,
    "--blockers", $Blockers
)
if ($Week) {
    $logArgs += @("--week", $Week)
}
if ($DryRun) {
    $logArgs += "--dry-run"
}

if (-not $SkipSeed) {
    Write-Host "Running seed_forum_insights.py ..."
    & $pythonExe @seedArgs
}

if (-not $SkipLog) {
    Write-Host "Running update_forum_intake_log.py ..."
    & $pythonExe @logArgs
}

if ($VerifyCount) {
    if ($DryRun) {
        Write-Host "VerifyCount skipped because DryRun is enabled."
    } else {
        Write-Host "Running weekly count verification for $effectiveWeek ..."
        $verifyUrl = "$($BaseUrl.TrimEnd('/'))/forum-insights/?target_week=$effectiveWeek"
        $records = Invoke-RestMethod -Method Get -Uri $verifyUrl
        $actualCount = @($records).Count
        if ($actualCount -ne $IdeasAdded) {
            Write-Warning "Weekly count mismatch for $effectiveWeek. Expected IdeasAdded=$IdeasAdded but API returned $actualCount records."
        } else {
            Write-Host "Weekly count verification passed for $effectiveWeek ($actualCount records)."
        }
    }
}

Write-Host "Forum weekly intake workflow completed."