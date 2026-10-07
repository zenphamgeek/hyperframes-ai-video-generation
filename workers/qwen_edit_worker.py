"""Qwen Image 2.1 Image-to-Image Editing Worker.

Supports character face & attire preservation, style modification,
inpainting with masks, and dual-workspace failover (lovenovel / verticalresilience).
"""

import os
import sys
import time
import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import requests
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.fleet_config import QWEN_EDIT_WORKERS, DIT_WORKER_ENDPOINTS


class QwenEditWorker:
    """Worker client for Qwen Image 2.1 Editing."""

    def __init__(self, edit_workers: Optional[List[Dict[str, Any]]] = None, timeout: int = 360):
        self.edit_workers = edit_workers or QWEN_EDIT_WORKERS
        self.fallback_workers = DIT_WORKER_ENDPOINTS
        self.timeout = timeout

    def check_health(self, worker_info: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        """Check health of a dedicated edit worker."""
        url = worker_info["health_url"]
        ws = worker_info["workspace"]
        t0 = time.time()
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Modal-Fleet-Client/1.0"})
            elapsed = round(time.time() - t0, 2)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "workspace": ws,
                    "status": "healthy",
                    "modelId": data.get("modelId", worker_info["model"]),
                    "modelRevision": data.get("modelRevision", worker_info.get("pinned_revision")),
                    "pipeline": data.get("pipeline", worker_info["pipeline"]),
                    "elapsed_s": elapsed,
                    "url": url,
                }
            return {
                "workspace": ws,
                "status": f"http_{resp.status_code}",
                "elapsed_s": elapsed,
                "url": url,
            }
        except Exception as e:
            return {
                "workspace": ws,
                "status": "unreachable",
                "error": str(e),
                "elapsed_s": round(time.time() - t0, 2),
                "url": url,
            }

    def edit(
        self,
        image_input: Union[str, Path, bytes],
        prompt: str,
        mask_input: Optional[Union[str, Path, bytes]] = None,
        strength: float = 0.75,
        steps: int = 40,
        output_resolution: int = 1024,
        seed: int = 42,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edit an existing image using Qwen Image 2.1."""
        # Convert image_input to base64
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                return {"success": False, "error": f"Image file not found: {image_input}"}
            raw_bytes = p.read_bytes()
        elif isinstance(image_input, bytes):
            raw_bytes = image_input
        else:
            return {"success": False, "error": "Invalid image_input format"}

        img_b64 = base64.b64encode(raw_bytes).decode("ascii")

        mask_b64 = None
        if mask_input:
            if isinstance(mask_input, (str, Path)):
                mask_p = Path(mask_input)
                if mask_p.exists():
                    mask_b64 = base64.b64encode(mask_p.read_bytes()).decode("ascii")
            elif isinstance(mask_input, bytes):
                mask_b64 = base64.b64encode(mask_input).decode("ascii")

        errors = []

        # 1. First attempt: Dedicated Qwen Image 2.1 Edit workers (graydoom-qwen-image-21-edit)
        for worker in self.edit_workers:
            ws = worker["workspace"]
            url = worker["edit_url"]
            t0 = time.time()
            try:
                print(f"[QwenEditWorker] Calling dedicated edit worker on '{ws}'...")
                payload = {
                    "modelId": worker["model"],
                    "modelRevision": worker.get("pinned_revision", "d26bb61231c349cf6b7896fa83353113880e1ba3"),
                    "prompt": prompt,
                    "image_b64": img_b64,
                    "steps": steps,
                    "output_resolution": output_resolution,
                    "seed": seed,
                }
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json", "User-Agent": "Modal-Fleet-Client/1.0"}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("b64_json"):
                        out_bytes = base64.b64decode(data["b64_json"])
                        sha256 = hashlib.sha256(out_bytes).hexdigest()
                        saved_to = None
                        if output_path:
                            out_p = Path(output_path)
                            out_p.parent.mkdir(parents=True, exist_ok=True)
                            out_p.write_bytes(out_bytes)
                            saved_to = str(out_p)

                        return {
                            "success": True,
                            "workspace": ws,
                            "engine": worker["app"],
                            "sha256": sha256,
                            "bytes_length": len(out_bytes),
                            "saved_to": saved_to,
                            "steps": steps,
                            "seed": seed,
                            "elapsed_s": round(time.time() - t0, 2),
                        }
                    errors.append(f"Dedicated worker {ws} failed: {data.get('error', 'unknown')}")
                else:
                    errors.append(f"Dedicated worker {ws} HTTP {resp.status_code}")
            except Exception as e:
                errors.append(f"Dedicated worker {ws} exception: {e}")

        # 2. Fallback attempt: hermes-qwen-img-21 edit endpoints
        for fallback in self.fallback_workers:
            ws = fallback["workspace"]
            url = fallback["edit_url"]
            t0 = time.time()
            try:
                print(f"[QwenEditWorker] Fallback calling hermes edit on '{ws}'...")
                fallback_payload = {
                    "prompt": prompt,
                    "image_b64": img_b64,
                    "strength": strength,
                    "steps": steps,
                    "guidance_scale": 5.0,
                    "seed": seed,
                }
                if mask_b64:
                    fallback_payload["mask_b64"] = mask_b64

                resp = requests.post(
                    url,
                    json=fallback_payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("b64_json"):
                        out_bytes = base64.b64decode(data["b64_json"])
                        sha256 = hashlib.sha256(out_bytes).hexdigest()
                        saved_to = None
                        if output_path:
                            out_p = Path(output_path)
                            out_p.parent.mkdir(parents=True, exist_ok=True)
                            out_p.write_bytes(out_bytes)
                            saved_to = str(out_p)

                        return {
                            "success": True,
                            "workspace": ws,
                            "engine": "hermes-qwen-img-21",
                            "sha256": sha256,
                            "bytes_length": len(out_bytes),
                            "saved_to": saved_to,
                            "steps": steps,
                            "seed": seed,
                            "elapsed_s": round(time.time() - t0, 2),
                        }
                    errors.append(f"Fallback {ws} failed: {data.get('error')}")
                else:
                    errors.append(f"Fallback {ws} HTTP {resp.status_code}")
            except Exception as e:
                errors.append(f"Fallback {ws} exception: {e}")

        return {
            "success": False,
            "error": "All Qwen Edit worker nodes failed",
            "details": errors,
        }
