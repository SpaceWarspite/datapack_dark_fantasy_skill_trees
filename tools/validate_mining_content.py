import argparse
import json
import math
import struct
from pathlib import Path
from zipfile import ZipFile

import generate_mining_content as source


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/main/resources/data/darkfantasy"

parser = argparse.ArgumentParser()
parser.add_argument("--resource-jar", action="append", type=Path, default=[])
options = parser.parse_args()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


catalog = read_json(DATA / "mining_quests/catalog.json")
assert catalog == source.build_catalog()
assert len(catalog["categories"]) == 8
quests = [milestone for category in catalog["categories"] for milestone in category["milestones"]]
assert len(quests) == 32
assert sum(milestone["reward"] for milestone in quests) == 203
assert sum(milestone["reward"] + 1 for milestone in quests) == 235
assert [milestone["reward"] for milestone in catalog["categories"][0]["milestones"]] == [1, 1, 1, 1]
assert [milestone["reward"] for milestone in catalog["categories"][6]["milestones"]] == [1, 1, 1, 1]

assert source.MINER_ORDER == [6, 1, 2, 3, 4, 5, 12, 7, 8, 9, 10, 11, 18, 13, 14, 15, 16, 17, 24, 19, 20, 21, 22, 23, 30, 25, 26, 27, 28, 29, 36, 31, 32, 33, 34, 35]
assert sorted(source.MINER_ORDER) == list(range(1, 37))

assert source.CHECKPOINTS == {
    6: ("enchanting_table", "minecraft:enchanting_table"),
    12: ("respawn_anchor", "minecraft:respawn_anchor"),
    18: ("conduit", "minecraft:conduit"),
    24: ("calibrated_sculk_sensor", "minecraft:calibrated_sculk_sensor"),
    30: ("beacon", "minecraft:beacon"),
    36: ("shulker_box", "minecraft:shulker_box"),
}
assert source.KEYSTONE_GLYPHS == {
    6: "eye_green",
    12: "skull",
    18: "heart_cyan",
    24: "heart_violet",
    30: "torch",
    36: "treasure_chest_gold",
}

icons = [
    ROOT / "src/main/resources/assets/darkfantasy/textures/icons/skill_tree/miner.png",
    ROOT / "src/main/resources/assets/darkfantasy/textures/icons/skill_tree/mining_quests.png",
]
icon_bytes = [path.read_bytes() for path in icons]
assert icon_bytes[0] == icon_bytes[1]
assert all(data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (38, 114) for data in icon_bytes)

tree = read_json(DATA / "skill_trees/miner.json")
nodes_by_id = {index: read_json(DATA / "skills" / f"miner_{index:02d}.json") for index in range(1, 37)}
nodes = [nodes_by_id[index] for index in source.MINER_ORDER]
assert tree["skillIds"] == [f"darkfantasy:miner_{index:02d}" for index in source.MINER_ORDER]
assert [node["id"] for node in nodes] == tree["skillIds"]
assert nodes[0]["id"] == "darkfantasy:miner_06"
assert nodes[0]["isStartingPoint"] and not nodes[0]["directConnections"]
assert sum(node["isStartingPoint"] for node in nodes) == 1
assert sum(bonus["multiplier"] * 100 for node in nodes for bonus in node["bonuses"] if bonus["type"] == "skilltree:block_break_speed") == 300
assert sum(bonus["multiplier"] * 100 for node in nodes for bonus in node["bonuses"] if bonus["type"] == "skilltree:gained_experience") == 300
ore_xp_bonuses = [bonus for node in nodes for bonus in node["bonuses"] if bonus["type"] == "skilltree:gained_experience"]
assert len(ore_xp_bonuses) == 12
assert all(bonus["multiplier"] == 0.25 for bonus in ore_xp_bonuses)
assert source.GROUP_SPEED == [5, 5, 5, 10, 10, 15]
assert source.DURABILITY_NODES == {2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24, 27, 30, 33, 36}
durability = [bonus for node in nodes for bonus in node["bonuses"] if bonus["type"] == "skilltree:item_durability_loss_avoidance"]
assert len(durability) == 40
assert sum(bonus["chance"] for bonus in durability if bonus["item_condition"]["equipment_type"] == "tool") == 1.0
assert sum(bonus["chance"] for bonus in durability if bonus["item_condition"]["equipment_type"] == "armor") == 1.0

assert source.CHECKPOINTS == {
    6: ("enchanting_table", "minecraft:enchanting_table"),
    12: ("respawn_anchor", "minecraft:respawn_anchor"),
    18: ("conduit", "minecraft:conduit"),
    24: ("calibrated_sculk_sensor", "minecraft:calibrated_sculk_sensor"),
    30: ("beacon", "minecraft:beacon"),
    36: ("shulker_box", "minecraft:shulker_box"),
}
gate_positions = [1, 7, 13, 19, 25, 31]
assert [nodes[position - 1]["id"] for position in gate_positions] == [
    f"darkfantasy:miner_{index:02d}" for index in source.CHECKPOINTS
]
for group_start in range(0, 36, 6):
    group = nodes[group_start:group_start + 6]
    assert group_start == 0 or group_start + 1 in gate_positions
    assert [node["id"] for node in group[1:]] == [
        f"darkfantasy:miner_{index:02d}" for index in source.MINER_ORDER[group_start + 1:group_start + 6]
    ]
    assert all(node["id"].split("_")[-1] not in {f"{gate:02d}" for gate in source.CHECKPOINTS} for node in group[1:])

for position, node in enumerate(nodes, start=1):
    skill_index = source.MINER_ORDER[position - 1]
    previous_index = source.MINER_ORDER[position - 2] if position > 1 else None
    assert node["id"] == f"darkfantasy:miner_{skill_index:02d}"
    assert node["directConnections"] == ([f"darkfantasy:miner_{previous_index:02d}"] if previous_index is not None else [])
    assert node["isStartingPoint"] == (position == 1)
    assert (node["positionX"], node["positionY"]) == source.coordinates(position)
    speed = [bonus["multiplier"] * 100 for bonus in node["bonuses"] if bonus["type"] == "skilltree:block_break_speed"]
    assert speed == [source.GROUP_SPEED[(skill_index - 1) % 6]]
    ore_xp = [bonus["multiplier"] for bonus in node["bonuses"] if bonus["type"] == "skilltree:gained_experience"]
    assert ore_xp == ([0.25] if skill_index % 3 == 0 else [])
    durability_for_node = [bonus for bonus in node["bonuses"] if bonus["type"] == "skilltree:item_durability_loss_avoidance"]
    expected_durability = 2 if skill_index in source.DURABILITY_NODES else 0
    assert len(durability_for_node) == expected_durability
    assert all(bonus["chance"] == 0.05 for bonus in durability_for_node)
    assert {bonus["item_condition"]["equipment_type"] for bonus in durability_for_node} == ({"tool", "armor"} if expected_durability else set())
    if skill_index in source.CHECKPOINTS:
        block, stat_id = source.CHECKPOINTS[skill_index]
        assert node["requirements"] == [{"type": "skilltree:stat_value", "statTypeId": "minecraft:crafted", "statId": stat_id, "minValue": 1}]
        assert node["description"][0]["with"] == [{"translate": f"block.minecraft.{block}"}]
        assert node["iconTexture"] == f"skilltree:textures/icons/{source.KEYSTONE_GLYPHS[skill_index]}.png"
        assert node["buttonSize"] == 32
    else:
        assert node["buttonSize"] == 16
    x, y = node["positionX"], node["positionY"]
    for previous in nodes[:position - 1]:
        dx = abs(x - previous["positionX"])
        dy = abs(y - previous["positionY"])
        half_widths = (node["buttonSize"] + previous["buttonSize"]) / 2
        assert dx >= half_widths or dy >= half_widths, (node["id"], previous["id"], dx, dy)

quest_tree = read_json(DATA / "skill_trees/mining_quests.json")
assert len(quest_tree["skillIds"]) == 32
root_advancement = read_json(DATA / "advancement/mining/root.json")
assert root_advancement["criteria"] == {"root": {"trigger": "minecraft:impossible"}}
assert root_advancement["display"]["hidden"]
assert root_advancement["display"]["title"]["translate"] == "advancements.mining.root.title"
assert root_advancement["display"]["description"]["translate"] == "advancements.mining.root.description"
for category in catalog["categories"]:
    for milestone in category["milestones"]:
        key = f"{category['id']}_{milestone['stage']}"
        skill_id = f"darkfantasy:mining_quest_{key}"
        skill = read_json(DATA / "skills" / f"mining_quest_{key}.json")
        assert skill["id"] == skill_id
        assert skill["isAlwaysStartingPoint"]
        assert skill["requirements"] == [{"type": "skilltree:advancement", "advancement": f"darkfantasy:mining/ready/{key}"}]
        bonus = skill["bonuses"][0]
        assert bonus["type"] == "skilltree:command"
        assert bonus["event_listener"]["type"] == "skilltree:skill_learned"
        assert bonus["command"] == f"function darkfantasy:mining/claim/{key}"
        assert skill["description"][0]["translate"] == f"skill.darkfantasy.{skill_id.split(':')[1]}.description"
        assert skill["description"][1]["translate"] == f"skill.darkfantasy.{skill_id.split(':')[1]}.claim_description"
        assert skill["description"][1]["with"] == [{"text": str(milestone["reward"] + 1)}]
        assert bonus["description"] == f"skill.darkfantasy.{skill_id.split(':')[1]}.reward"
        ready = read_json(DATA / "advancement/mining/ready" / f"{key}.json")
        paid = read_json(DATA / "advancement/mining/paid" / f"{key}.json")
        assert ready["display"]["hidden"] and ready["display"]["show_toast"] is False
        assert ready["parent"] == "darkfantasy:mining/root"
        assert paid.get("display") is None
        claim = (DATA / "function/mining/claim" / f"{key}.mcfunction").read_text(encoding="utf-8")
        claim_once = (DATA / "function/mining/claim_once" / f"{key}.mcfunction").read_text(encoding="utf-8")
        assert "unless entity @s[advancements={darkfantasy:mining/paid/" in claim
        assert claim.index("ready/") < claim.index("unless entity")
        assert claim_once.splitlines()[0] == f"advancement grant @s only darkfantasy:mining/paid/{key}"
        assert claim_once.splitlines()[1] == f"advancement revoke @s only darkfantasy:mining/ready/{key}"
        assert claim_once.splitlines()[2] == f"skilltree points add @s {milestone['reward'] + 1}"

for language in ("en_us", "ru_ru"):
    translations = read_json(ROOT / "src/main/resources/assets/darkfantasy/lang" / f"{language}.json")
    assert translations["darkfantasy:miner"]
    assert translations["darkfantasy:mining_quests"]
    assert translations["advancements.mining.root.title"]
    assert translations["advancements.mining.root.description"]
    for category in catalog["categories"]:
        for milestone in category["milestones"]:
            key = f"{category['id']}_{milestone['stage']}"
            assert f"advancements.mining.ready.{key}.title" in translations
            assert translations[f"skill.darkfantasy.mining_quest_{key}.description"] == (
                f"Mine {milestone['threshold']:,} blocks in this category."
                if language == "en_us"
                else f"Добудьте {milestone['threshold']:,} блоков этой категории."
            )
            assert translations[f"skill.darkfantasy.mining_quest_{key}.claim_description"] == (
                f"Learn: cost 1, grants {milestone['reward'] + 1} points."
                if language == "en_us"
                else f"Изучение: стоимость 1, начисление {milestone['reward'] + 1} очк."
            )
            assert translations[f"skill.darkfantasy.mining_quest_{key}.reward"] == (
                f"Net reward: +{milestone['reward']} skill points"
                if language == "en_us"
                else f"Чистая награда: +{milestone['reward']} очк. навыков"
            )
    for index in source.CHECKPOINTS:
        assert translations[f"skill.darkfantasy.miner_{index:02d}.description"]

if options.resource_jar:
    resources = ROOT / "src/main/resources"
    assets = {path.relative_to(resources).as_posix() for path in (resources / "assets").rglob("*") if path.is_file()}
    for jar in options.resource_jar:
        with ZipFile(jar) as archive:
            assets.update(archive.namelist())
    for skill_path in (DATA / "skills").glob("min*.json"):
        skill = read_json(skill_path)
        for key in ("iconTexture", "backgroundTexture", "borderTexture"):
            namespace, path = skill[key].split(":", 1)
            assert f"assets/{namespace}/{path}" in assets, (skill_path.name, key, skill[key])
    print("All mining skill textures exist in the supplied resource JARs and addon.")

print("Mining content validation passed: canonical 36-skill order, 32 guarded quests, 203 net / 235 credited quest points, 300% speed/ore XP, 100% tool/armor preservation.")
