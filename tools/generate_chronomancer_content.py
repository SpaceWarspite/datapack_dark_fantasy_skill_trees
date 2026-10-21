import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/main/resources"
SKILLS = RESOURCES / "data/darkfantasy/skills"
CAST = "irons_spellbooks:cast_time_reduction"
COOLDOWN = "irons_spellbooks:cooldown_reduction"
DURATION = "darkfantasyskilltrees:self_spell_duration"

NODES = [
    (10, 10, 1, (-17.48959, -7.42389), [(CAST, .07, 1)], None),
    (11, 11, 10, (-36.16467, -23.2619), [(COOLDOWN, .07, 1)], None),
    (12, 12, 11, (-46, -56), [(CAST, .07, 1)], None),
    (13, 13, 12, (-43, -83), [(COOLDOWN, .07, 1)], None),
    (14, 14, 13, (-37, -110), [("irons_spellbooks:casting_movespeed", .21, 1)], None),
    (15, 15, 14, (-26, -136), [("irons_spellbooks:spell_resist", .14, 1)], None),
    (16, 16, 15, (-18, -165), [(CAST, .17, 1), (COOLDOWN, .19, 1)], None),
    (103, 12, 16, (-44, -187), [(CAST, .07, 1)], ("Быстрое колдовство III", "Quick Casting III")),
    (104, 13, 103, (-62, -212), [(COOLDOWN, .07, 1)], ("Магический ритм III", "Arcane Rhythm III")),
    (105, 16, 104, (-80, -238), [(CAST, .17, 1), (COOLDOWN, .19, 1)], ("Ускорение времени", "Time Acceleration")),
    (17, 17, 105, (-101, -267), [(CAST, .20, 1), (COOLDOWN, .24, 1), ("irons_spellbooks:max_mana", -50, 0)], None),
    (106, 12, 16, (8, -187), [(CAST, .07, 1)], ("Быстрое колдовство IV", "Quick Casting IV")),
    (107, 13, 106, (26, -212), [(COOLDOWN, .07, 1)], ("Магический ритм IV", "Arcane Rhythm IV")),
    (108, 16, 107, (44, -238), [(CAST, .17, 1), (COOLDOWN, .19, 1)], ("Петля мгновений", "Moment Loop")),
    (109, 17, 108, (65, -267), [(CAST, .20, 1), (COOLDOWN, .24, 1), ("irons_spellbooks:max_mana", -55, 0)], ("Властелин времени", "Lord of Time")),
    (110, 12, 16, (-18, -205), [(DURATION, .25, 1)], ("Долгое мгновение I", "Lingering Moment I")),
    (111, 12, 110, (-18, -229), [(DURATION, .25, 1)], ("Долгое мгновение II", "Lingering Moment II")),
    (112, 12, 111, (-18, -253), [(DURATION, .50, 1)], ("Долгое мгновение III", "Lingering Moment III")),
    (113, 12, 112, (-18, -277), [(DURATION, .50, 1)], ("Долгое мгновение IV", "Lingering Moment IV")),
    (114, 16, 113, (-18, -303), [(DURATION, .50, 1)], ("Непрерывный поток", "Unbroken Flow")),
    (115, 17, 114, (-18, -337), [(DURATION, .50, 1), ("irons_spellbooks:max_mana", -50, 0)], ("Вечный миг", "Eternal Moment")),
]


def read(path):
    return json.loads(path.read_text("utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")


def main():
    templates = {index: read(SKILLS / f"mage_{index:02d}.json") for index in range(10, 18)}
    for index, template, parent, position, effects, names in NODES:
        node = copy.deepcopy(templates[template])
        node_id = f"darkfantasy:mage_{index:02d}"
        node["id"] = node_id
        node["positionX"], node["positionY"] = position
        node["directConnections"] = [f"darkfantasy:mage_{parent:02d}"]
        node["bonuses"] = [
            {
                "player_condition": {"type": "skilltree:none"},
                "id": f"{node_id}_bonus_{bonus_index}",
                "player_multiplier": {"type": "skilltree:none"},
                "attribute": attribute,
                "operation": operation,
                "amount": amount,
                "type": "skilltree:attribute",
            }
            for bonus_index, (attribute, amount, operation) in enumerate(effects)
        ]
        write(SKILLS / f"mage_{index:02d}.json", node)
    tree_path = RESOURCES / "data/darkfantasy/skill_trees/mage.json"
    tree = read(tree_path)
    for index in range(103, 116):
        node_id = f"darkfantasy:mage_{index}"
        if node_id not in tree["skillIds"]:
            tree["skillIds"].append(node_id)
    write(tree_path, tree)
    for language, language_index in (("ru_ru", 0), ("en_us", 1)):
        path = RESOURCES / f"assets/darkfantasy/lang/{language}.json"
        lang = read(path)
        for index, _, _, _, _, names in NODES:
            if names:
                lang[f"skill.darkfantasy.mage_{index}.name"] = names[language_index]
            if index >= 110:
                lang[f"skill.darkfantasy.mage_{index}.description"] = (
                    "Продлевает положительные эффекты собственных заклинаний, наложенные на себя при касте. Не действует на зелья, эффекты союзников и бесконечные эффекты."
                    if language_index == 0 else
                    "Extends beneficial effects applied to yourself during your own spell cast. Does not affect potions, allies' buffs or infinite effects."
                )
        lang["attribute.darkfantasyskilltrees.self_spell_duration"] = (
            "Длительность эффектов собственных заклинаний" if language_index == 0 else "Self-cast spell effect duration"
        )
        write(path, lang)
    print("Generated Chronomancer: 21 nodes, three arms, existing skill IDs preserved")


if __name__ == "__main__":
    main()
