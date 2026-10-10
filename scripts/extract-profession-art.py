"""Convert extracted WoW BLP bar atlases to lossless, cropped companion assets."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def read_blp(path):
    data = path.read_bytes()
    magic, _, encoding, _, _, _, width, height = struct.unpack_from("<4sI4B2I", data)
    if magic == b"BLP2" and encoding == 3:
        offset = struct.unpack_from("<I", data, 20)[0]
        size = width * height * 4
        assert len(data[offset:offset + size]) == size, path
        return Image.frombytes("RGBA", (width, height), data[offset:offset + size], "raw", "BGRA")
    image = Image.open(path)
    image.load()
    return image.convert("RGBA")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--members", type=Path, required=True)
    parser.add_argument("--atlases", type=Path, required=True)
    parser.add_argument("--listfile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build", required=True)
    args = parser.parse_args()
    names = dict(line.strip().split(";", 1) for line in args.listfile.read_text().splitlines())
    atlases = {row["ID"]: row for row in csv.DictReader(args.atlases.open())}
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"build": args.build, "source": "Extracted from installed WoW CASC archives", "assets": {}}
    images = {}
    for row in csv.DictReader(args.members.open()):
        atlas = atlases[row["UiTextureAtlasID"]]
        file_id = atlas["FileDataID"]
        path = args.raw_dir / names[file_id]
        if file_id not in images:
            images[file_id] = read_blp(path)
        source = images[file_id]
        left, top = int(row["CommittedLeft"]), int(row["CommittedTop"])
        width, height = int(row["Width"]), int(row["Height"])
        assert left + width <= source.width and top + height <= source.height
        name = row["CommittedName"].lower()
        cropped = source.crop((left, top, left + width, top + height))
        cropped.save(args.output / (name + ".png"))
        manifest["assets"][name] = {
            "file": name + ".png", "width": width, "height": height,
            "sourceFileDataID": int(file_id), "sourcePath": names[file_id],
            "sourceSHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sourceCrop": [left, top, width, height],
            "columns": 2 if name.startswith("skillbar_fill_flipbook_") and height >= 34 else 1,
            "rows": max(1, height // 34) if name.startswith("skillbar_fill_flipbook_") else 1,
        }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported {len(manifest['assets'])} original atlas regions from WoW {args.build}.")


if __name__ == "__main__":
    main()
