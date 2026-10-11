# Обновление конфигурации базы: `/UpdateDBCfg`

## Синтаксис

```text
/UpdateDBCfg
    [-Dynamic-|-Dynamic+|-Dynamic]
    [-BackgroundStart]
    [-BackgroundCancel]
    [-BackgroundFinish [-Visible]]
    [-BackgroundSuspend]
    [-BackgroundResume]
    [-WarningsAsErrors]
    [-Server]
    [-v1|-v2]
    [-Extension <имя>]
    [-SessionTerminate disable|force]
```

## Обычное и динамическое обновление

- `-Dynamic-`: явно запрещает динамическое обновление.
- `-Dynamic+`: сначала выполняется попытка обычного обновления; если она не удалась, разрешается попытка динамического обновления.
- Если `-Dynamic+` отсутствует или указан `-Dynamic` без знака, динамическое обновление также разрешено.

Не утверждай, что отсутствие `-Dynamic-` означает только обычное обновление.

## Расширение

```text
/UpdateDBCfg -Extension "ExtensionName"
```

Без `-Extension` обновляется основная конфигурация базы данных.

## Монопольный доступ

```text
-SessionTerminate disable
-SessionTerminate force
```

- `disable`: не завершать сеансы принудительно, значение по умолчанию.
- `force`: принудительно завершать активные сеансы при необходимости монопольной блокировки. Использовать только при явном разрешении.

## Сервер и механизм реструктуризации

- `-Server`: обновление выполняется на сервере, имеет смысл только для клиент-серверной базы.
- `-v1` или `-v2`: выбор механизма реструктуризации.
- Если версия механизма не указана, используется значение `UpdateDBCfg` из клиентского `conf.cfg`.
- Для фонового обновления выбор `-v1/-v2` игнорируется.
- При `-Server` в фоновом обновлении оптимизированный механизм не используется, `-v2` игнорируется.
- Если выбранный механизм конфликтует с другими параметрами, применяется обычный механизм.

## Предупреждения

`-WarningsAsErrors` трактует все предупреждения как ошибки. Без параметра диагностические сообщения считаются предупреждениями и не блокируют обновление сами по себе.

## Фоновое обновление

```text
/UpdateDBCfg -BackgroundStart
/UpdateDBCfg -BackgroundSuspend
/UpdateDBCfg -BackgroundResume
/UpdateDBCfg -BackgroundCancel
/UpdateDBCfg -BackgroundFinish
```

`-BackgroundFinish -Visible` может показать диалог при невозможности завершения. Для безоператорного запуска не добавляй `-Visible`.

## Разрешенные предшествующие команды

Официальная документация разрешает использовать `/UpdateDBCfg` после:

- `/LoadCfg`;
- `/UpdateCfg`;
- `/ConfigurationRepositoryUpdateCfg`;
- `/LoadConfigFiles`;
- `/LoadConfigFromFiles`;
- перечисленных мобильных команд.

Для задач этого скилла обычно применяй:

```text
/ConfigurationRepositoryUpdateCfg ... /UpdateDBCfg ...
```

или:

```text
/LoadConfigFromFiles ... /UpdateDBCfg ...
```

У каждой команды собственные параметры. Для расширения укажи `-Extension` у обеих операций, не рассчитывай на перенос значения между ними.

Источники: см. `references/10-source-register.md`.
