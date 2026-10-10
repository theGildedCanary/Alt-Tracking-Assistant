"""Render original profession-specific artwork extracted from WoW's atlases."""
from functools import lru_cache
import json
from pathlib import Path
import tkinter as tk

from PIL import Image, ImageTk

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "profession_bars"
KITS = {171: "alchemy", 164: "blacksmithing", 185: "cooking", 333: "enchanting",
        202: "engineering", 356: "fishing", 182: "herbalism", 773: "inscription",
        755: "jewelcrafting", 165: "leatherworking", 186: "mining", 393: "skinning", 197: "tailoring"}


def profession_kit(profession):
    try:
        return KITS.get(int(profession.get("skillLineID")), "defaultblue")
    except (TypeError, ValueError):
        name = str(profession.get("name", "")).lower().replace(" ", "")
        return name if name in KITS.values() else "defaultblue"


@lru_cache(maxsize=1)
def manifest():
    return json.loads((ASSET_DIR / "manifest.json").read_text())


@lru_cache(maxsize=32)
def asset(name):
    info = manifest()["assets"][name]
    with Image.open(ASSET_DIR / info["file"]) as image:
        return image.convert("RGBA"), info


def frame_count(kit):
    _, info = asset("skillbar_fill_flipbook_" + kit)
    return info["columns"] * info["rows"]


@lru_cache(maxsize=128)
def scaled_fill(kit, width, height, frame):
    sheet, info = asset("skillbar_fill_flipbook_" + kit)
    columns, rows = info["columns"], info["rows"]
    frame = max(0, min(columns * rows - 1, frame))
    x, y = frame % columns, frame // columns
    w, h = sheet.width // columns, sheet.height // rows
    return sheet.crop((x*w, y*h, (x+1)*w, (y+1)*h)).resize((width, height), Image.Resampling.LANCZOS)


def render_bar_image(kit, width, height, fraction, frame=0):
    width, height = max(11, int(width)), max(8, int(height))
    fraction = max(0, min(1, fraction))
    background, _ = asset("professions-skillbar-bg")
    border, _ = asset("professions-skillbar-frame")
    result = background.resize((width, height), Image.Resampling.LANCZOS)
    # The border atlas is resized with the bar, so its insets must scale too.
    inset_x, inset_y = max(1, round(width*5/451)), max(1, round(height*3/29))
    inner_width, inner_height = max(1, width-2*inset_x), max(1, round(height*18/29))
    interior = Image.new("RGBA", (inner_width, inner_height))
    fill_width = round(inner_width * fraction)
    if fill_width:
        fill = scaled_fill(kit, inner_width, inner_height, frame)
        interior.alpha_composite(fill.crop((0, 0, fill_width, inner_height)))
        flare_name = "skillbar_flare_" + kit
        if fraction < 1 and flare_name in manifest()["assets"]:
            flare, _ = asset(flare_name)
            flare = flare.resize((max(1, round(height*53/29)), max(1, round(height*16/29))), Image.Resampling.LANCZOS)
            interior.alpha_composite(flare, (fill_width-flare.width, (inner_height-flare.height)//2))
    result.alpha_composite(interior, (inset_x, inset_y))
    result.alpha_composite(border.resize((width, height), Image.Resampling.LANCZOS))
    return result


class NativeProfessionBar(tk.Canvas):
    def __init__(self, parent, profession, tier, height, font, background):
        super().__init__(parent, height=height, highlightthickness=0, bg=background)
        self.kit = profession_kit(profession)
        self.art_height, self.font = height, font
        maximum = tier.get("maxSkillLevel") or 0
        current = tier.get("skillLevel") or 0
        self.fraction = current/maximum if maximum > 0 else 0
        self.label = f"{tier.get('name') or 'Profession skill'}   {current:g} / {maximum:g}"
        self._elapsed, self._timer, self._photo = 0, None, None
        self.bind("<Configure>", self._restart)
        self.bind("<Map>", self._restart)
        self.bind("<Unmap>", self._stop)
        self.bind("<Destroy>", self._stop)

    def _stop(self, event=None):
        if self._timer is not None:
            self.after_cancel(self._timer)
            self._timer = None

    def _restart(self, event=None):
        self._stop()
        self._elapsed = 0
        width = getattr(event, "width", None)
        self._draw(width if isinstance(width, (int, float)) else self.winfo_width())
        if self.winfo_ismapped() and frame_count(self.kit) > 1:
            self._timer = self.after(33, self._tick)

    def _tick(self):
        self._timer = None
        self._elapsed = min(2, self._elapsed + .033)
        self._draw(self.winfo_width())
        if self._elapsed < 2 and self.winfo_ismapped():
            self._timer = self.after(33, self._tick)

    def _draw(self, width):
        frame = min(frame_count(self.kit)-1, int(self._elapsed/2*frame_count(self.kit)))
        art = render_bar_image(self.kit, width, self.art_height, self.fraction, frame)
        photo = ImageTk.PhotoImage(art, master=self)
        self.delete("all")
        self.create_image(0, 0, image=photo, anchor="nw")
        self._photo = photo
        y = max(1, round(self.art_height*3/29)) + max(1, round(self.art_height*18/29)) / 2
        self.create_text(width/2+1, y+1, text=self.label, fill="black", font=self.font)
        self.create_text(width/2, y, text=self.label, fill="white", font=self.font)
