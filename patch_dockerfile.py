#!/usr/bin/env python3
"""Insert KJNodes (ColorMatch — per-clip grade lock against the scene plate)
into upstream's Dockerfile, BEFORE the build-time CPU smoke test so a broken
node import fails the build, not a live worker.

Installs with `uv pip` while /opt/venv is on PATH — the venv start.sh actually
launches ComfyUI with (the two-venv trap). Fails loudly if the anchor drifted.
"""
import sys

path = sys.argv[1]
src = open(path).read()

anchor = "RUN cd /comfyui && timeout 300 python main.py --quick-test-for-ci --cpu"
addition = (
    "# studiomax: KJNodes for ColorMatch (scene-plate grade lock)\n"
    "RUN git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes "
    "/comfyui/custom_nodes/ComfyUI-KJNodes \\\n"
    "    && uv pip install -r /comfyui/custom_nodes/ComfyUI-KJNodes/requirements.txt\n\n"
    + anchor
)

count = src.count(anchor)
if count != 1:
    print(f"ERROR: expected exactly 1 anchor occurrence, found {count} — upstream drifted")
    sys.exit(1)

open(path, "w").write(src.replace(anchor, addition))
print("Dockerfile patched: KJNodes baked in before the smoke test")
