"""Video & Composition Render Worker.

Bridges Modal GPU video generation (hermes-neural-ltxvideo) with
local HyperFrames HTML/GSAP rendering into final MP4/WebM video.
"""

import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.fleet_config import LTX_VIDEO_CONFIG


class VideoRenderWorker:
    """Worker for rendering video compositions and generating foundation video clips."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or REPO_ROOT

    def render_hyperframes(
        self,
        project_dir: str,
        output_file: Optional[str] = None,
        format: str = "mp4",
        fps: int = 30,
        quality: str = "high",
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """Render a HyperFrames HTML composition to MP4/WebM using npx hyperframes render."""
        proj_path = Path(project_dir).resolve()
        if not proj_path.exists():
            return {"success": False, "error": f"Project directory does not exist: {proj_path}"}

        # Ensure index.html exists
        index_html = proj_path / "index.html"
        if not index_html.exists():
            return {"success": False, "error": f"index.html not found in {proj_path}"}

        out_dir = proj_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        if not output_file:
            slug = proj_path.name
            out_file = out_dir / f"{slug}.{format}"
        else:
            out_file = Path(output_file).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "npx", "hyperframes", "render",
            str(proj_path),
            "-o", str(out_file),
            "--format", format,
        ]

        t0 = time.time()
        print(f"[VideoRenderWorker] Running render: {' '.join(cmd)}")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_root),
            )
            elapsed = round(time.time() - t0, 2)

            if res.returncode == 0 and out_file.exists():
                file_size = out_file.stat().st_size
                return {
                    "success": True,
                    "rendered_file": str(out_file),
                    "file_size_bytes": file_size,
                    "elapsed_s": elapsed,
                    "stdout": res.stdout[-500:] if res.stdout else "",
                }
            else:
                return {
                    "success": False,
                    "error": f"Hyperframes render failed with code {res.returncode}",
                    "stderr": res.stderr,
                    "stdout": res.stdout,
                    "elapsed_s": elapsed,
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Render timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def lint_project(self, project_dir: str) -> Dict[str, Any]:
        """Validate hyperframes project against schema and syntax."""
        cmd = ["npx", "hyperframes", "lint", str(project_dir)]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.workspace_root))
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }

    def inspect_project(self, project_dir: str) -> Dict[str, Any]:
        """Inspect layout and overflow in hyperframes project."""
        cmd = ["npx", "hyperframes", "inspect", str(project_dir)]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.workspace_root))
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
