import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/main/resources"
BRANCH_IDS = {f"darkfantasy:mage_{index:02d}" for index in (*range(10, 18), *range(103, 110))}
ENTRANCE_IDS = {"darkfantasy:mage_10", "darkfantasy:mage_11"}


def point(node):
    return node["positionX"], node["positionY"]


def distance_to_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / denominator))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def crosses(a, b, c, d):
    def orientation(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return orientation(a, b, c) * orientation(a, b, d) < 0 and orientation(c, d, a) * orientation(c, d, b) < 0


def validate(read, baseline=None, assets=None):
    tree = read("data/darkfantasy/skill_trees/mage.json")
    assert len(tree["skillIds"]) == 115, f"Expected 115 Mage nodes, got {len(tree['skillIds'])}"
    assert len(set(tree["skillIds"])) == 115, "Duplicate Mage IDs"
    assert BRANCH_IDS <= set(tree["skillIds"]), "Chronomancer must contain 15 nodes"
    nodes = {id: read(f"data/darkfantasy/skills/{id.split(':')[1]}.json") for id in tree["skillIds"]}
    edges = set()
    bonus_ids = []
    for id, node in nodes.items():
        assert id == node["id"], f"Wrong ID in {id}"
        for key in ("directConnections", "longConnections", "oneWayConnections"):
            for target in node[key]:
                assert target in nodes and target != id, f"Invalid connection {id} to {target}"
                edges.add(frozenset((id, target)))
        bonus_ids.extend(b["id"] for b in node["bonuses"] if "id" in b)
        if assets is not None and id in BRANCH_IDS:
            for key in ("backgroundTexture", "iconTexture", "borderTexture"):
                namespace, path = node[key].split(":", 1)
                assert f"assets/{namespace}/{path}" in assets, f"Missing texture {node[key]}"
    assert len(bonus_ids) == len(set(bonus_ids)), "Duplicate bonus modifier IDs"
    branch = [nodes[id] for id in BRANCH_IDS]
    assert Counter(n["backgroundTexture"].split("/")[-1] for n in branch) == {
        "lesser.png": 10, "notable.png": 3, "keystone.png": 2
    }, "Expected 10 ordinary, 3 notable and 2 keystone nodes"
    assert all(not n["tags"] and not n["isStartingPoint"] for n in branch), "Arms must be jointly learnable from the existing start"
    totals = defaultdict(Decimal)
    for node in branch:
        for bonus in node["bonuses"]:
            assert bonus["type"] == "skilltree:attribute"
            assert bonus["player_condition"] == {"type": "skilltree:none"}
            assert bonus["player_multiplier"] == {"type": "skilltree:none"}
            totals[bonus["attribute"], bonus["operation"]] += Decimal(str(bonus["amount"]))
    assert dict(totals) == {
        ("irons_spellbooks:cast_time_reduction", 1): Decimal("1.19"),
        ("irons_spellbooks:cooldown_reduction", 1): Decimal("1.33"),
        ("irons_spellbooks:casting_movespeed", 1): Decimal("0.21"),
        ("irons_spellbooks:spell_resist", 1): Decimal("0.14"),
        ("irons_spellbooks:max_mana", 0): Decimal("-105"),
    }, f"Wrong aggregate modifiers: {dict(totals)}"
    parent = {n["id"]: n["directConnections"][0] for n in branch}
    assert all(len(n["directConnections"]) == 1 and not n["longConnections"] and not n["oneWayConnections"] for n in branch)
    assert set(parent.values()) - BRANCH_IDS == {"darkfantasy:mage_01"}
    children = Counter(parent.values())
    leaves = BRANCH_IDS - set(parent.values())
    assert leaves == {"darkfantasy:mage_17", "darkfantasy:mage_109"}
    assert children["darkfantasy:mage_16"] == 2 and max(children.values()) == 2
    for index, advancement in ((105, "spell_book_equip"), (108, "spell_book_equip"), (109, "spell_book_gold")):
        assert nodes[f"darkfantasy:mage_{index}"]["requirements"] == [
            {"advancement": f"irons_spellbooks:irons_spellbooks/{advancement}", "type": "skilltree:advancement"}
        ], f"Wrong advancement gate for mage_{index}"
    paths = []
    for leaf in sorted(leaves):
        path = [leaf]
        while path[-1] != "darkfantasy:mage_01":
            path.append(parent[path[-1]])
            assert len(path) == len(set(path)), f"Cycle from {leaf}"
        assert len(path) == 12, f"Expected 11 edges from start to {leaf}"
        length = sum(math.dist(point(nodes[a]), point(nodes[b])) for a, b in itertools.pairwise(path))
        assert 300 <= length <= 340, f"Unexpected compact path length {length}"
        paths.append(round(length, 3))
    branch_edges = {edge for edge in edges if edge & BRANCH_IDS}
    spacing = []
    for a, b in itertools.combinations(nodes.values(), 2):
        pair = {a["id"], b["id"]}
        if not pair & BRANCH_IDS or frozenset(pair) in edges:
            continue
        gap = math.dist(point(a), point(b)) - (a["buttonSize"] + b["buttonSize"]) / 2
        if pair & ENTRANCE_IDS:
            assert gap >= 1.8, f"Entrance spacing regressed: {pair}, {gap}"
        else:
            assert gap >= 8, f"Buttons too close: {pair}, gap {gap}"
            spacing.append(gap)
    for edge in branch_edges:
        a, b = sorted(edge)
        for id, node in nodes.items():
            if id in edge:
                continue
            clearance = distance_to_segment(point(node), point(nodes[a]), point(nodes[b])) - node["buttonSize"] / 2
            assert clearance >= 0, f"Connection {a}, {b} crosses button {id}"
        for other in edges:
            if edge & other:
                continue
            c, d = sorted(other)
            assert not crosses(point(nodes[a]), point(nodes[b]), point(nodes[c]), point(nodes[d])), f"Crossing links {edge} and {other}"
    for language in ("ru_ru", "en_us"):
        lang = read(f"assets/darkfantasy/lang/{language}.json")
        names = [lang[f"skill.darkfantasy.{id.split(':')[1]}.name"] for id in BRANCH_IDS]
        assert all(names) and len(names) == len(set(names)), f"Missing or duplicate {language} names"
    if baseline:
        old_tree = baseline("data/darkfantasy/skill_trees/mage.json")
        assert tree["skillLimitations"] == old_tree["skillLimitations"]
        for id in old_tree["skillIds"]:
            old = baseline(f"data/darkfantasy/skills/{id.split(':')[1]}.json")
            if id not in BRANCH_IDS:
                assert nodes[id] == old, f"Unrelated skill changed: {id}"
            else:
                assert nodes[id]["requirements"] == old["requirements"], f"Existing gate changed: {id}"
        for id in ENTRANCE_IDS:
            old = baseline(f"data/darkfantasy/skills/{id.split(':')[1]}.json")
            assert point(nodes[id]) == point(old) and nodes[id]["buttonSize"] == old["buttonSize"], "Keep the crowded entrance unchanged"
        assert set(old_tree["skillIds"]) <= set(tree["skillIds"]), "Existing save IDs removed"
    print(f"PASS: 15 nodes, 2 terminal keystones, exact x7 modifiers; paths {paths}; minimum outer gap {min(spacing):.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--baseline-jar", type=Path)
    parser.add_argument("--resource-jar", action="append", type=Path, default=[])
    args = parser.parse_args()
    from contextlib import ExitStack
    with ExitStack() as stack:
        if args.jar:
            jar = stack.enter_context(ZipFile(args.jar))
            read = lambda name: json.loads(jar.read(name))
        else:
            read = lambda name: json.loads((RESOURCES / name).read_text("utf-8"))
        baseline = None
        if args.baseline_jar:
            old = stack.enter_context(ZipFile(args.baseline_jar))
            baseline = lambda name: json.loads(old.read(name))
        assets = None
        if args.resource_jar:
            assets = {f.relative_to(RESOURCES).as_posix() for f in RESOURCES.rglob("*.png")}
            for path in args.resource_jar:
                resource = stack.enter_context(ZipFile(path))
                assets.update(resource.namelist())
        validate(read, baseline, assets)


if __name__ == "__main__":
    main()
