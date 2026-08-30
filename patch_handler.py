#!/usr/bin/env python3
"""Patch worker-comfyui's handler.py to also return video/audio outputs.

Upstream only collects node_output["images"]; ComfyUI's SaveVideo writes its
mp4 under a different history key, so H3 results would be silently dropped
(the handler even logs "unhandled output keys"). This inserts a merge step so
any {filename,...} entries under video/videos/gifs/audio are treated like
images and flow through the same base64/S3 return path.

Fails loudly (non-zero exit) if the upstream anchor line drifted.
"""
import sys

path = sys.argv[1]
src = open(path).read()

anchor = "        for node_id, node_output in outputs.items():"
addition = (
    anchor
    + "\n"
    + "            # studiomax patch: collect video/audio outputs (SaveVideo etc.)\n"
    + "            _merged = list(node_output.get(\"images\") or [])\n"
    + "            for _k in (\"video\", \"videos\", \"gifs\", \"audio\"):\n"
    + "                _v = node_output.get(_k)\n"
    + "                if isinstance(_v, list):\n"
    + "                    _merged.extend(\n"
    + "                        x for x in _v if isinstance(x, dict) and x.get(\"filename\")\n"
    + "                    )\n"
    + "            node_output = dict(node_output)\n"
    + "            node_output[\"images\"] = _merged\n"
)

count = src.count(anchor)
if count != 1:
    print(f"ERROR: expected exactly 1 anchor occurrence, found {count} — upstream drifted")
    sys.exit(1)

open(path, "w").write(src.replace(anchor, addition))
print("handler.py patched: video/audio outputs now returned")
