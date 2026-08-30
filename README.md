# studiomax-h3-worker

RunPod serverless worker image for **MiniMax H3** (Hailuo 3.0, open weights) in ComfyUI —
used by StudioMax v2 as its self-hosted video engine.

This repo is a thin patch layer over [runpod-workers/worker-comfyui](https://github.com/runpod-workers/worker-comfyui)
`5.8.7`, rebuilt with `COMFYUI_VERSION=0.34.0` (native H3 nodes need >= 0.30.0):

1. **`patch_handler.py`** — upstream only returns `node_output["images"]`; ComfyUI's
   `SaveVideo` history entries live under other keys, so H3 mp4s would be dropped.
   The patch merges `video/videos/gifs/audio` entries into the same return path.
2. **`extra_model_paths.append.yaml`** — upstream maps only classic folder names
   (`unet:`, `clip:`); this adds `diffusion_models:`/`text_encoders:` so the
   Comfy-Org H3 files resolve from the network volume at their canonical paths.

Image: `ghcr.io/sujeetmreddy/studiomax-h3-worker:v1` (build via GitHub Actions on push).
After the first build, flip the GHCR package to **public** (GitHub → Packages → settings)
so RunPod can pull it — there is no API for that toggle.

Expected network volume layout (`/runpod-volume/models/...`):

```
diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors   19.5 GB
diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors  19.5 GB
text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors          14.6 GB
vae/minimax_h3_video_vae_fp16.safetensors                            4.9 GB
vae/minimax_h3_audio_vae_fp32.safetensors                            0.6 GB
loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors     1.8 GB
loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors      1.8 GB
loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors 1.8 GB
```

Provisioning (volume + download pod + endpoint) is scripted in the StudioMax repo:
`scripts/provision-h3.sh`.

License note: commercial use of locally generated H3 output requires a MiniMax
commercial license (sold via comfy.org/minimax/license). Dev/testing is fine.
