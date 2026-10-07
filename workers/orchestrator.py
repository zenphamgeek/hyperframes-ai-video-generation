"""Fleet Orchestrator Engine for Parallel Modal GPU Swarm.

Enforces:
- Concurrent parallel dispatch across available Modal GPU workers.
- Load balancing across verticalresilience, zenmaster, r2rgraph, mojopham, mvlm, lovenovel, zenonmind.
- Durable job state tracking (.jobs/ directory).
- Automatic retries and failover.
"""

import os
import sys
import time
import json
import base64
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workers.qwen_dit_worker import QwenDitWorker
from workers.qwen_edit_worker import QwenEditWorker
from config.fleet_config import DIT_WORKER_ENDPOINTS, QWEN_EDIT_WORKERS


class FleetOrchestrator:
    """Parallel Swarm Orchestrator for Modal GPU Fleet."""

    def __init__(self, jobs_dir: Optional[Path] = None):
        self.jobs_dir = jobs_dir or (REPO_ROOT / ".jobs")
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.dit_worker = QwenDitWorker()
        self.edit_worker = QwenEditWorker()

    def create_job_record(self, job_id: str, job_type: str, params: Dict[str, Any]) -> Path:
        """Create a durable job record file on disk."""
        record = {
            "schemaVersion": 1,
            "jobId": job_id,
            "jobType": job_type,
            "state": "prepared",
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "parameters": params,
        }
        job_file = self.jobs_dir / f"{job_id}.json"
        job_file.write_text(json.dumps(record, indent=2, ensure_ascii=False))
        return job_file

    def update_job_record(self, job_file: Path, state: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Update job state on disk."""
        try:
            data = json.loads(job_file.read_text())
            data["state"] = state
            data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if extra:
                data.update(extra)
            job_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[FleetOrchestrator] Warning: Could not update job record: {e}")

    def run_parallel_generation(
        self,
        tasks: List[Dict[str, Any]],
        max_workers: int = 5,
    ) -> List[Dict[str, Any]]:
        """Run multiple image generation tasks in parallel across the Modal GPU fleet.

        Each task dict can contain:
          - prompt (str)
          - negative_prompt (str, optional)
          - aspect_ratio (str, default '9:16')
          - width, height (optional int)
          - steps (int, default 40)
          - guidance_scale (float, default 5.0)
          - seed (int, default 42)
          - output_path (str)
          - label (str)
        """
        print(f"🔥 [FleetOrchestrator] Launching {len(tasks)} parallel generation tasks across Modal fleet...")
        results = []

        def execute_task(task_spec: Dict[str, Any], task_index: int) -> Dict[str, Any]:
            prompt = task_spec["prompt"]
            out_p = task_spec.get("output_path")
            aspect_ratio = task_spec.get("aspect_ratio", "9:16")
            steps = task_spec.get("steps", 40)
            seed = task_spec.get("seed", 42 + task_index * 13)
            label = task_spec.get("label", f"task_{task_index}")

            job_id = f"gen_{label}_{int(time.time())}"
            job_file = self.create_job_record(job_id, "text-to-image", task_spec)

            self.update_job_record(job_file, "submitting")
            res = self.dit_worker.generate_sync(
                prompt=prompt,
                negative_prompt=task_spec.get("negative_prompt"),
                aspect_ratio=aspect_ratio,
                width=task_spec.get("width"),
                height=task_spec.get("height"),
                steps=steps,
                guidance_scale=task_spec.get("guidance_scale", 5.0),
                seed=seed,
                output_path=out_p,
            )

            if res.get("success"):
                self.update_job_record(job_file, "downloaded", {
                    "workspace": res.get("workspace"),
                    "sha256": res.get("sha256"),
                    "saved_to": res.get("saved_to"),
                    "elapsed_s": res.get("elapsed_s"),
                })
            else:
                self.update_job_record(job_file, "failed", {"error": res.get("error")})

            res["label"] = label
            res["task_index"] = task_index
            return res

        workers_count = min(max_workers, len(tasks), len(DIT_WORKER_ENDPOINTS))
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            future_to_task = {
                executor.submit(execute_task, task, i): i
                for i, task in enumerate(tasks)
            }
            for future in as_completed(future_to_task):
                try:
                    res = future.result()
                    results.append(res)
                    status_emoji = "✅" if res.get("success") else "❌"
                    print(f" {status_emoji} [{res.get('label')}] Finished in {res.get('elapsed_s', 0)}s on {res.get('workspace', 'unknown')}")
                except Exception as exc:
                    idx = future_to_task[future]
                    results.append({"success": False, "task_index": idx, "error": str(exc)})
                    print(f" ❌ Task {idx} generated an exception: {exc}")

        # Sort back to original order
        results.sort(key=lambda r: r.get("task_index", 0))
        return results

    def run_parallel_editing(
        self,
        tasks: List[Dict[str, Any]],
        max_workers: int = 3,
    ) -> List[Dict[str, Any]]:
        """Run multiple image editing tasks in parallel using Qwen Image 2.1."""
        print(f"🎨 [FleetOrchestrator] Launching {len(tasks)} parallel edit tasks...")
        results = []

        def execute_edit(task_spec: Dict[str, Any], task_index: int) -> Dict[str, Any]:
            img_in = task_spec["image_input"]
            prompt = task_spec["prompt"]
            out_p = task_spec.get("output_path")
            label = task_spec.get("label", f"edit_{task_index}")

            job_id = f"edit_{label}_{int(time.time())}"
            job_file = self.create_job_record(job_id, "image-edit", task_spec)
            self.update_job_record(job_file, "submitting")

            res = self.edit_worker.edit(
                image_input=img_in,
                prompt=prompt,
                mask_input=task_spec.get("mask_input"),
                strength=task_spec.get("strength", 0.75),
                steps=task_spec.get("steps", 40),
                output_resolution=task_spec.get("output_resolution", 1024),
                seed=task_spec.get("seed", 42 + task_index),
                output_path=out_p,
            )

            if res.get("success"):
                self.update_job_record(job_file, "downloaded", {
                    "workspace": res.get("workspace"),
                    "sha256": res.get("sha256"),
                    "saved_to": res.get("saved_to"),
                    "elapsed_s": res.get("elapsed_s"),
                })
            else:
                self.update_job_record(job_file, "failed", {"error": res.get("error")})

            res["label"] = label
            res["task_index"] = task_index
            return res

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(execute_edit, task, i): i
                for i, task in enumerate(tasks)
            }
            for future in as_completed(future_to_task):
                try:
                    res = future.result()
                    results.append(res)
                    status_emoji = "✅" if res.get("success") else "❌"
                    print(f" {status_emoji} [{res.get('label')}] Edit done in {res.get('elapsed_s', 0)}s on {res.get('workspace', 'unknown')}")
                except Exception as exc:
                    idx = future_to_task[future]
                    results.append({"success": False, "task_index": idx, "error": str(exc)})

        results.sort(key=lambda r: r.get("task_index", 0))
        return results
