from PIL import Image, ImageDraw, ImageFont
import os

base_dir = r"c:\Users\DELL\Desktop\Panasonic Project\Panasonic Web\docs\assets"
os.makedirs(base_dir, exist_ok=True)
png_path = os.path.join(base_dir, 'panasonic_logo.png')

size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Black circle
draw.ellipse([0, 0, size, size], fill=(0, 0, 0, 255))

try:
    font = ImageFont.truetype("arialbd.ttf", 375)
except Exception:
    font = ImageFont.load_default()

text = "P"
# Get the exact ink boundaries
left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
text_width = right - left
text_height = bottom - top

# Mathematically perfect visual centering
x = (size - text_width) / 2 - left
y = (size - text_height) / 2 - top

draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

# Save as a single ultra-high-resolution PNG
img.save(png_path, format='PNG')
print("Generated high-res PNG icon.")
