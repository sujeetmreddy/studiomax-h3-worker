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
    "# studiomax v4: RIFE frame interpolation (ComfyUI-Frame-Interpolation) for the\n"
    "# 48fps delivery option — H3 renders 24fps natively; the graph appends\n"
    "# 'RIFE VFI' x2 when the project asks for 48. Pinned commit; no-cupy deps\n"
    "# (RIFE needs neither cupy nor taichi). rife47 weights baked in so a fresh\n"
    "# worker never hits GitHub/HF at render time.\n"
    "RUN git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation "
    "/comfyui/custom_nodes/ComfyUI-Frame-Interpolation \\\n"
    "    && cd /comfyui/custom_nodes/ComfyUI-Frame-Interpolation \\\n"
    "    && git checkout 26545cc2dd95bc3d27f056016300673bdeee78f5 \\\n"
    "    && uv pip install -r requirements-no-cupy.txt \\\n"
    "    && mkdir -p ckpts/rife \\\n"
    "    && curl -fL --retry 5 -o ckpts/rife/rife47.pth "
    "https://huggingface.co/marduk191/rife/resolve/main/rife47.pth \\\n"
    "    && test $(stat -c %s ckpts/rife/rife47.pth) -gt 20000000\n\n"
    # Upstream's quick-test only fails on a crash; a custom node that fails to
    # IMPORT is just a log line. Gate ours explicitly.
    "RUN cd /comfyui && (timeout 300 python main.py --quick-test-for-ci --cpu > /tmp/qt.log 2>&1; "
    "echo \"exit=$?\" >> /tmp/qt.log) && tail -n 60 /tmp/qt.log && grep -q 'exit=0' /tmp/qt.log "
    "&& ! grep -qE '(IMPORT FAILED|Cannot import).*(Frame-Interpolation|KJNodes|Spectrum)' /tmp/qt.log\n\n"
    + anchor
)

count = src.count(anchor)
if count != 1:
    print(f"ERROR: expected exactly 1 anchor occurrence, found {count} — upstream drifted")
    sys.exit(1)

open(path, "w").write(src.replace(anchor, addition))
print("Dockerfile patched: KJNodes + Spectrum + RIFE baked in before the smoke test")
