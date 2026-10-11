# Рабочий процесс нового корневого объекта

## Структура задачи

Внутри существующей папки задачи создай отдельный каталог:

```text
new-object-merge\
    manifest.json
    baseline\
        Configuration.xml
    input\
        object.json
    donor-src\
    donor-db\
    artifacts\
        MergeSettings.xml
        donor.cf
        donor-objects.json
    verification\
```

Журналы каждого Designer-процесса остаются в обязательном каталоге задачи `DESIGNERlogs`.
Не помещай `donor.cf` и файловую ИБ в `1c_core` или `components`.

## Подготовка

```powershell
python "<skill>\scripts\new_object_workflow.py" prepare `
  --type AccumulationRegister `
  --name Example_НовыйРегистр `
  --baseline-configuration "<PROJECT_ROOT>\1c_works_files\components\main\src\Configuration.xml" `
  --workspace "<папка-задачи>\new-object-merge"
```

Команда завершится ошибкой, если объект уже зарегистрирован, тип не поддерживается или рабочий
каталог уже содержит файлы. Существующее содержимое не удаляется и не перезаписывается.
До создания остальных артефактов команда сохраняет неизменяемый снимок входного
`Configuration.xml` в `baseline\Configuration.xml` и его SHA-256 в manifest. Поэтому повторная
выгрузка в исходный каталог не меняет базу сравнения. `finalize` и `verify-main` останавливаются,
если снимок отсутствует или его SHA-256 изменился.

Затем:

1. `cf-init` создает пустую donor-конфигурацию в `donor-src` с `FormatVersion=2.20` и
   `CompatibilityMode=Version8_3_27`.
2. `meta-compile` читает `input/object.json` и создает минимальный объект в `donor-src`.
   Для `AccumulationRegister` JSON уже содержит вспомогательный donor-only документ-регистратор.
   Он нужен только для проверки целостности и сборки `donor.cf`. Регистр также получает технические
   измерение `Example_DonorDimension` и ресурс `Example_DonorResource`, иначе платформа отвергает пустой
   регистр.
3. `meta-validate` проверяет объект, `cf-validate` - конфигурацию donor.

После проверок:

```powershell
python "<skill>\scripts\new_object_workflow.py" finalize `
  --manifest "<workspace>\manifest.json"
```

`finalize` сканирует donor `Configuration.xml`. Целевой объект получает
`GetFromSecondConfiguration`, все остальные объекты donor - явное `DoNotMerge`.

## Сборка donor.cf

Создай новую файловую ИБ в `donor-db`. Не используй `-AddToList` и не обновляй ее конфигурацию БД.
Для точных сочетаний ключей сначала используй проверенный рецепт проекта
`docs/verified-1c-commands/add-new-object-merge-isolated.md`, затем справочник
`1c-configurator-batch-8-3-27/references/11-merge-cfg.md`.

Последовательно, одним Designer-процессом на операцию:

```text
/F "<workspace>\donor-db"
/LoadConfigFromFiles "<workspace>\donor-src"
```

```text
/F "<workspace>\donor-db"
/DumpCfg "<workspace>\artifacts\donor.cf"
```

Каждая команда обязана содержать `/DisableStartupDialogs`, `/DisableStartupMessages`, отдельные
`/Out` и `/DumpResult`. После каждой операции проверь код процесса, `/DumpResult`, `/Out` и
фактический результат.

## Объединение с DEV

Базовая операция:

```text
/S "<SERVER>\<INFOBASE>"
/WA+
/MergeCfg "<workspace>\artifacts\donor.cf" -Settings "<workspace>\artifacts\MergeSettings.xml"
```

Не добавляй механически параметры поддержки. `-EnableSupport` или `-DisableSupport` выбираются только
после определения фактического режима поддержки и по правилам `1c-configurator-batch-8-3-27`.

По умолчанию запрещены:

- `-force` - продолжение при определенных предупреждениях;
- `-ClearUnresolvedRefs` - очистка неразрешенных ссылок;
- `-IncludeObjectsByUnresolvedRefs` - автоматическое расширение состава merge.

После успешного merge не выполняй `UpdateDBCfg`. Сначала повторно выгрузи рабочую конфигурацию DEV в
тот же актуальный XML-каталог. Если `ConfigDumpInfo.xml` соответствует свежему baseline, используй
инкрементальную выгрузку по проверенному рецепту проекта.

## Проверка после merge

```powershell
python "<skill>\scripts\new_object_workflow.py" verify-main `
  --manifest "<workspace>\manifest.json" `
  --current-source "<PROJECT_ROOT>\1c_works_files\components\main\src"
```

Проверка требует одновременно:

- объект отсутствовал в сохраненном снимке baseline;
- теперь присутствует в `Configuration.xml`;
- файл объекта находится в ожидаемом каталоге;
- добавлен ровно один корневой объект - целевой;
- ни один корневой объект baseline не удален.

После этого donor считается только механизмом регистрации. Дальнейшая разработка выполняется в
свежем XML основной конфигурации.

## Проверка перед UpdateDBCfg

После замены каркаса реальными реквизитами и зависимостями выполни:

```powershell
python "<skill>\scripts\new_object_workflow.py" verify-ready `
  --manifest "<workspace>\manifest.json" `
  --current-source "<PROJECT_ROOT>\1c_works_files\components\main\src"
```

Для регистра накопления команда проверит отсутствие технических `Example_DonorDimension` и
`Example_DonorResource`, а также наличие реального документа-регистратора. После нее обязательны
`meta-validate` и `cf-validate`. Только затем разрешен `UpdateDBCfg`.

## Обязательные ссылки

Упрощенный donor применим, когда минимальный объект самодостаточен либо skill знает безопасный
donor-only объект целостности. Для `AccumulationRegister` таким объектом является автоматически
созданный документ-регистратор. Он получает `DoNotMerge`; контрольная выгрузка должна подтвердить,
что документ не появился в основной конфигурации.

Технические `Example_DonorDimension` и `Example_DonorResource` переносятся вместе с регистром. Сразу после
контрольной выгрузки замени их реальными измерениями и ресурсами или удали. До этого `UpdateDBCfg`
запрещен. Точный список хранится в manifest `bootstrapMembersToReplace`.

Не включай в каркас ссылки на объекты УХ, обработчики, владельцев, планы счетов или планы видов
расчета.

Если тип требует обязательную внешнюю ссылку уже при создании, например регистр бухгалтерии требует
план счетов, упрощенный donor не является универсально безопасным. Остановись и подготовь отдельный
проверенный сценарий с donor на базе свежей конфигурации. Не создавай фиктивную зависимость и не
очищай ссылку.

## Восстановление после ошибки

Не выполняй `RollbackCfg`, повторный `MergeCfg` или удаление объекта автоматически. Зафиксируй
команду и результат в журнале задачи и запроси решение пользователя. Повтор изменяющей операции
после неопределенного ответа запрещен.
