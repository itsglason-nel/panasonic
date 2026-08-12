from PIL import Image, ImageDraw, ImageFont
import os

base_dir = r"c:\Users\DELL\Desktop\Panasonic Project\Panasonic Web\docs\assets"
os.makedirs(base_dir, exist_ok=True)
ico_path = os.path.join(base_dir, 'panasonic_logo.ico')

sizes = [128, 64, 48, 32, 24, 16]
icon_layers = []

for s in sizes:
    # Render massively and shrink to perfectly anti-alias the circle and P for every layer
    big_size = 1024
    img = Image.new('RGBA', (big_size, big_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Perfect black circle
    draw.ellipse([0, 0, big_size, big_size], fill=(0, 0, 0, 255))
    
    try:
        font = ImageFont.truetype("arialbd.ttf", 750)
    except Exception:
        font = ImageFont.load_default()
        
    text = "P"
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    x = (big_size - text_width) / 2 - left
    y = (big_size - text_height) / 2 - top
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Add to layers
    icon_layers.append(img.resize((s, s), Image.Resampling.LANCZOS))

# Save standard ICO
icon_layers[0].save(
    ico_path,
    format='ICO',
    append_images=icon_layers[1:]
)

print("Generated precise circular ICO.")
