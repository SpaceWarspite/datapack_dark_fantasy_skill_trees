import argparse
import itertools
import json
import math
from collections import Counter
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from validate_chronomancer import BRANCH_IDS, crosses, distance_to_segment, point


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/main/resources"
IDS = {f"darkfantasy:mage_{i}" for i in range(110, 116)}


def validate(read, baseline, chrono_only=False):
    tree = read("data/darkfantasy/skill_trees/mage.json")
    assert len(tree["skillIds"]) == len(set(tree["skillIds"])) == 115, "Expected 115 Mage nodes"
    nodes = {id: read(f"data/darkfantasy/skills/{id.split(':')[1]}.json") for id in tree["skillIds"]}
    assert IDS <= nodes.keys(), "Missing duration skills"
    effects = []
    mana = []
    branch = [nodes[f"darkfantasy:mage_{i}"] for i in range(110, 116)]
    for i, node in enumerate(branch, 110):
        assert node["directConnections"] == [f"darkfantasy:mage_{16 if i == 110 else i - 1}"]
        assert not node["tags"] and not node["isStartingPoint"]
        assert not node["longConnections"] and not node["oneWayConnections"]
        for bonus in node["bonuses"]:
            assert bonus["type"] == "skilltree:attribute"
            if bonus["attribute"] == "darkfantasyskilltrees:self_spell_duration":
                assert bonus["operation"] == 1
                effects.append(Decimal(str(bonus["amount"])))
            elif bonus["attribute"] == "irons_spellbooks:max_mana":
                assert bonus["operation"] == 0 and i == 115
                mana.append(Decimal(str(bonus["amount"])))
            else:
                raise AssertionError(f"Unexpected duration-branch bonus {bonus}")
    assert effects == list(map(Decimal, [".25", ".25", ".5", ".5", ".5", ".5"]))
    assert sum(effects) == Decimal("2.5") and mana == [Decimal("-50")]
    assert Counter(n["backgroundTexture"].split("/")[-1] for n in branch) == {"lesser.png": 4, "notable.png": 1, "keystone.png": 1}
    edges = {frozenset((id, other)) for id, node in nodes.items() for key in ("directConnections", "longConnections", "oneWayConnections") for other in node[key]}
    gaps = []
    for a, b in itertools.combinations(nodes.values(), 2):
        pair = {a["id"], b["id"]}
        if not pair & IDS or frozenset(pair) in edges:
            continue
        gap = math.dist(point(a), point(b)) - (a["buttonSize"] + b["buttonSize"]) / 2
        assert gap >= 8, f"Crowded duration branch {pair}: {gap}"
        gaps.append(gap)
    for edge in edges:
        if not edge & IDS:
            continue
        a, b = sorted(edge)
        for id, node in nodes.items():
            if id not in edge:
                assert distance_to_segment(point(node), point(nodes[a]), point(nodes[b])) >= node["buttonSize"] / 2, f"Link crosses button {id}"
        for other in edges:
            if edge & other:
                continue
            c, d = sorted(other)
            assert not crosses(point(nodes[a]), point(nodes[b]), point(nodes[c]), point(nodes[d])), f"Crossing duration links {edge}, {other}"
    old_tree = baseline("data/darkfantasy/skill_trees/mage.json")
    assert len(old_tree["skillIds"]) in (109, 115)
    assert tree["skillLimitations"] == old_tree["skillLimitations"]
    for id in old_tree["skillIds"]:
        if chrono_only and id not in BRANCH_IDS | IDS:
            continue
        old = baseline(f"data/darkfantasy/skills/{id.split(':')[1]}.json")
        current = nodes[id]
        if id in BRANCH_IDS | IDS:
            old = {key: value for key, value in old.items() if key not in ("positionX", "positionY")}
            current = {key: value for key, value in current.items() if key not in ("positionX", "positionY")}
        assert current == old, f"Previous skill changed beyond Chronomancer placement: {id}"
    for lang in ("ru_ru", "en_us"):
        strings = read(f"assets/darkfantasy/lang/{lang}.json")
        assert strings["attribute.darkfantasyskilltrees.self_spell_duration"]
        for id in IDS:
            assert strings[f"skill.darkfantasy.{id.split(':')[1]}.name"]
            assert strings[f"skill.darkfantasy.{id.split(':')[1]}.description"]
    scope = "Chronomancer" if chrono_only else "prior skill"
    print(f"PASS: six skills from mage_16, +250% duration, -50 mana, {scope} definitions preserved; minimum gap {min(gaps):.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--baseline-jar", type=Path, required=True)
    parser.add_argument("--chrono-only", action="store_true")
    args = parser.parse_args()
    with ZipFile(args.baseline_jar) as old:
        baseline = lambda path: json.loads(old.read(path))
        if args.jar:
            with ZipFile(args.jar) as new:
                validate(lambda path: json.loads(new.read(path)), baseline, args.chrono_only)
        else:
            validate(lambda path: json.loads((RESOURCES / path).read_text("utf-8")), baseline, args.chrono_only)


if __name__ == "__main__":
    main()
