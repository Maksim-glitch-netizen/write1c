# Результаты и ошибки

## Собирай четыре результата

После каждого запуска проверяй независимо:

1. код завершения процесса `1cv8.exe`;
2. содержимое `/DumpResult`;
3. содержимое `/Out`;
4. фактический ожидаемый результат операции.

Нулевой показатель без ожидаемого файла или изменения состояния недостаточен для объявления успеха.

## Документированные коды

- Для работы с расширениями в пакетном режиме: `0` при успехе, `1` при ошибке.
- `ConfigurationRepositoryLock`, `ConfigurationRepositoryUnLock`, `ConfigurationRepositoryCommit`: `0` без ошибок, `1` при ошибках; текст ошибки в файле служебных сообщений.
- `DumpConfigFiles` и `LoadConfigFiles`: `0` успех, `1` ошибка, `101` данные содержат ошибки.
- `/DumpResult`: официальный источник указывает числовой результат; `0` является успешным значением. При другом значении анализируй `/Out`.

Не переносить код `101` на `DumpConfigToFiles`, `LoadConfigFromFiles`, `UpdateDBCfg` или другие команды без отдельного официального подтверждения.

## PowerShell-проверка

```powershell
$OneC = '<PLATFORM_EXECUTABLE>'
$Log = '<WORK_DIRECTORY>\logs\operation.log'
$Result = '<WORK_DIRECTORY>\logs\operation.result'

Remove-Item -LiteralPath $Log, $Result -Force -ErrorAction SilentlyContinue

& $OneC DESIGNER `
    /S '<SERVER>\<INFOBASE>' `
    /WA+ `
    /DisableStartupDialogs `
    /DisableStartupMessages `
    /Out $Log `
    /DumpResult $Result `
    <ПАКЕТНАЯ_КОМАНДА>

$ExitCode = $LASTEXITCODE
$DesignerResult = if (Test-Path -LiteralPath $Result) {
    ([IO.File]::ReadAllText($Result)).Trim()
} else {
    $null
}

if ($ExitCode -ne 0 -or $DesignerResult -ne '0') {
    $LogText = if (Test-Path -LiteralPath $Log) {
        [IO.File]::ReadAllText($Log)
    } else {
        '<лог не создан>'
    }
    throw "Пакетная операция завершилась ошибкой. ExitCode=$ExitCode; DumpResult=$DesignerResult`n$LogText"
}
```

После этого отдельно проверь ожидаемый файл, каталог, изменение конфигурации или состояние хранилища.

## Типовые действия

- Родительского каталога нет: создать его до запуска.
- Открылся диалог: проверить `/F` или `/S`, аутентификацию, реквизиты хранилища и `/DisableStartupDialogs`.
- `DumpConfigToFiles -update` не находит `ConfigDumpInfo.xml`: выполнить полную выгрузку в чистый каталог.
- Версия формата выгрузки не совпадает: выполнить чистую полную выгрузку; `-update -force` использовать только осознанно.
- Одновременно указаны `-Extension` и `-AllExtensions`: остановить запуск, комбинация не поддерживается.
- Полная загрузка расширения, подключенного к хранилищу: перейти к частичной загрузке захваченных объектов или использовать другой документированный процесс.
- Нет монопольного доступа для `UpdateDBCfg`: анализировать сеансы и `/Out`; `-SessionTerminate force` только по явному разрешению.
- `ConfigurationRepositoryUpdateCfg` не добавил или не удалил объекты: проверить `/Out` и необходимость `-force`.
- `ConfigurationRepositoryUnLock -force`: до запуска подтвердить допустимость потери локальных изменений.
- Модуль закрыт паролем: пакетный режим его игнорирует и формирует диагностическое сообщение; учитывать неполноту проверки.

Никогда не придумывай универсальный текст ошибки. Используй фактический `/Out`.

Источники: см. `references/10-source-register.md`.
