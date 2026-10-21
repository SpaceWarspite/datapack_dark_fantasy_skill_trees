import argparse
import copy
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/main/resources"
START = "darkfantasy:mage_01"


def read_node(read, skill_id):
    return read(f"data/darkfantasy/skills/{skill_id.split(':')[1]}.json")


def branches(nodes):
    adjacency = defaultdict(set)
    for skill_id, node in nodes.items():
        for key in ("directConnections", "longConnections", "oneWayConnections"):
            for target in node[key]:
                if START not in (skill_id, target):
                    adjacency[skill_id].add(target)
                    adjacency[target].add(skill_id)
    remaining = set(nodes) - {START}
    groups = []
    while remaining:
        seed = min(remaining, key=lambda id: int(id.split('_')[-1]))
        group, pending = {seed}, [seed]
        while pending:
            for target in adjacency[pending.pop()] - group:
                group.add(target)
                pending.append(target)
        remaining -= group
        groups.append(group)
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-jar", required=True, type=Path)
    parser.add_argument("--factor", required=True, type=Decimal)
    parser.add_argument("--replace-factor", type=Decimal)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    assert args.factor.is_finite() and args.factor > 1, "Factor must be finite and greater than one"
    if args.replace_factor is not None:
        assert args.replace_factor.is_finite() and args.replace_factor > 1, "Previous factor must be finite and greater than one"
    assert not args.jar or args.check, "Packaged JARs can only be checked"
    with ZipFile(args.baseline_jar) as old:
        baseline = lambda path: json.loads(old.read(path))
        tree = baseline("data/darkfantasy/skill_trees/mage.json")
        nodes = {id: read_node(baseline, id) for id in tree["skillIds"]}
        groups = branches(nodes)
        chrono = next(group for group in groups if "darkfantasy:mage_17" in group)
        assert chrono == {f"darkfantasy:mage_{i:02d}" for i in (*range(10, 18), *range(103, 116))}
        excluded = chrono | {START}
        count_positive = count_negative = count_changed = 0
        expected = {}
        summaries = []
        for skill_id, node in nodes.items():
            result = copy.deepcopy(node)
            if skill_id not in excluded:
                for bonus in result["bonuses"]:
                    assert bonus["type"] == "skilltree:attribute", f"Unsupported bonus: {skill_id}, {bonus}"
                    assert bonus["operation"] in (0, 1), f"Unsupported operation: {skill_id}"
                    amount = Decimal(str(bonus["amount"]))
                    count_positive += amount > 0
                    count_negative += amount < 0
                    bonus["amount"] = float(amount * args.factor)
            count_changed += result != node
            expected[skill_id] = result
        assert (count_changed, count_positive, count_negative) == (92, 146, 9)
        for group in groups:
            if group == chrono:
                continue
            totals = defaultdict(Decimal)
            for skill_id in group:
                for bonus in nodes[skill_id]["bonuses"]:
                    sign = "+" if bonus["amount"] >= 0 else "-"
                    totals[bonus["attribute"], bonus["operation"], sign] += Decimal(str(bonus["amount"]))
            summaries.append({
                "skills": sorted(group, key=lambda id: int(id.split('_')[-1])),
                "modifiers": [{"attribute": key[0], "operation": key[1], "sign": key[2],
                               "before": str(value), "after": str(value * args.factor)} for key, value in sorted(totals.items())],
            })
        if args.check:
            if args.jar:
                with ZipFile(args.jar) as jar:
                    assert json.loads(jar.read("data/darkfantasy/skill_trees/mage.json")) == tree
                    for skill_id, result in expected.items():
                        actual = read_node(lambda path: json.loads(jar.read(path)), skill_id)
                        assert actual == result, f"Wrong scaling or unexpected change: {skill_id}"
            else:
                assert json.loads((RESOURCES / "data/darkfantasy/skill_trees/mage.json").read_text("utf-8")) == tree
                for skill_id, result in expected.items():
                    actual = read_node(lambda path: json.loads((RESOURCES / path).read_text("utf-8")), skill_id)
                    assert actual == result, f"Wrong scaling or unexpected change: {skill_id}"
        else:
            for skill_id, result in expected.items():
                path = RESOURCES / f"data/darkfantasy/skills/{skill_id.split(':')[1]}.json"
                actual = json.loads(path.read_text("utf-8"))
                allowed = [nodes[skill_id], result]
                if args.replace_factor is not None:
                    previous = copy.deepcopy(nodes[skill_id])
                    if skill_id not in excluded:
                        for bonus in previous["bonuses"]:
                            bonus["amount"] = float(Decimal(str(bonus["amount"])) * args.replace_factor)
                    allowed.append(previous)
                assert actual in allowed, f"Source has unrelated edits: {skill_id}"
            for skill_id, result in expected.items():
                if result != nodes[skill_id]:
                    path = RESOURCES / f"data/darkfantasy/skills/{skill_id.split(':')[1]}.json"
                    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf-8")
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({
                "baseline": str(args.baseline_jar), "factor": str(args.factor), "branches": len(summaries),
                "changed_skills": count_changed, "positive_modifiers": count_positive,
                "negative_modifiers": count_negative, "chronomancer_skills_unchanged": len(chrono),
                "common_start_unchanged": True, "branch_totals": summaries,
            }, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(f"{'PASS' if args.check else 'SCALED'}: {len(summaries)} branches, {count_changed} skills, "
              f"{count_positive} buffs and {count_negative} debuffs x{args.factor}; all {len(chrono)} Chronomancer skills and shared start unchanged")


if __name__ == "__main__":
    main()
