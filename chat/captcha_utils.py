import random
import string
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def generate_captcha_text(length=6):
    """Generate a random alphanumeric string for CAPTCHA."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_captcha_image(text):
    """Generate a CAPTCHA image from the given text."""
    width, height = 180, 60
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    font_path = "arial.ttf"  # You might need to specify a full path or ensure it's available
    try:
        font = ImageFont.truetype(font_path, 40)
    except IOError:
        font = ImageFont.load_default() # Fallback to default font

    draw = ImageDraw.Draw(image)
    
    # Draw text
    draw.text((10, 5), text, font=font, fill=(0, 0, 0))

    # Add some noise
    for _ in range(1500):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    # Add lines
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()
