# Бинарные конфигурации и управляемое объединение

## Команды

```text
/DumpCfg <имя-файла-cf> [-Extension <имя-расширения>]
/LoadCfg <имя-файла-cf> [-Extension <имя-расширения>]
/MergeCfg <имя-cf-или-cfe> -Settings <файл-настроек>
    [-EnableSupport | -DisableSupport]
    [-IncludeObjectsByUnresolvedRefs | -ClearUnresolvedRefs]
    [-Extension <имя-расширения>]
    [-force]
```

- `DumpCfg` выгружает рабочую конфигурацию или расширение в `.cf`/`.cfe`.
- `LoadCfg` полностью загружает конфигурацию или расширение из бинарного файла.
- `MergeCfg` объединяет текущую рабочую конфигурацию с бинарным файлом по XML-настройкам.

`MergeCfg` изменяет рабочую конфигурацию. Обновление конфигурации базы данных является отдельной
операцией и не должно запускаться механически сразу после регистрации минимального каркаса.

## Минимальная структура файла настроек

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Settings xmlns="http://v8.1c.ru/8.3/config/merge/settings"
          version="1.1"
          platformVersion="8.3.27">
    <Parameters>
        <ConfigurationsRelation>ConfigurationsNotRelated</ConfigurationsRelation>
        <AllowMainConfigurationObjectDeletion>false</AllowMainConfigurationObjectDeletion>
        <CopyObjectsMode>false</CopyObjectsMode>
    </Parameters>
    <Objects>
        <Configuration>
            <MergeRule>DoNotMerge</MergeRule>
        </Configuration>
        <Object fullNameInSecondConfiguration="AccumulationRegister.Example_НовыйРегистр">
            <MergeRule>GetFromSecondConfiguration</MergeRule>
        </Object>
        <Object fullNameInSecondConfiguration="Language.Русский">
            <MergeRule>DoNotMerge</MergeRule>
        </Object>
    </Objects>
</Settings>
```

Порядок верхнеуровневых элементов файла значим. Используй namespace из примера.

Для конфигураций без родства применяется `ConfigurationsNotRelated`.
`AllowMainConfigurationObjectDeletion=false` запрещает удаление объектов основной конфигурации.
`CopyObjectsMode=false` сохраняет внутренние идентификаторы переносимого объекта.

Объект, существующий только во второй конфигурации, добавляется, если его правило не равно
`DoNotMerge`. Полное имя во второй конфигурации задается атрибутом
`fullNameInSecondConfiguration`.

## Проектное правило состава

Корневой `Configuration/DoNotMerge` не используется как неявное доказательство, что другие объекты
donor исключены. Генератор проекта перечисляет каждый корневой объект donor:

- целевой новый объект - `GetFromSecondConfiguration`;
- язык и любые другие вспомогательные объекты - `DoNotMerge`.

В настройках должен существовать ровно один переносимый объект для сценария создания одного нового
объекта.

## Неразрешенные ссылки

Если ни один из ключей не указан, при неразрешенных ссылках объединение прерывается и пишет
диагностику в `/Out`. Это безопасное проектное поведение по умолчанию.

- `-IncludeObjectsByUnresolvedRefs` рекурсивно включает связанные отсутствующие объекты и способен
  расширить состав вплоть до всей конфигурации.
- `-ClearUnresolvedRefs` очищает ссылки на объекты, не включенные в объединение.

Оба ключа требуют отдельного явного разрешения и проверки последствий. Не используй их для обхода
ошибки минимального donor.

## Поддержка

Не добавляй `-EnableSupport` или `-DisableSupport` по шаблону. Их допустимость зависит от того,
возможна ли поддержка для объединяемой конфигурации. Неверное наличие или отсутствие ключа приводит
к ошибке. Для расширения сочетание параметра поддержки с `-Extension` завершается ошибкой.

## `-force`

`-force` разрешает применение объединения при определенных предупреждениях. Предупреждения все равно
записываются в `/Out`. В проекте ключ запрещен по умолчанию и применяется только после явного
разрешения пользователя.

## Проверка результата

После каждой операции проверь четыре независимых результата:

1. код процесса;
2. `/DumpResult`;
3. полный `/Out`;
4. фактический результат.

Для `DumpCfg` фактический результат - существующий непустой `.cf`. Для `MergeCfg` в сценарии нового
объекта - повторная XML-выгрузка, где добавлен ровно целевой объект, ничего не удалено и присутствует
XML-файл объекта.

При неопределенном ответе изменяющий `MergeCfg` автоматически не повторять.
