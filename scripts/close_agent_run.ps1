param(
    [Parameter(Mandatory = $true)]
    [string]$RunCard,

    [Parameter(Mandatory = $true)]
    [ValidateSet("IN REVIEW", "DONE")]
    [string]$Status
)

$ErrorActionPreference = "Stop"

function Get-CardContent {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Run card not found: $Path"
    }
    return Get-Content -Path $Path -Raw
}

function Get-FieldValue {
    param(
        [string]$Content,
        [string]$Name
    )

    $pattern = "(?m)^" + [regex]::Escape($Name) + ":\s*(.+)$"
    $match = [regex]::Match($Content, $pattern)
    if (-not $match.Success) {
        return ""
    }
    return $match.Groups[1].Value.Trim()
}

function Set-FieldValue {
    param(
        [string]$Content,
        [string]$Name,
        [string]$Value
    )

    $pattern = "(?m)^(" + [regex]::Escape($Name) + ":\s*).*$"
    if ([regex]::IsMatch($Content, $pattern)) {
        return [regex]::Replace($Content, $pattern, ('$1' + $Value), 1)
    }

    $createdPattern = "(?m)^created_at:\s*.+$"
    if ([regex]::IsMatch($Content, $createdPattern)) {
        return [regex]::Replace($Content, $createdPattern, ('$0' + [Environment]::NewLine + $Name + ': ' + $Value), 1)
    }

    return ($Name + ': ' + $Value + [Environment]::NewLine + $Content)
}

function Get-BulletValue {
    param(
        [string]$Content,
        [string]$Label
    )

    $pattern = "(?m)^-\s*" + [regex]::Escape($Label) + ":\s*(.*)$"
    $match = [regex]::Match($Content, $pattern)
    if (-not $match.Success) {
        return ""
    }
    return $match.Groups[1].Value.Trim()
}

function Ensure-EvidenceForReview {
    param([string]$Content)

    $required = @("Tests", "Logs", "Screenshots", "Diff summary")
    foreach ($label in $required) {
        $value = Get-BulletValue -Content $Content -Label $label
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "Cannot move to IN REVIEW. Missing evidence: $label"
        }
    }
}

function Ensure-DecisionForDone {
    param([string]$Content)

    $reviewer = Get-BulletValue -Content $Content -Label "Reviewer"
    $decision = Get-BulletValue -Content $Content -Label "Decision"
    if ([string]::IsNullOrWhiteSpace($reviewer)) {
        throw "Cannot move to DONE. Missing review decision reviewer."
    }
    if ([string]::IsNullOrWhiteSpace($decision)) {
        throw "Cannot move to DONE. Missing review decision result."
    }

    $normalizedDecision = $decision.ToLowerInvariant()
    if ($normalizedDecision -notin @("approve", "approved")) {
        throw "Cannot move to DONE. Decision must be 'approve' or 'approved'."
    }
}

$fullPath = Resolve-Path -Path $RunCard
$content = Get-CardContent -Path $fullPath
$currentStatus = Get-FieldValue -Content $content -Name "status"
if ([string]::IsNullOrWhiteSpace($currentStatus)) {
    throw "Run card is missing required field: status"
}

if ($Status -eq "IN REVIEW") {
    if ($currentStatus -notin @("TODO", "IN PROGRESS")) {
        throw "Invalid transition: $currentStatus -> IN REVIEW"
    }
    Ensure-EvidenceForReview -Content $content
}

if ($Status -eq "DONE") {
    if ($currentStatus -ne "IN REVIEW") {
        throw "Invalid transition: $currentStatus -> DONE"
    }
    Ensure-EvidenceForReview -Content $content
    Ensure-DecisionForDone -Content $content
}

$updatedAtUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$content = Set-FieldValue -Content $content -Name "status" -Value $Status
$content = Set-FieldValue -Content $content -Name "updated_at" -Value $updatedAtUtc

Set-Content -Path $fullPath -Value $content -Encoding UTF8

Write-Host "Updated run card: $fullPath"
Write-Host "Status: $currentStatus -> $Status"
Write-Host "updated_at: $updatedAtUtc"
