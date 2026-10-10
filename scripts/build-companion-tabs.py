"""Prepare companion tab artwork from the addon's source textures."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent
output = root / "Companion/assets/theme"
for name in ("TabInactive", "TabActive"):
    image = Image.open(root / "Media" / (name + ".tga")).convert("RGBA")
    width, height = image.size
    if name == "TabActive":
        glow = Image.new("RGBA", image.size)
        draw = ImageDraw.Draw(glow)
        for y in range(height):
            draw.line((0, y, width-1, y), fill=(205, 151, 49, round(90*(1-y/(height-1))**1.3)))
        image = Image.alpha_composite(image, glow)
    mask = Image.new("L", image.size)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width-1, height-1), radius=6, fill=255)
    draw.rectangle((0, 6, width-1, height-1), fill=255)
    image.putalpha(mask)
    image.save(output / (name + ".png"))
