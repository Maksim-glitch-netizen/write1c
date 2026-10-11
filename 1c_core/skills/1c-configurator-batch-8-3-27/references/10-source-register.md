# Реестр официальных источников

Дата повторной сверки: 2026-09-17.

## Codex и формат скилла

- OpenAI, Build skills: https://developers.openai.com/codex/skills
- Agent Skills specification: https://agentskills.io/specification

Проверено:

- каталог скилла содержит обязательный `SKILL.md`;
- `SKILL.md` содержит YAML frontmatter с `name` и `description`;
- имя использует строчные латинские буквы, цифры и дефисы и совпадает с именем каталога;
- `scripts/` и `references/` являются допустимыми каталогами;
- ссылки из `SKILL.md` должны быть относительными от корня скилла;
- полное содержимое `SKILL.md` загружается при активации, справочники читаются по необходимости.

## 1С:Предприятие 8.3.27

Официальное руководство администратора 1C International:

1. Общие сведения о пакетном режиме:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.4._Running_Designer_in_batch_mode/7.4.1._General_information/?language=en
2. Подключение к информационной базе:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.3._General_startup_commands/7.3.1._Connection_parameters/?language=en
3. Аутентификация:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.3._General_startup_commands/7.3.2._Authentication_settings/?language=en
4. `/Out`, `/DisableStartupDialogs`, `/DisableStartupMessages`, `/@`:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.3._General_startup_commands/7.3.11._Other_parameters/?language=en
5. Конфигурации и расширения, включая `DumpConfigToFiles`, `LoadConfigFromFiles`, `UpdateDBCfg`:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.4._Running_Designer_in_batch_mode/7.4.4._Configurations_and_extensions/?language=en
6. Проверки конфигурации и расширений:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.4._Running_Designer_in_batch_mode/7.4.5._Configuration_and_extension_checks/?language=en
7. Операции хранилища:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.4._Running_Designer_in_batch_mode/7.4.15._Configuration_repository_operations/?language=en
8. `/DumpResult`:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_7._Startup_command-line_options_of_1C_Enterprise/7.4._Running_Designer_in_batch_mode/7.4.17._Other_parameters/?language=en
9. Файл списка объектов:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_3._Description_and_location_of_internal_files/3.31._Object_list_file/?language=en
10. Файл настроек объединения, общая структура:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_3._Description_and_location_of_internal_files/3.32._A_file_of_merge_settings/3.32.1._General_information/?language=en
11. Элемент `Settings`, параметры и объекты объединения:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_3._Description_and_location_of_internal_files/3.32._A_file_of_merge_settings/3.32.2.__Settings_/?language=en
12. Правила `MergeRule`:
   https://kb.1ci.com/1C_Enterprise_Platform/Guides/Administrator_Guides/1C_Enterprise_8.3.27_Administrator_Guide/Appendix_3._Description_and_location_of_internal_files/3.32._A_file_of_merge_settings/3.32.3._Auxiliary_items/?language=en

## Ограничения достоверности

- Публичная английская страница формата Object list file не отображает схему и примеры. Поэтому скилл не генерирует такой XML по догадке.
- Английское описание `ConfigurationRepositoryUpdateCfg -v` содержит противоречивые фразы для неподключенной конфигурации. Скилл не выводит из них дополнительное правило.
- `DumpConfigToFiles -listFile` в официальной странице объявлен несовместимым с другими параметрами. Скилл применяет консервативное ограничение.
- Документация и тесты скилла подтверждают синтаксис и правила, но не заменяют тестовый запуск на конкретной информационной базе с конкретной сборкой платформы.
- Наличие только корневого `Configuration/DoNotMerge` не используется как предположение об исключении
  всех остальных объектов donor. Проект применяет более строгое правило: каждый вспомогательный
  объект donor явно получает `DoNotMerge`.

## Аудитная копия полного документа

Полный документ, на основании которого выполнено разбиение, сохранен в `references/archive/verified-documentation-full.md`. Он не включен в обычный поисковый маршрут.
