"""Draw assets/app.ico (orange rounded square with a white "PC" monogram)."""

import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "assets", "app.ico")


def draw(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=size // 5, fill="#EA580C")
    try:
        font = ImageFont.truetype("segoeuib.ttf", int(size * 0.42))
    except OSError:
        font = ImageFont.load_default()
    d.text((size / 2, size / 2), "PC", font=font, fill="white", anchor="mm")
    return img


if __name__ == "__main__":
    draw().save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Wrote", os.path.normpath(OUT))
