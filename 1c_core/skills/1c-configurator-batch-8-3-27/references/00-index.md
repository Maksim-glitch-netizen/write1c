# Индекс операций

Открывай только файлы, нужные для текущей задачи.

| Задача | Обязательные справочники |
|---|---|
| Базовая строка, `/F`, `/S`, `/N`, `/P`, `/WA`, `/Out`, `/DumpResult` | `references/01-common-cli.md`, `references/08-results-errors.md` |
| Полная или инкрементальная XML-выгрузка | `references/01-common-cli.md`, `references/02-xml-dump.md`, `references/08-results-errors.md` |
| Полная или частичная XML-загрузка | `references/01-common-cli.md`, `references/03-xml-load.md`, `references/08-results-errors.md` |
| Подключение или получение из хранилища | `references/01-common-cli.md`, `references/04-repository-read-bind.md`, `references/08-results-errors.md` |
| Захват, помещение, отмена захвата | `references/01-common-cli.md`, `references/05-repository-write.md`, `references/08-results-errors.md` |
| Обновление конфигурации базы | `references/01-common-cli.md`, `references/06-update-db-cfg.md`, `references/08-results-errors.md` |
| Проверка конфигурации или расширения | `references/01-common-cli.md`, `references/07-checks.md`, `references/08-results-errors.md` |
| `DumpCfg`, `LoadCfg`, `MergeCfg` и файл настроек объединения | `references/01-common-cli.md`, `references/11-merge-cfg.md`, `references/08-results-errors.md` |
| Готовый рабочий цикл | `references/09-workflows.md` и перечисленные в нем справочники |
| Проверка официальных источников | `references/10-source-register.md` |

## Различай три вида списков

1. `DumpConfigToFiles -listFile`: список объектов для XML-выгрузки. У параметра есть особые ограничения в `02-xml-dump.md`.
2. `LoadConfigFromFiles -listFile`: UTF-8 файл с путями XML-файлов, по одному пути на строку.
3. Операции хранилища `-Objects`: официальный XML-файл списка объектов. Это не текстовый список XML-путей.

Никогда не заменяй один формат другим.

## Аудитный архив

`references/archive/verified-documentation-full.md` хранит полный исходный документ. Не открывай его целиком при обычной работе. Используй только для аудита или поиска недостающего контекста; при противоречии приоритет имеют модульные правила `00`-`11`.
