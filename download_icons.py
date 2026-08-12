import os
import urllib.request

base_dir = r"c:\Users\DELL\Desktop\Panasonic Project\Panasonic Web"
assets_dir = os.path.join(base_dir, 'docs', 'assets')

if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

icons = {
    "info": "https://img.icons8.com/ios-filled/50/ffffff/info.png",
    "globe": "https://img.icons8.com/ios-filled/50/ffffff/domain.png",
    "play": "https://img.icons8.com/ios-filled/50/ffffff/play.png",
    "stop": "https://img.icons8.com/ios-filled/50/ffffff/stop.png",
    "restart": "https://img.icons8.com/ios-filled/50/ffffff/restart.png"
}

for name, url in icons.items():
    filepath = os.path.join(assets_dir, f"{name}.png")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        with open(filepath, 'wb') as f:
            f.write(response.read())
    print(f"Downloaded {name}.png")
