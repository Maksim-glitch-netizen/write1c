[CmdletBinding()]
param(
    [string]$SkillRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SkillRoot)) {
    $SkillRoot = Split-Path -Parent $PSScriptRoot
}
$errors = New-Object System.Collections.Generic.List[string]

function Add-ValidationError {
    param([string]$Message)
    $errors.Add($Message)
}

$skillRootPath = [IO.Path]::GetFullPath($SkillRoot)
$skillPath = Join-Path $skillRootPath 'SKILL.md'

if (-not (Test-Path -LiteralPath $skillPath -PathType Leaf)) {
    throw "SKILL.md не найден: $skillPath"
}

$utf8 = New-Object Text.UTF8Encoding($false, $true)
try {
    $text = [IO.File]::ReadAllText($skillPath, $utf8)
} catch {
    throw "SKILL.md не является корректным UTF-8: $($_.Exception.Message)"
}

$frontmatterMatch = [regex]::Match(
    $text,
    '\A---\r?\n(?<yaml>.*?)\r?\n---(?:\r?\n|\z)',
    [Text.RegularExpressions.RegexOptions]::Singleline
)

if (-not $frontmatterMatch.Success) {
    Add-ValidationError 'SKILL.md не содержит корректный YAML frontmatter.'
} else {
    $yaml = $frontmatterMatch.Groups['yaml'].Value
    $nameMatch = [regex]::Match($yaml, '(?m)^name:\s*(?<value>[^\r\n]+)\s*$')
    $descriptionMatch = [regex]::Match($yaml, '(?m)^description:\s*(?<value>[^\r\n]+)\s*$')
    $frontmatterKeys = [regex]::Matches($yaml, '(?m)^(?<key>[A-Za-z][A-Za-z0-9_-]*):') |
        ForEach-Object { $_.Groups['key'].Value }

    foreach ($unexpectedKey in ($frontmatterKeys | Where-Object { $_ -notin @('name', 'description') })) {
        Add-ValidationError "Недопустимое поле frontmatter: $unexpectedKey"
    }

    if (-not $nameMatch.Success) {
        Add-ValidationError 'В frontmatter отсутствует name.'
    } else {
        $name = $nameMatch.Groups['value'].Value.Trim().Trim([char[]]@('"', "'"))
        $directoryName = Split-Path -Leaf $skillRootPath
        if ($name.Length -lt 1 -or $name.Length -gt 64) {
            Add-ValidationError 'Длина name должна быть от 1 до 64 символов.'
        }
        if ($name -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
            Add-ValidationError 'name должен содержать только строчные латинские буквы, цифры и одиночные дефисы.'
        }
        if ($name -ne $directoryName) {
            Add-ValidationError "name '$name' не совпадает с именем каталога '$directoryName'."
        }
    }

    if (-not $descriptionMatch.Success) {
        Add-ValidationError 'В frontmatter отсутствует description.'
    } else {
        $description = $descriptionMatch.Groups['value'].Value.Trim().Trim([char[]]@('"', "'"))
        if ($description.Length -lt 1 -or $description.Length -gt 1024) {
            Add-ValidationError 'Длина description должна быть от 1 до 1024 символов.'
        }
    }
}

$skillLines = [regex]::Split($text, '\r?\n').Count
if ($skillLines -gt 500) {
    Add-ValidationError "SKILL.md содержит $skillLines строк, рекомендуется не более 500."
}

$allTextFiles = Get-ChildItem -LiteralPath $skillRootPath -Recurse -File |
    Where-Object { $_.Extension -in '.md', '.ps1', '.json', '.txt' }

foreach ($file in $allTextFiles) {
    try {
        $content = [IO.File]::ReadAllText($file.FullName, $utf8)
    } catch {
        Add-ValidationError "Некорректный UTF-8: $($file.FullName)"
        continue
    }
    if ($content -match '[\u2010\u2011\u2012\u2013\u2014\u2212]') {
        Add-ValidationError "Найден Unicode-дефис или тире: $($file.FullName)"
    }
}

$linkMatches = [regex]::Matches($text, '\[[^\]]+\]\((?<path>[^)]+)\)')
foreach ($match in $linkMatches) {
    $relativePath = $match.Groups['path'].Value
    if ($relativePath -match '^(?:https?://|#)') { continue }
    $relativePath = $relativePath.Split('#')[0]
    $target = Join-Path $skillRootPath $relativePath
    if (-not (Test-Path -LiteralPath $target)) {
        Add-ValidationError "Не найдена ссылка из SKILL.md: $relativePath"
    }
}

$required = @(
    'references\00-index.md',
    'references\01-common-cli.md',
    'references\02-xml-dump.md',
    'references\03-xml-load.md',
    'references\04-repository-read-bind.md',
    'references\05-repository-write.md',
    'references\06-update-db-cfg.md',
    'references\07-checks.md',
    'references\08-results-errors.md',
    'references\09-workflows.md',
    'references\10-source-register.md',
    'references\11-merge-cfg.md',
    'references\archive\verified-documentation-full.md',
    'scripts\search-docs.ps1',
    'manifest.json'
)

foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $skillRootPath $relative) -PathType Leaf)) {
        Add-ValidationError "Отсутствует обязательный файл: $relative"
    }
}

$criticalRules = @(
    @{ File = 'references\02-xml-dump.md'; Text = '`-listFile` нельзя использовать с другими параметрами этой команды' },
    @{ File = 'references\03-xml-load.md'; Text = 'Если расширение подключено к хранилищу, полностью загрузить его нельзя' },
    @{ File = 'references\04-repository-read-bind.md'; Text = 'нет документированного ключа `-update`' },
    @{ File = 'references\05-repository-write.md'; Text = 'не должен генерировать содержимое такого файла по догадке' },
    @{ File = 'references\06-update-db-cfg.md'; Text = '-SessionTerminate force' },
    @{ File = 'references\08-results-errors.md'; Text = 'Не переносить код `101`' },
    @{ File = 'references\11-merge-cfg.md'; Text = '`-ClearUnresolvedRefs` очищает ссылки' },
    @{ File = 'references\11-merge-cfg.md'; Text = 'При неопределенном ответе изменяющий `MergeCfg` автоматически не повторять' }
)

foreach ($rule in $criticalRules) {
    $rulePath = Join-Path $skillRootPath $rule.File
    if (Test-Path -LiteralPath $rulePath -PathType Leaf) {
        $ruleText = [IO.File]::ReadAllText($rulePath, $utf8)
        if (-not $ruleText.Contains($rule.Text)) {
            Add-ValidationError "Не найдено критическое правило: $($rule.Text)"
        }
    }
}

$manifestPath = Join-Path $skillRootPath 'manifest.json'
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    try {
        $manifest = [IO.File]::ReadAllText($manifestPath, $utf8) | ConvertFrom-Json
        foreach ($property in $manifest.files.PSObject.Properties) {
            $relative = $property.Name.Replace([char]'/', [IO.Path]::DirectorySeparatorChar)
            $expected = $property.Value
            $target = Join-Path $skillRootPath $relative
            if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
                Add-ValidationError "Файл из manifest.json отсутствует: $relative"
                continue
            }
            $actualBytes = (Get-Item -LiteralPath $target).Length
            $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actualBytes -ne [long]$expected.bytes) {
                Add-ValidationError "Размер файла не совпадает с manifest.json: $relative"
            }
            if ($actualHash -ne [string]$expected.sha256) {
                Add-ValidationError "SHA-256 файла не совпадает с manifest.json: $relative"
            }
        }
    } catch {
        Add-ValidationError "Не удалось проверить manifest.json: $($_.Exception.Message)"
    }
}

if ($errors.Count -gt 0) {
    $message = "Проверка скилла завершилась ошибками:`n - " + ($errors -join "`n - ")
    throw $message
}

Write-Output 'OK: структура, критические правила и контрольные суммы скилла проверены.'
Write-Output "SkillRoot: $skillRootPath"
Write-Output "SKILL.md lines: $skillLines"
