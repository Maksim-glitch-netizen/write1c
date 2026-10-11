[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$skillName = Split-Path -Leaf $sourceRoot
$validator = Join-Path $sourceRoot 'scripts\validate-skill.ps1'

& $validator -SkillRoot $sourceRoot

$skillsRoot = Join-Path $HOME '.agents\skills'
$destination = Join-Path $skillsRoot $skillName

if ([IO.Path]::GetFullPath($destination) -eq $sourceRoot) {
    Write-Output "Скилл уже находится в пользовательском каталоге: $destination"
    exit 0
}

if (Test-Path -LiteralPath $destination) {
    if (-not $Force) {
        throw "Скилл уже установлен: $destination. Для замены запустите .\install.ps1 -Force"
    }
    Remove-Item -LiteralPath $destination -Recurse -Force
}

New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Get-ChildItem -LiteralPath $sourceRoot -Force |
    Copy-Item -Destination $destination -Recurse -Force

& (Join-Path $destination 'scripts\validate-skill.ps1') -SkillRoot $destination

Write-Output "Скилл установлен: $destination"
Write-Output 'Перезапустите Codex, если скилл не появился автоматически.'
Write-Output 'В Codex CLI или IDE выполните /skills или укажите $1c-configurator-batch-8-3-27.'
