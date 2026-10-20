import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/main/resources/data/darkfantasy"
LANG = ROOT / "src/main/resources/assets/darkfantasy/lang"
ICON_TARGET = ROOT / "src/main/resources/assets/darkfantasy/textures/icons/skill_tree/miner.png"

CATEGORIES = [
    ("stone", "minecraft:stone", [1000, 5000, 20000, 60000], [1, 1, 1, 1], "Stone Delver", "Каменолом"),
    ("coal", "minecraft:coal_ore", [64, 256, 1024, 4096], [2, 3, 5, 8], "Coal Seeker", "Искатель угля"),
    ("iron", "minecraft:iron_ore", [32, 128, 512, 2048], [2, 4, 6, 10], "Iron Prospector", "Искатель железа"),
    ("gold", "minecraft:gold_ore", [16, 64, 256, 1024], [3, 5, 8, 12], "Gold Prospector", "Искатель золота"),
    ("redstone", "minecraft:redstone_ore", [64, 256, 1024, 4096], [2, 4, 6, 10], "Redstone Delver", "Искатель редстоуна"),
    ("diamond", "minecraft:diamond_ore", [8, 32, 128, 512], [5, 10, 15, 20], "Diamond Seeker", "Искатель алмазов"),
    ("obsidian", "minecraft:obsidian", [32, 128, 512, 2048], [1, 1, 1, 1], "Obsidian Breaker", "Разрушитель обсидиана"),
    ("ancient_debris", "minecraft:ancient_debris", [4, 16, 48, 128], [5, 10, 15, 25], "Relic Hunter", "Охотник за древними обломками"),
]
DEEPSLATE = {
    "coal": "minecraft:deepslate_coal_ore",
    "iron": "minecraft:deepslate_iron_ore",
    "gold": "minecraft:deepslate_gold_ore",
    "redstone": "minecraft:deepslate_redstone_ore",
    "diamond": "minecraft:deepslate_diamond_ore",
}
CHECKPOINTS = {
    6: ("enchanting_table", "minecraft:enchanting_table"),
    12: ("respawn_anchor", "minecraft:respawn_anchor"),
    18: ("conduit", "minecraft:conduit"),
    24: ("calibrated_sculk_sensor", "minecraft:calibrated_sculk_sensor"),
    30: ("beacon", "minecraft:beacon"),
    36: ("shulker_box", "minecraft:shulker_box"),
}
MINER_ORDER = [6, 1, 2, 3, 4, 5, 12, 7, 8, 9, 10, 11, 18, 13, 14, 15, 16, 17, 24, 19, 20, 21, 22, 23, 30, 25, 26, 27, 28, 29, 36, 31, 32, 33, 34, 35]
KEYSTONE_GLYPHS = {
    6: "eye_green",
    12: "skull",
    18: "heart_cyan",
    24: "heart_violet",
    30: "torch",
    36: "treasure_chest_gold",
}
GROUP_SPEED = [5, 5, 5, 10, 10, 15]
DURABILITY_NODES = {2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24, 27, 30, 33, 36}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resource_id(value):
    return value.removeprefix("minecraft:")


def coordinates(index):
    if index == 1:
        return 0.0, 0.0
    radius = 36 + 3.5 * index
    angle = 0.54 * index
    return round(radius * math.cos(angle), 3), round(radius * math.sin(angle), 3)


def build_catalog():
    return {
        "version": 1,
        "categories": [
            {
                "id": category,
                "block_ids": [block_id] + ([DEEPSLATE[category]] if category in DEEPSLATE else [])
                + (["minecraft:nether_gold_ore"] if category == "gold" else []),
                "milestones": [
                    {"stage": stage, "threshold": thresholds[stage - 1], "reward": rewards[stage - 1]}
                    for stage in range(1, 5)
                ],
            }
            for category, block_id, thresholds, rewards, _, _ in CATEGORIES
        ],
    }


def skill_bonus(skill_id, bonus_id, bonus_type, value_key, value, extra=None):
    bonus = {
        "player_condition": {"type": "skilltree:none"},
        "id": f"darkfantasy:{skill_id}_{bonus_id}",
        "player_multiplier": {"type": "skilltree:none"},
        value_key: value,
        "type": bonus_type,
    }
    if extra:
        bonus.update(extra)
    return bonus


def miner_skill(skill_index, position, previous_index):
    skill_id = f"miner_{skill_index:02d}"
    checkpoint = CHECKPOINTS.get(skill_index)
    frame = "keystone" if checkpoint else "lesser"
    x, y = coordinates(position)
    percent = GROUP_SPEED[(skill_index - 1) % 6]
    bonuses = [
        skill_bonus(skill_id, "speed", "skilltree:block_break_speed", "multiplier", percent / 100),
    ]
    if skill_index % 3 == 0:
        bonuses.append(skill_bonus(
            skill_id, "ore_xp", "skilltree:gained_experience", "multiplier", 0.25,
            {"experience_source": "ore"},
        ))
    if skill_index in DURABILITY_NODES:
        for equipment in ("tool", "armor"):
            bonuses.append(skill_bonus(
                skill_id, f"durability_{equipment}", "skilltree:item_durability_loss_avoidance", "chance", 0.05,
                {"item_condition": {"type": "skilltree:equipment_type", "equipment_type": equipment}},
            ))
    requirement = []
    description = []
    if checkpoint:
        requirement.append({
            "type": "skilltree:stat_value",
            "statTypeId": "minecraft:crafted",
            "statId": checkpoint[1],
            "minValue": 1,
        })
        description.append({
            "translate": f"skill.darkfantasy.{skill_id}.description",
            "with": [{"translate": f"block.minecraft.{checkpoint[0]}"}],
        })
    return {
        "requirements": requirement,
        "positionY": y,
        "borderTexture": f"skilltree:textures/tooltip/{frame}.png",
        "backgroundTexture": f"skilltree:textures/icons/background/{frame}.png",
        "iconTexture": f"skilltree:textures/icons/{KEYSTONE_GLYPHS[skill_index]}.png" if checkpoint else "minecraft:textures/item/iron_pickaxe.png",
        "buttonSize": 32 if checkpoint else 16,
        "isStartingPoint": position == 1,
        "tags": [],
        "bonuses": bonuses,
        "id": f"darkfantasy:{skill_id}",
        "titleColor": "",
        "longConnections": [],
        "directConnections": [f"darkfantasy:miner_{previous_index:02d}"] if previous_index is not None else [],
        "oneWayConnections": [],
        "positionX": x,
        **({"description": description} if description else {}),
    }


def quest_skill(category, block_id, column, stage, threshold, reward):
    skill_id = f"mining_quest_{category}_{stage}"
    quest_key = f"{category}_{stage}"
    return {
        "requirements": [{
            "type": "skilltree:advancement",
            "advancement": f"darkfantasy:mining/ready/{quest_key}",
        }],
        "positionY": (1.5 - stage) * 42,
        "borderTexture": "skilltree:textures/tooltip/lesser.png",
        "backgroundTexture": "skilltree:textures/icons/background/lesser.png",
        "iconTexture": f"minecraft:textures/block/{resource_id(block_id)}{'_side' if category == 'ancient_debris' else ''}.png",
        "buttonSize": 20,
        "isStartingPoint": False,
        "isAlwaysStartingPoint": True,
        "tags": [],
        "bonuses": [{
            "player_condition": {"type": "skilltree:none"},
            "id": f"darkfantasy:{skill_id}_claim",
            "player_multiplier": {"type": "skilltree:none"},
            "type": "skilltree:command",
            "command": f"function darkfantasy:mining/claim/{quest_key}",
            "description": f"skill.darkfantasy.{skill_id}.reward",
            "event_listener": {
                "type": "skilltree:skill_learned",
                "player_multiplier": {"type": "skilltree:none"},
            },
        }],
        "id": f"darkfantasy:{skill_id}",
        "titleColor": "",
        "longConnections": [],
        "directConnections": [],
        "oneWayConnections": [],
        "positionX": (column - 3.5) * 44,
        "description": [
            {"translate": f"skill.darkfantasy.{skill_id}.description", "with": [{"text": f"{threshold:,}"}]},
            {"translate": f"skill.darkfantasy.{skill_id}.claim_description", "with": [{"text": f"{reward + 1}"}]},
        ],
    }


def ready_advancement(category, stage, threshold, display_item):
    key = f"{category}_{stage}"
    return {
        "parent": "darkfantasy:mining/root",
        "display": {
            "icon": {"id": display_item},
            "title": {"translate": f"advancements.mining.ready.{key}.title"},
            "description": {"translate": f"advancements.mining.ready.{key}.description"},
            "hidden": True,
            "show_toast": False,
            "announce_to_chat": False,
        },
        "criteria": {"eligible": {"trigger": "minecraft:impossible"}},
        "requirements": [["eligible"]],
    }


def root_advancement():
    return {
        "display": {
            "icon": {"id": "minecraft:iron_pickaxe"},
            "background": "minecraft:textures/gui/advancements/backgrounds/stone.png",
            "title": {"translate": "advancements.mining.root.title"},
            "description": {"translate": "advancements.mining.root.description"},
            "hidden": True,
            "show_toast": False,
            "announce_to_chat": False,
        },
        "criteria": {"root": {"trigger": "minecraft:impossible"}},
        "requirements": [["root"]],
    }


def main():
    catalog = build_catalog()
    write_json(DATA / "mining_quests/catalog.json", catalog)
    write_json(DATA / "skill_trees/miner.json", {
        "skillIds": [f"darkfantasy:miner_{index:02d}" for index in MINER_ORDER],
        "id": "darkfantasy:miner",
    })
    quest_ids = []
    en = {}
    ru = {}
    write_json(DATA / "advancement/mining/root.json", root_advancement())
    en["darkfantasy:miner"] = "Lord of the Depths"
    ru["darkfantasy:miner"] = "Владыка недр"
    en["darkfantasy:mining_quests"] = "Mining Quests"
    ru["darkfantasy:mining_quests"] = "Задания шахтёра"
    en["advancements.mining.root.title"] = "Mining"
    en["advancements.mining.root.description"] = "Mining quests and milestones."
    ru["advancements.mining.root.title"] = "Добыча"
    ru["advancements.mining.root.description"] = "Квесты и этапы добычи ресурсов."
    for position, index in enumerate(MINER_ORDER, start=1):
        previous_index = MINER_ORDER[position - 2] if position > 1 else None
        node = miner_skill(index, position, previous_index)
        write_json(DATA / "skills" / f"miner_{index:02d}.json", node)
        skill_id = node["id"].split(":", 1)[1]
        checkpoint = CHECKPOINTS.get(index)
        if checkpoint:
            en[f"skill.darkfantasy.{skill_id}.name"] = f"Master Miner {index // 6}"
            ru[f"skill.darkfantasy.{skill_id}.name"] = f"Мастер шахтёр {index // 6}"
            en[f"skill.darkfantasy.{skill_id}.description"] = "Requires crafting %s at least once."
            ru[f"skill.darkfantasy.{skill_id}.description"] = "Требуется хотя бы раз создать: %s."
        else:
            en[f"skill.darkfantasy.{skill_id}.name"] = f"Mining +{GROUP_SPEED[(index - 1) % 6]}%"
            ru[f"skill.darkfantasy.{skill_id}.name"] = f"Добыча +{GROUP_SPEED[(index - 1) % 6]}%"
    quest_tree = []
    for col, (category, block_id, thresholds, rewards, en_name, ru_name) in enumerate(CATEGORIES):
        for stage, (threshold, reward) in enumerate(zip(thresholds, rewards), start=1):
            key = f"{category}_{stage}"
            node = quest_skill(category, block_id, col, stage, threshold, reward)
            skill_id = node["id"].split(":", 1)[1]
            quest_ids.append(f"darkfantasy:{skill_id}")
            quest_tree.append(node)
            write_json(DATA / "skills" / f"{skill_id}.json", node)
            en[f"skill.darkfantasy.{skill_id}.name"] = f"{en_name} {stage}"
            ru[f"skill.darkfantasy.{skill_id}.name"] = f"{ru_name} {stage}"
            en[f"skill.darkfantasy.{skill_id}.description"] = f"Mine {threshold:,} blocks in this category."
            ru[f"skill.darkfantasy.{skill_id}.description"] = f"Добудьте {threshold:,} блоков этой категории."
            en[f"skill.darkfantasy.{skill_id}.claim_description"] = f"Learn: cost 1, grants {reward + 1} points."
            ru[f"skill.darkfantasy.{skill_id}.claim_description"] = f"Изучение: стоимость 1, начисление {reward + 1} очк."
            en[f"skill.darkfantasy.{skill_id}.reward"] = f"Net reward: +{reward} skill points"
            ru[f"skill.darkfantasy.{skill_id}.reward"] = f"Чистая награда: +{reward} очк. навыков"
            display_item = block_id
            if category == "stone":
                display_item = "minecraft:stone"
            write_json(DATA / "advancement/mining/ready" / f"{key}.json",
                       ready_advancement(category, stage, threshold, display_item))
            write_json(DATA / "advancement/mining/paid" / f"{key}.json", {
                "criteria": {"paid": {"trigger": "minecraft:impossible"}},
                "requirements": [["paid"]],
            })
            functions = DATA / "function/mining"
            (functions / "claim").mkdir(parents=True, exist_ok=True)
            (functions / "claim" / f"{key}.mcfunction").write_text(
                f"execute if entity @s[advancements={{darkfantasy:mining/ready/{key}=true}}] unless entity @s[advancements={{darkfantasy:mining/paid/{key}=true}}] run function darkfantasy:mining/claim_once/{key}\n",
                encoding="utf-8",
            )
            (functions / "claim_once").mkdir(parents=True, exist_ok=True)
            (functions / "claim_once" / f"{key}.mcfunction").write_text(
                f"advancement grant @s only darkfantasy:mining/paid/{key}\n"
                f"advancement revoke @s only darkfantasy:mining/ready/{key}\n"
                f"skilltree points add @s {reward + 1}\n",
                encoding="utf-8",
            )
            en[f"advancements.mining.ready.{key}.title"] = f"{en_name} {stage} ready"
            en[f"advancements.mining.ready.{key}.description"] = f"Mine {threshold:,} blocks. Claim this milestone in the Mining Quests tree."
            ru[f"advancements.mining.ready.{key}.title"] = f"{ru_name} {stage} доступно"
            ru[f"advancements.mining.ready.{key}.description"] = f"Добудьте {threshold:,} блоков. Заберите награду в дереве квестов шахтёра."
    write_json(DATA / "skill_trees/mining_quests.json", {
        "skillIds": quest_ids,
        "id": "darkfantasy:mining_quests",
    })
    for language, values in (("en_us", en), ("ru_ru", ru)):
        path = LANG / f"{language}.json"
        existing = json.loads(path.read_text(encoding="utf-8"))
        for index in CHECKPOINTS:
            skill_id = f"miner_{index:02d}"
            existing.pop(f"skill.darkfantasy.{skill_id}.description", None)
        existing.update(values)
        write_json(path, existing)
    quest_icon = ICON_TARGET.parent / "mining_quests.png"
    quest_icon.write_bytes(ICON_TARGET.read_bytes())


if __name__ == "__main__":
    main()
