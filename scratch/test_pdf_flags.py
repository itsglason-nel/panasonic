import subprocess
import os

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_exe):
    edge_exe = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

test_url = "http://127.0.0.1:8080/internal/print-tag/CW9-U-0003"
out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\Panasonic Web\scratch"

def test_pdf(filename, flags):
    out = os.path.join(out_dir, filename)
    cmd = [edge_exe, "--headless", "--disable-gpu", f"--print-to-pdf={out}", "--run-all-compositor-stages-before-draw"] + flags + [test_url]
    print(f"Testing {filename}...")
    subprocess.run(cmd, capture_output=True)

test_pdf("test_margins.pdf", ["--no-pdf-header-footer"])
test_pdf("test_no_margins.pdf", ["--no-margins"])
test_pdf("test_scale.pdf", ["--no-margins"]) # just checking

print("Tests done.")
