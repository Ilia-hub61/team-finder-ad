import random
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

AVATAR_SIZE = 400
FONT_PATH = (
    settings.BASE_DIR / "static" / "fonts" / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
)

AVATAR_COLORS = [
    ("#DBEAFE", "#1E3A8A"),
    ("#DCFCE7", "#14532D"),
    ("#FEF3C7", "#78350F"),
    ("#FCE7F3", "#831843"),
    ("#EDE9FE", "#4C1D95"),
    ("#FFE4E6", "#881337"),
    ("#CCFBF1", "#134E4A"),
    ("#FFEDD5", "#7C2D12"),
]


def _load_font(size):
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.load_default(size)


def generate_avatar(name):
    letter = (name.strip()[:1] or "?").upper()
    background, foreground = random.choice(AVATAR_COLORS)
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), background)
    draw = ImageDraw.Draw(image)
    font = _load_font(int(AVATAR_SIZE * 0.5))
    left, top, right, bottom = draw.textbbox((0, 0), letter, font=font)
    x = (AVATAR_SIZE - (right - left)) / 2 - left
    y = (AVATAR_SIZE - (bottom - top)) / 2 - top
    draw.text((x, y), letter, font=font, fill=foreground)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
