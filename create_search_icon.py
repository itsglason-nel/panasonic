from PIL import Image, ImageDraw
import os

base_dir = r"c:\Users\DELL\Desktop\Panasonic Project\Panasonic Web\docs\assets"
os.makedirs(base_dir, exist_ok=True)
icon_path = os.path.join(base_dir, "search_icon.png")

# Make a thicker, more visible search icon
img = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse((3, 3, 16, 16), outline=(255, 255, 255, 255), width=3)
draw.line((13, 13, 21, 21), fill=(255, 255, 255, 255), width=4)

img.save(icon_path)
print(f"Generated bold search icon at {icon_path}")
