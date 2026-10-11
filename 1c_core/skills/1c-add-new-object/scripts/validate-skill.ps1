[CmdletBinding()]
param(
    [string]$SkillRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SkillRoot)) {
    $SkillRoot = Split-Path -Parent $PSScriptRoot
}
$root = [IO.Path]::GetFullPath($SkillRoot)
$utf8 = New-Object Text.UTF8Encoding($false, $true)
$required = @(
    'SKILL.md',
    'references\workflow.md',
    'references\tooling.md',
    'scripts\new_object_workflow.py',
    'scripts\validate-skill.ps1',
    'tests\test_new_object_workflow.py'
)

foreach ($relative in $required) {
    $path = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Отсутствует обязательный файл: $relative"
    }
}

$skillPath = Join-Path $root 'SKILL.md'
$skillText = [IO.File]::ReadAllText($skillPath, $utf8)
$frontmatter = [regex]::Match(
    $skillText,
    '\A---\r?\n(?<yaml>.*?)\r?\n---(?:\r?\n|\z)',
    [Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $frontmatter.Success) {
    throw 'SKILL.md не содержит корректный YAML frontmatter.'
}
$yaml = $frontmatter.Groups['yaml'].Value
$keys = [regex]::Matches($yaml, '(?m)^(?<key>[A-Za-z][A-Za-z0-9_-]*):') |
    ForEach-Object { $_.Groups['key'].Value }
if (($keys | Where-Object { $_ -notin @('name', 'description') }).Count -gt 0) {
    throw 'В YAML frontmatter разрешены только name и description.'
}
if ($yaml -notmatch '(?m)^name:\s*1c-add-new-object\s*$') {
    throw 'Некорректное имя skill в YAML frontmatter.'
}
if ((Split-Path -Leaf $root) -ne '1c-add-new-object') {
    throw 'Имя каталога skill не совпадает с name.'
}
if ($yaml -notmatch '(?m)^description:\s*(?<value>\S.*)$') {
    throw 'В YAML frontmatter отсутствует description.'
}
$description = $Matches['value'].Trim().Trim([char[]]@('"', "'"))
if ($description.Length -gt 1024) {
    throw 'Description превышает 1024 символа.'
}

Get-ChildItem -LiteralPath $root -Recurse -File |
    Where-Object { $_.Extension -in '.md', '.ps1', '.py', '.json' } |
    ForEach-Object {
        try {
            [void][IO.File]::ReadAllText($_.FullName, $utf8)
        } catch {
            throw "Файл не является корректным UTF-8: $($_.FullName)"
        }
    }

[regex]::Matches($skillText, '\[[^\]]+\]\((?<path>[^)]+)\)') | ForEach-Object {
    $relative = $_.Groups['path'].Value.Split('#')[0]
    if ($relative -and $relative -notmatch '^(?:https?://|#)') {
        $target = Join-Path $root $relative
        if (-not (Test-Path -LiteralPath $target)) {
            throw "Не найдена локальная ссылка из SKILL.md: $relative"
        }
    }
}

$python = Get-Command python -ErrorAction Stop
$testsPath = Join-Path $root 'tests'

& $python.Source -B -m unittest discover -s $testsPath -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) {
    throw "Unit tests завершились с кодом $LASTEXITCODE"
}

Write-Output 'OK: структура skill, Python-синтаксис и unit tests проверены.'
Write-Output "SkillRoot: $root"
