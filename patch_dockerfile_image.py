#!/usr/bin/env python3
"""Image-worker v2 Dockerfile patch: Nunchaku (SVDQuant INT4 Qwen-Image)
plus the ComfyUI-nunchaku plugin.

Unlike KJNodes/Spectrum on the video worker, the nunchaku block is inserted
AFTER upstream's CPU smoke test: the runtime wheel ships CUDA kernels and a
GPU-less import check would fail the build for the wrong reason. The wheel
URL is computed from the image's actual torch/python at build time and a 404
fails the build loudly — never a live worker.
"""
import sys

path = sys.argv[1]
src = open(path).read()

anchor = "RUN cd /comfyui && timeout 300 python main.py --quick-test-for-ci --cpu"
addition = (
    anchor + "\n\n"
    "# studiomax image-v2: Nunchaku SVDQuant INT4 runtime + ComfyUI plugin.\n"
    "RUN TV=$(python -c \"import torch;v=torch.__version__.split('+')[0].split('.');print(v[0]+'.'+v[1])\") \\\n"
    "    && PY=$(python -c \"import sys;print(f'cp{sys.version_info[0]}{sys.version_info[1]}')\") \\\n"
    "    && W=\"nunchaku-1.2.0+torch${TV}-${PY}-${PY}-linux_x86_64.whl\" \\\n"
    "    && echo \"installing $W\" \\\n"
    "    && uv pip install \"https://github.com/nunchaku-tech/nunchaku/releases/download/v1.2.0/${W}\"\n\n"
    "# The nunchaku wheels link libcudart.so.13 (cu13 toolchain) while this\n"
    "# image ships torch+cu12.8 — provide CUDA 13 runtime side-by-side and\n"
    "# register it with the dynamic linker; the two cudarts coexist fine.\n"
    "RUN uv pip install nvidia-cuda-runtime-cu13 \\\n"
    "    && LIBDIR=$(python -c \"import nvidia.cuda_runtime, os; print(os.path.join(os.path.dirname(nvidia.cuda_runtime.__file__), 'lib'))\") \\\n"
    "    && echo \"$LIBDIR\" > /etc/ld.so.conf.d/cuda13-runtime.conf \\\n"
    "    && ldconfig \\\n"
    "    && python -c \"import ctypes; ctypes.CDLL('libcudart.so.13'); print('libcudart.so.13 resolves')\"\n\n"
    "RUN git clone --depth 1 --branch v1.2.0 https://github.com/nunchaku-tech/ComfyUI-nunchaku "
    "/comfyui/custom_nodes/ComfyUI-nunchaku \\\n"
    "    && uv pip install -r /comfyui/custom_nodes/ComfyUI-nunchaku/requirements.txt\n"
)

count = src.count(anchor)
if count != 1:
    print(f"ERROR: expected exactly 1 anchor occurrence, found {count} — upstream drifted")
    sys.exit(1)

open(path, "w").write(src.replace(anchor, addition))
print("Dockerfile patched: nunchaku runtime + plugin after the CPU smoke test")
