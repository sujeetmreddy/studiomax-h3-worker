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
    "# studiomax v3: Spectrum acceleration for native H3 (~30% fewer transformer\n"
    "# evals at matched quality; no extra python deps). Pinned for reproducibility.\n"
    "RUN git clone --depth 1 --branch v0.1.8 "
    "https://github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3 "
    "/comfyui/custom_nodes/ComfyUI-Spectrum-MiniMax-H3\n\n"
    "# studiomax v3: SageAttention available but OFF unless the endpoint sets\n"
    "# SAGE_ATTENTION=1 (sm_89 FP8-PV kernels have unreproduced noise reports).\n"
    "RUN uv pip install sageattention || echo 'sageattention install failed - opt-in only'\n\n"
    + anchor
)

count = src.count(anchor)
if count != 1:
    print(f"ERROR: expected exactly 1 anchor occurrence, found {count} — upstream drifted")
    sys.exit(1)

open(path, "w").write(src.replace(anchor, addition))
print("Dockerfile patched: KJNodes baked in before the smoke test")
