# Проверки конфигурации и расширений

## Проверка модулей

```text
/CheckModules
    [-ThinClient]
    [-WebClient]
    [-MobileClient]
    [-MobileAppClient]
    [-Server]
    [-MobileAppServer]
    [-ExternalConnection]
    [-ThickClientOrdinaryApplication]
    [-ExtendedModulesCheck]
    [-Extension <имя>]
    [-AllExtensions]
```

Нужно указать хотя бы один режим проверки, иначе проверка не выполняется.

Пример для управляемого клиент-серверного приложения:

```text
/CheckModules -ThinClient -Server -ExtendedModulesCheck
```

Не включай режимы механически. Выбирай только среды, реально используемые конфигурацией.

## Централизованная проверка

```text
/CheckConfig <набор-параметров> [-Extension <имя>] [-AllExtensions]
```

Часто применяемые документированные параметры:

- `-ConfigLogIntegrity`: логическая целостность конфигурации;
- `-IncorrectReferences`: поиск неверных ссылок;
- `-ThinClient`, `-Server` и другие режимы синтаксической проверки;
- `-ExtendedModulesCheck`: расширенная проверка модулей.

Пример:

```text
/CheckConfig -ConfigLogIntegrity -IncorrectReferences -ThinClient -Server -ExtendedModulesCheck
```

## Проверка применимости расширения

```text
/CheckCanApplyConfigurationExtensions [-Extension <имя>] [-AllZones] [-Z <разделители>]
```

- С `-Extension`: проверяет указанное расширение с учетом ранее загруженных расширений.
- Без имени расширения проверяются все расширения в порядке загрузки.
- `-Extension` и `-AllZones` несовместимы.
- `-Z` и `-AllZones` несовместимы.

Источники: см. `references/10-source-register.md`.
