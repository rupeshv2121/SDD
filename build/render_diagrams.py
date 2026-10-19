"""Write every diagram to ../diagrams/<id>.mmd and render ../images/<id>.png.

Usage: python render_diagrams.py <path-to-mmdc> [id ...]
"""
import json
import pathlib
import subprocess
import sys

from sdd_diagrams import D

HERE = pathlib.Path(__file__).parent
SRC = HERE.parent / "diagrams"
IMG = HERE.parent / "images"
SRC.mkdir(exist_ok=True)
IMG.mkdir(exist_ok=True)

mmdc = sys.argv[1]
only = set(sys.argv[2:])

cfg = HERE / "mermaid-config.json"
cfg.write_text(json.dumps({
    "theme": "neutral",
    "themeVariables": {"fontFamily": "Arial, Helvetica, sans-serif", "fontSize": "15px"},
    "flowchart": {"htmlLabels": True, "curve": "basis", "nodeSpacing": 34, "rankSpacing": 42},
    "er": {"useMaxWidth": False},
}))
pup = HERE / "puppeteer-config.json"
pup.write_text(json.dumps({
    "executablePath": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "headless": "new",
}))

failed = []
for key, src in D.items():
    if only and key not in only:
        continue
    mmd = SRC / f"{key}.mmd"
    mmd.write_text(src.strip() + "\n", encoding="utf-8")
    png = IMG / f"{key}.png"
    r = subprocess.run(
        [mmdc, "-i", str(mmd), "-o", str(png), "-c", str(cfg), "-p", str(pup),
         "-s", "2.2", "-b", "white", "-q"],
        capture_output=True, text=True, shell=True,
    )
    if r.returncode != 0 or not png.exists():
        failed.append(key)
        print("FAIL", key, (r.stderr or r.stdout)[-600:])
    else:
        print("ok  ", key)
print("failed:", failed)
