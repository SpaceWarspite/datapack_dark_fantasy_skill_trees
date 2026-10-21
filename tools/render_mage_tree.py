import argparse
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CHRONOMANCER = {f"darkfantasy:mage_{i:02d}" for i in (*range(10, 18), *range(103, 116))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--textures", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    scale, width, height = 2, 860, 1590
    image = Image.new("RGB", (width * 2, height), "#09070f")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 23)
    small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
    with ZipFile(args.textures) as textures:
        for panel, (path, title) in enumerate(((args.before, "До"), (args.after, "После"))):
            with ZipFile(path) as jar:
                tree = json.loads(jar.read("data/darkfantasy/skill_trees/mage.json"))
                nodes = {id: json.loads(jar.read(f"data/darkfantasy/skills/{id.split(':')[1]}.json")) for id in tree["skillIds"]}
                branch = [n for id, n in nodes.items() if id in CHRONOMANCER]
                keystones = sum(n["backgroundTexture"].endswith("/keystone.png") for n in branch)
                title += f": {len(branch)} узлов, кейстоунов {keystones}"
                def location(node):
                    return round(panel * width + width / 2 + node["positionX"] * scale), round(1110 + node["positionY"] * scale)
                draw.text((panel * width + 30, 22), title, font=font, fill="#ffd67e")
                draw.text((panel * width + 30, 62), "План расположения из JSON и текстур мода", font=small, fill="#a99dbb")
                for id, node in nodes.items():
                    for key in ("directConnections", "longConnections", "oneWayConnections"):
                        for target in node[key]:
                            color = "#d9a633" if id in CHRONOMANCER else "#493c26"
                            draw.line((location(node), location(nodes[target])), fill=color, width=3)
                for id, node in nodes.items():
                    size = node["buttonSize"] * scale
                    x, y = location(node)
                    namespace, texture = node["backgroundTexture"].split(":", 1)
                    sheet = Image.open(BytesIO(textures.read(f"assets/{namespace}/{texture}"))).convert("RGBA")
                    tile = sheet.crop((0, 0, sheet.height, sheet.height))
                    if id in CHRONOMANCER:
                        tile.alpha_composite(sheet.crop((sheet.height * 2, 0, sheet.height * 3, sheet.height)))
                    tile = tile.resize((size, size), Image.Resampling.NEAREST)
                    image.paste(tile, (x - size // 2, y - size // 2), tile)
                    namespace, texture = node["iconTexture"].split(":", 1)
                    resource = f"assets/{namespace}/{texture}"
                    provider = jar if resource in jar.namelist() else textures
                    if resource in provider.namelist():
                        icon = Image.open(BytesIO(provider.read(resource))).convert("RGBA")
                        icon = icon.resize((size // 2, size // 2), Image.Resampling.NEAREST)
                        image.paste(icon, (x - size // 4, y - size // 4), icon)
                    if id in CHRONOMANCER:
                        draw.text((x + size // 2 + 3, y - 10), id.split("_")[-1], font=small, fill="#ebe0ff")
    draw.line((width, 10, width, height - 10), fill="#493c55", width=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
