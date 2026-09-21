param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Target = Join-Path $HOME ".config\jcval94-git-hooks"

New-Item -ItemType Directory -Force -Path $Target | Out-Null

$Existing = git config --global --get core.hooksPath 2>$null
if ($Existing -and ($Existing -ne $Target) -and -not $Force) {
    throw "core.hooksPath is already set to '$Existing'. Re-run with -Force only if you want to replace it."
}

Copy-Item (Join-Path $RepoRoot "tools\contribution_gate.py") (Join-Path $Target "contribution_gate.py") -Force
Copy-Item (Join-Path $RepoRoot ".githooks\pre-commit") (Join-Path $Target "pre-commit") -Force
Copy-Item (Join-Path $RepoRoot ".githooks\pre-push") (Join-Path $Target "pre-push") -Force

git config --global core.hooksPath $Target

Write-Host "Installed jcval94 contribution gate globally."
Write-Host "Hooks path: $Target"
python (Join-Path $Target "contribution_gate.py") status
