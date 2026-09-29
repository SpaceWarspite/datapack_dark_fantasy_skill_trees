# Dark Fantasy Skill Trees

Контентный мод-аддон для **Passive Skill Tree** под **Minecraft 1.21.1 / NeoForge**.

Мод добавляет дополнительные тематические деревья прокачки в стиле Dark Fantasy и распространяет игровые данные и клиентские ресурсы в одном `.jar`-файле.

Текущая версия: **0.1.0**

## Что добавляет мод

На данный момент доступны два дополнительных дерева:

- **Warrior** — дерево боевой специализации;
- **Mage** — дерево магической специализации с интеграцией Iron's Spells 'n Spellbooks.

Текущая версия содержит:

- 61 узел Warrior;
- 61 узел Mage;
- 122 узла навыков всего;
- собственные связи и геометрию деревьев;
- requirements для части навыков;
- специализации и ограничения выбора через `tags` / `skillLimitations`;
- русскую и английскую локализацию;
- собственные иконки выбора деревьев.

## Как это работает

Проект является **NeoForge low-code content mod**.

Java-код для текущей версии не требуется. Passive Skill Tree остаётся движком деревьев навыков, а Dark Fantasy Skill Trees поставляет ему JSON-данные и клиентские ресурсы.

В одном JAR находятся одновременно:

```text
data/darkfantasy/
├── skill_trees/
└── skills/

assets/darkfantasy/
├── lang/
└── textures/
```

`data/` используется как datapack-часть мода, а `assets/` — как resource-pack-часть.

Отдельная установка datapack, resource pack или Moonlight Global Datapacks больше не требуется.

## Зависимости

Обязательные:

- Minecraft **1.21.1**
- NeoForge
- Passive Skill Tree (`skilltree`)
- Iron's Spells 'n Spellbooks (`irons_spellbooks`)

Первая рабочая версия проверена в сборке с:

- NeoForge **21.1.235**
- Passive Skill Tree **1.21.1-1.0.0**
- Iron's Spells 'n Spellbooks **1.21.1-3.16.3**

## Установка

1. Убедиться, что установлены обязательные зависимости.
2. Скопировать:

```text
darkfantasyskilltrees-<version>.jar
```

в папку:

```text
.minecraft/mods/
```

3. Запустить Minecraft.

Старые версии проекта в виде отдельного datapack в `moonlight-global-datapacks` и отдельного resource pack использовать одновременно с JAR не нужно.

## Структура исходного проекта

```text
datapack_dark_fantasy_skill_trees/
├── build.gradle
├── gradle.properties
├── settings.gradle
├── gradlew
├── gradlew.bat
├── gradle/
└── src/
    └── main/
        ├── templates/
        │   └── META-INF/
        │       └── neoforge.mods.toml
        └── resources/
            ├── data/
            │   └── darkfantasy/
            │       ├── skill_trees/
            │       │   ├── mage.json
            │       │   └── warrior.json
            │       └── skills/
            │           ├── mage_01.json
            │           ├── ...
            │           ├── mage_61.json
            │           ├── warrior_01.json
            │           ├── ...
            │           └── warrior_61.json
            └── assets/
                └── darkfantasy/
                    ├── lang/
                    │   ├── en_us.json
                    │   └── ru_ru.json
                    └── textures/
                        └── icons/
                            └── skill_tree/
                                ├── mage.png
                                └── warrior.png
```

## Требования для сборки

Нужен **JDK 21**.

Проверка Java:

```powershell
java -version
```

Ожидается Java 21, например:

```text
openjdk version "21..."
```

Все команды ниже выполняются из корневой папки проекта, где находится `gradlew.bat`.

## Сборка

Обычная сборка:

```powershell
.\gradlew.bat build
```

После успешной сборки Gradle выведет:

```text
BUILD SUCCESSFUL
```

Готовый JAR появляется в:

```text
build\libs\
```

Например:

```text
build\libs\darkfantasyskilltrees-0.1.0.jar
```

## Удаление ранее собранного JAR

Удалить все собранные версии Dark Fantasy Skill Trees из `build\libs`:

```powershell
Remove-Item .\build\libs\darkfantasyskilltrees-*.jar -Force
```

Если Windows сообщает, что файл используется другим процессом, необходимо сначала закрыть процесс, удерживающий JAR. Чаще всего это Minecraft/Java или программа, открывшая файл.

## Чистая пересборка

Рекомендуемый вариант, если нужно удалить старые build-артефакты и собрать проект заново:

```powershell
.\gradlew.bat clean build
```

Это обычно удобнее, чем вручную удалять старый JAR.

## Версия мода

Версия задаётся в:

```text
gradle.properties
```

параметром:

```properties
mod_version=0.1.0
```

После изменения версии и новой сборки имя JAR обновится автоматически, например:

```text
darkfantasyskilltrees-0.2.0.jar
```

## Namespace и Mod ID

Mod ID:

```text
darkfantasyskilltrees
```

Resource/data namespace:

```text
darkfantasy
```

Это разные идентификаторы и менять namespace без необходимости не следует, поскольку на него уже ссылаются ID деревьев и навыков:

```text
darkfantasy:warrior
darkfantasy:mage
darkfantasy:warrior_01
darkfantasy:mage_01
```

## Разработка

Основные файлы деревьев:

```text
src/main/resources/data/darkfantasy/skill_trees/
```

Узлы навыков:

```text
src/main/resources/data/darkfantasy/skills/
```

Локализация:

```text
src/main/resources/assets/darkfantasy/lang/
```

Клиентские текстуры:

```text
src/main/resources/assets/darkfantasy/textures/
```

После изменения контента достаточно пересобрать проект:

```powershell
.\gradlew.bat build
```

или выполнить полную чистую пересборку:

```powershell
.\gradlew.bat clean build
```
