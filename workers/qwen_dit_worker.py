"""Qwen DiT 2.1 (hermes-qwen-img-21) Text-to-Image Generation Worker.

Leverages Modal Fleet GPU (A100-80GB) with multi-node load balancing,
failover, and parallel batch processing.
"""

import os
import sys
import time
import json
import base64
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests
import aiohttp

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.fleet_config import DIT_WORKER_ENDPOINTS, NATIVE_ASPECT_RATIOS, DEFAULT_PARAMS


class QwenDitWorker:
    """Worker client for Qwen DiT 2.1 Text-to-Image Modal fleet."""

    def __init__(self, endpoints: Optional[List[Dict[str, Any]]] = None, timeout: int = 360):
        self.endpoints = endpoints or DIT_WORKER_ENDPOINTS
        self.timeout = timeout
        self.current_idx = 0

    def check_health(self, endpoint_dict: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        """Check liveness of a single DiT worker node."""
        url = endpoint_dict["health_url"]
        ws = endpoint_dict["workspace"]
        t0 = time.time()
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Modal-Fleet-Client/1.0"})
            elapsed = round(time.time() - t0, 2)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "workspace": ws,
                    "status": "healthy",
                    "model": data.get("model", endpoint_dict["model"]),
                    "gpu": data.get("gpu", endpoint_dict["gpu"]),
                    "vram_used_gb": data.get("vram_used_gb", 0),
                    "vram_total_gb": data.get("vram_total_gb", 80),
                    "elapsed_s": elapsed,
                    "url": url,
                }
            return {
                "workspace": ws,
                "status": f"http_{resp.status_code}",
                "error": resp.text[:100],
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

    def check_all_health(self, timeout: int = 15) -> List[Dict[str, Any]]:
        """Probe all fleet DiT worker nodes in parallel."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.endpoints)) as executor:
            futures = [executor.submit(self.check_health, ep, timeout) for ep in self.endpoints]
            return [f.result() for f in concurrent.futures.as_completed(futures)]

    def generate_sync(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "9:16",
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: int = 40,
        guidance_scale: float = 5.0,
        seed: int = 42,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronously generate an image with multi-node automatic failover."""
        # Resolve dimensions
        if width is None or height is None:
            if aspect_ratio in NATIVE_ASPECT_RATIOS:
                w, h = NATIVE_ASPECT_RATIOS[aspect_ratio]
            else:
                w, h = (1080, 1920)
        else:
            w, h = width, height

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "steps": steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "aspect_ratio": aspect_ratio,
            "width": w,
            "height": h,
        }

        # Try endpoints in round-robin order with fallback
        total_eps = len(self.endpoints)
        errors = []

        for attempt in range(total_eps):
            ep_info = self.endpoints[(self.current_idx + attempt) % total_eps]
            generate_url = ep_info["generate_url"]
            ws = ep_info["workspace"]
            t0 = time.time()

            try:
                print(f"[QwenDitWorker] Dispatching to '{ws}' (node {attempt+1}/{total_eps})...")
                resp = requests.post(
                    generate_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json", "User-Agent": "Modal-Fleet-Client/1.0"}
                )

                if resp.status_code != 200:
                    errors.append(f"Node {ws} HTTP {resp.status_code}: {resp.text[:150]}")
                    continue

                res_json = resp.json()
                if not res_json.get("success"):
                    errors.append(f"Node {ws} failed: {res_json.get('error', 'unknown error')}")
                    continue

                b64_str = res_json.get("b64_json")
                if not b64_str:
                    errors.append(f"Node {ws} returned empty b64_json")
                    continue

                img_bytes = base64.b64decode(b64_str)
                sha256 = hashlib.sha256(img_bytes).hexdigest()
                elapsed = round(time.time() - t0, 2)

                saved_to = None
                if output_path:
                    out_p = Path(output_path)
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    out_p.write_bytes(img_bytes)
                    saved_to = str(out_p)

                # Move index for next request to balance load
                self.current_idx = (self.current_idx + attempt + 1) % total_eps

                return {
                    "success": True,
                    "workspace": ws,
                    "sha256": sha256,
                    "bytes_length": len(img_bytes),
                    "saved_to": saved_to,
                    "resolution": f"{w}x{h}",
                    "aspect_ratio": aspect_ratio,
                    "steps": steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed,
                    "elapsed_s": elapsed,
                    "b64_json": b64_str if not output_path else None,
                }

            except Exception as e:
                errors.append(f"Node {ws} exception: {e}")
                continue

        return {
            "success": False,
            "error": "All Modal DiT worker nodes failed or timed out",
            "details": errors,
        }

    async def generate_async(
        self,
        session: aiohttp.ClientSession,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "9:16",
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: int = 40,
        guidance_scale: float = 5.0,
        seed: int = 42,
        output_path: Optional[str] = None,
        target_workspace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Asynchronously generate image on target or best available worker node."""
        if width is None or height is None:
            w, h = NATIVE_ASPECT_RATIOS.get(aspect_ratio, (1080, 1920))
        else:
            w, h = width, height

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "steps": steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "aspect_ratio": aspect_ratio,
            "width": w,
            "height": h,
        }

        # Filter candidate endpoints
        candidates = (
            [ep for ep in self.endpoints if ep["workspace"] == target_workspace]
            if target_workspace
            else self.endpoints
        )

        for ep_info in candidates:
            generate_url = ep_info["generate_url"]
            ws = ep_info["workspace"]
            t0 = time.time()
            try:
                async with session.post(
                    generate_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status != 200:
                        continue
                    res_json = await resp.json()
                    if not res_json.get("success"):
                        continue
                    b64_str = res_json.get("b64_json")
                    if not b64_str:
                        continue

                    img_bytes = base64.b64decode(b64_str)
                    sha256 = hashlib.sha256(img_bytes).hexdigest()
                    elapsed = round(time.time() - t0, 2)

                    saved_to = None
                    if output_path:
                        out_p = Path(output_path)
                        out_p.parent.mkdir(parents=True, exist_ok=True)
                        out_p.write_bytes(img_bytes)
                        saved_to = str(out_p)

                    return {
                        "success": True,
                        "workspace": ws,
                        "sha256": sha256,
                        "bytes_length": len(img_bytes),
                        "saved_to": saved_to,
                        "resolution": f"{w}x{h}",
                        "seed": seed,
                        "elapsed_s": elapsed,
                    }
            except Exception:
                continue

        return {"success": False, "error": f"Failed generating on candidates ({target_workspace or 'all'})"}
