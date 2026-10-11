[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Query,

    [switch]$Regex,

    [switch]$IncludeSourceRegister,

    [string]$SkillRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SkillRoot)) {
    $SkillRoot = Split-Path -Parent $PSScriptRoot
}
$referenceRoot = Join-Path $SkillRoot 'references'

if (-not (Test-Path -LiteralPath $referenceRoot -PathType Container)) {
    throw "Каталог references не найден: $referenceRoot"
}

$files = Get-ChildItem -LiteralPath $referenceRoot -Filter '*.md' -File |
    Where-Object {
        $_.Name -match '^0[0-9]-.*\.md$' -or
        ($IncludeSourceRegister -and $_.Name -eq '10-source-register.md')
    } |
    Sort-Object Name

if (-not $files) {
    throw "Рабочие справочники не найдены: $referenceRoot"
}

$matches = foreach ($file in $files) {
    if ($Regex) {
        Select-String -LiteralPath $file.FullName -Pattern $Query -Encoding UTF8
    } else {
        Select-String -LiteralPath $file.FullName -Pattern $Query -SimpleMatch -Encoding UTF8
    }
}

if (-not $matches) {
    Write-Output "Совпадений не найдено: $Query"
    exit 1
}

$matches | ForEach-Object {
    [PSCustomObject]@{
        File = $_.Path.Substring($SkillRoot.Length).TrimStart([char[]]@('\', '/'))
        Line = $_.LineNumber
        Text = $_.Line.Trim()
    }
} | Format-Table -AutoSize
