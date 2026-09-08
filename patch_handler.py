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
src = src.replace(anchor, addition)

# Second patch: a worker whose ComfyUI process has DIED must not linger.
# Upstream's check_server() notices the exited PID and returns False — the
# handler then fails every subsequent job in ~100 ms ("not reachable after
# multiple retries") while RunPod keeps reporting the worker idle/ready.
# Exiting the worker process makes RunPod replace it with a fresh container.
zombie_anchor = (
    '                "Server will not become reachable."\n'
    "            )\n"
    "            return False\n"
)
zombie_fix = (
    '                "Server will not become reachable."\n'
    "            )\n"
    "            # studiomax patch: never linger as a zombie — exit so RunPod\n"
    "            # replaces this worker instead of failing every job it is handed.\n"
    "            os._exit(3)\n"
    "            return False\n"
)
zcount = src.count(zombie_anchor)
if zcount != 1:
    print(f"ERROR: expected exactly 1 zombie anchor occurrence, found {zcount} — upstream drifted")
    sys.exit(1)
src = src.replace(zombie_anchor, zombie_fix)
if "import os" not in src:
    src = "import os\n" + src

open(path, "w").write(src)
print("handler.py patched: video/audio outputs returned; dead-ComfyUI workers exit instead of zombie-ing")
