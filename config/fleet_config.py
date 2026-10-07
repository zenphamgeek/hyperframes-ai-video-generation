"""Modal Fleet Configuration and Topology Definition.

Defines active Modal Workspaces, endpoints for Qwen DiT 2.1 (T2I),
Qwen Image 2.1 (I2I Edit), LTX-Video, and Vieneu TTS.
"""

import os
from typing import Dict, List, Any

# Active healthy Modal Workspaces hosting Qwen DiT 2.1 (hermes-qwen-img-21) on A100-80GB
QWEN_DIT_WORKSPACES = [
    "verticalresilience",
    "lovenovel",
    "mvlm",
    "zenonmind",
    "mojopham",
]

# Standard endpoints for hermes-qwen-img-21 across workspaces
DIT_WORKER_ENDPOINTS = [
    {
        "workspace": ws,
        "app": "hermes-qwen-img-21",
        "generate_url": f"https://{ws}--hermes-qwen-img-21-qwenimg21worker-generate.modal.run",
        "edit_url": f"https://{ws}--hermes-qwen-img-21-qwenimg21worker-edit.modal.run",
        "health_url": f"https://{ws}--hermes-qwen-img-21-qwenimg21worker-health.modal.run",
        "gpu": "A100-80GB",
        "pipeline": "QwenImage21Pipeline",
        "model": "Qwen/Qwen-Image-2.1",
    }
    for ws in QWEN_DIT_WORKSPACES
]

# Dedicated Qwen Image 2.1 Edit workers (graydoom-qwen-image-21-edit)
QWEN_EDIT_WORKERS = [
    {
        "workspace": "lovenovel",
        "app": "graydoom-qwen-image-21-edit",
        "edit_url": "https://lovenovel--graydoom-qwen-image-21-edit-qwenimage21edit-edit.modal.run",
        "health_url": "https://lovenovel--graydoom-qwen-image-21-edit-qwenimage21edit-health.modal.run",
        "gpu": "A100-80GB",
        "pipeline": "QwenImage21Pipeline",
        "model": "Qwen/Qwen-Image-2.1",
        "pinned_revision": "d26bb61231c349cf6b7896fa83353113880e1ba3",
    }
]

# LTX-Video 2.5 Generation Engine
LTX_VIDEO_CONFIG = {
    "workspace": "verticalresilience",
    "app": "hermes-neural-ltxvideo",
    "gpu": "A100-80GB",
    "model": "Lightricks/LTX-Video",
}

# Vieneu TTS Audio Worker
VIENEU_TTS_CONFIG = {
    "workspace": "lovenovel",
    "app": "vieneu-tts-worker",
    "endpoint": "https://lovenovel--vieneu-tts-worker-api.modal.run",
}

# Supported Aspect Ratios for Qwen DiT 2.1
NATIVE_ASPECT_RATIOS = {
    "9:16": (1080, 1920),       # Vertical Short / Reel / Story (HD)
    "9:16_hi": (1536, 2752),    # Vertical Ultra DiT
    "16:9": (1920, 1080),       # Landscape Cinematic HD
    "16:9_hi": (2752, 1536),    # Landscape Cinematic Ultra DiT
    "1:1": (1024, 1024),        # Square Feed
    "1:1_hi": (2048, 2048),     # Square Ultra DiT
    "4:3": (2048, 1536),
    "3:4": (1536, 2048),
}

DEFAULT_PARAMS = {
    "steps": 40,
    "guidance_scale": 5.0,
    "seed": 42,
    "timeout_seconds": 300,      # Modal cold start + A100 inference buffer
    "max_parallel_workers": 5,   # Parallel fleet concurrency
}
