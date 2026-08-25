import random
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# Avoid visually-confusing characters (0/O, 1/l/I).
CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_text(length=5):
    return "".join(random.choices(CAPTCHA_CHARS, k=length))


def _generate_image(text, width=200, height=70):
    bg = tuple(random.randint(230, 255) for _ in range(3))
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Noise lines behind the text.
    for _ in range(6):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        color = tuple(random.randint(150, 200) for _ in range(3))
        draw.line((x1, y1, x2, y2), fill=color, width=1)

    # Speckle noise.
    for _ in range(80):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        color = tuple(random.randint(150, 200) for _ in range(3))
        draw.point((x, y), fill=color)

    font = ImageFont.load_default(size=36)
    char_spacing = width // (len(text) + 1)

    for i, ch in enumerate(text):
        char_color = tuple(random.randint(0, 90) for _ in range(3))

        # Draw each character on its own transparent tile so it can be
        # rotated independently — this is what makes it look "real"
        # rather than a flat row of text.
        char_img = Image.new("RGBA", (50, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((10, 5), ch, font=font, fill=char_color)

        angle = random.randint(-30, 30)
        rotated = char_img.rotate(angle, expand=True)

        x = char_spacing * (i + 1) - 20 + random.randint(-5, 5)
        y = random.randint(5, height - 45)
        img.paste(rotated, (x, y), rotated)

    # A wavy line across the text for extra distortion.
    mid = height // 2
    draw.line(
        [
            (0, mid + random.randint(-10, 10)),
            (width // 2, mid + random.randint(-10, 10)),
            (width, mid + random.randint(-10, 10)),
        ],
        fill=(120, 120, 120),
        width=2,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_captcha():
    """Returns (text, base64_png_string). Compare user input against
    `text` case-insensitively."""
    text = _generate_text()
    png_bytes = _generate_image(text)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return text, b64
      
