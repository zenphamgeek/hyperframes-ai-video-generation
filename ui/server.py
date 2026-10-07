"""FastAPI Web UI Server for HyperFrames & Modal GPU Swarm.

Hosts the Web Studio interface, provides REST APIs to:
- Probe Modal Fleet GPU workers (A100-80GB)
- Generate images via Qwen DiT 2.1
- Edit images via Qwen Image 2.1
- Generate parallel scene packs for video shorts
- Render HyperFrames compositions to MP4
"""

import os
import sys
import time
import json
import base64
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workers.qwen_dit_worker import QwenDitWorker
from workers.qwen_edit_worker import QwenEditWorker
from workers.video_render_worker import VideoRenderWorker
from workers.orchestrator import FleetOrchestrator
from config.fleet_config import DIT_WORKER_ENDPOINTS, QWEN_EDIT_WORKERS, NATIVE_ASPECT_RATIOS

app = FastAPI(
    title="HyperFrames AI Video & Modal GPU Fleet Studio",
    description="Studio interface for Qwen DiT 2.1, Qwen Image 2.1 Edit & HyperFrames Video Generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache workers
dit_worker = QwenDitWorker()
edit_worker = QwenEditWorker()
render_worker = VideoRenderWorker()
orchestrator = FleetOrchestrator()

OUTPUT_DIR = REPO_ROOT / "public" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Request / Response Models ────────────────────────────────────────────────
class DrawRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    aspect_ratio: Optional[str] = "9:16"
    steps: Optional[int] = 40
    guidance_scale: Optional[float] = 5.0
    seed: Optional[int] = 42


class EditJsonRequest(BaseModel):
    prompt: str
    image_b64: str
    mask_b64: Optional[str] = None
    strength: Optional[float] = 0.75
    steps: Optional[int] = 40
    seed: Optional[int] = 42


class ScenePackRequest(BaseModel):
    slug: str
    topic: str


class RenderRequest(BaseModel):
    project_dir: str
    output_file: Optional[str] = None
    format: Optional[str] = "mp4"


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/fleet/status")
def get_fleet_status(timeout: int = 4):
    """Probe all Modal GPU worker nodes and return status table."""
    dit_results = dit_worker.check_all_health(timeout=timeout)
    edit_results = [edit_worker.check_health(ew, timeout=timeout) for ew in QWEN_EDIT_WORKERS]
    return {
        "success": True,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dit_workers": dit_results,
        "edit_workers": edit_results,
    }


@app.post("/api/generate/draw")
def generate_draw(req: DrawRequest):
    """Generate image via Qwen DiT 2.1."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    filename = f"dit_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
    out_file = OUTPUT_DIR / filename

    res = dit_worker.generate_sync(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        aspect_ratio=req.aspect_ratio or "9:16",
        steps=req.steps or 40,
        guidance_scale=req.guidance_scale or 5.0,
        seed=req.seed or 42,
        output_path=str(out_file),
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Generation failed"))

    res["file_url"] = f"/public/generated/{filename}"
    return res


@app.post("/api/generate/edit")
def generate_edit(req: EditJsonRequest):
    """Edit image via Qwen Image 2.1."""
    if not req.prompt.strip() or not req.image_b64:
        raise HTTPException(status_code=400, detail="Prompt and image_b64 are required")

    filename = f"edit_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
    out_file = OUTPUT_DIR / filename

    raw_bytes = base64.b64decode(req.image_b64)
    mask_bytes = base64.b64decode(req.mask_b64) if req.mask_b64 else None

    res = edit_worker.edit(
        image_input=raw_bytes,
        prompt=req.prompt,
        mask_input=mask_bytes,
        strength=req.strength or 0.75,
        steps=req.steps or 40,
        seed=req.seed or 42,
        output_path=str(out_file),
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Edit failed"))

    res["file_url"] = f"/public/generated/{filename}"
    return res


@app.post("/api/generate/scene-pack")
def generate_scene_pack(req: ScenePackRequest):
    """Generate 4-frame scene pack for a video short in parallel across Modal GPU fleet."""
    if not req.slug.strip() or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Slug and topic are required")

    slug = req.slug.strip().lower().replace(" ", "-")
    target_dir = REPO_ROOT / "videos" / slug
    assets_dir = target_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Initialize video directory from template if not existing
    template_dir = REPO_ROOT / "templates" / "shorts" / "qwen-ai-video"
    if not (target_dir / "index.html").exists() and template_dir.exists():
        import shutil
        shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)

    tasks = [
        {
            "label": "scene_01_hook",
            "prompt": f"Dramatic vertical 9:16 opening hook scene, {req.topic}, cinematic lighting, 8k ultra detailed, volumetric light, dynamic composition",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 101,
            "output_path": str(assets_dir / "scene_01_hook.png"),
        },
        {
            "label": "scene_02_build",
            "prompt": f"Deep dive technical exposition scene, {req.topic}, detailed architectural elements, atmospheric rim lighting, high contrast, clean background",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 202,
            "output_path": str(assets_dir / "scene_02_build.png"),
        },
        {
            "label": "scene_03_climax",
            "prompt": f"Intense breakthrough scene showing transformation, {req.topic}, striking vivid palette, sharp focus, cinematic depth of field",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 303,
            "output_path": str(assets_dir / "scene_03_climax.png"),
        },
        {
            "label": "scene_04_thumbnail",
            "prompt": f"Hero thumbnail-grade final frame holding composition, {req.topic}, iconic framing, bold contrast, memorable visual focal point",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 404,
            "output_path": str(assets_dir / "scene_04_thumbnail.png"),
        },
    ]

    results = orchestrator.run_parallel_generation(tasks, max_workers=4)

    # Format scene items
    scenes = []
    for r in results:
        label = r.get("label")
        scenes.append({
            "label": label,
            "file_url": f"/videos/{slug}/assets/{label}.png",
            "workspace": r.get("workspace"),
            "elapsed_s": r.get("elapsed_s"),
            "sha256": r.get("sha256"),
            "success": r.get("success"),
        })

    return {
        "success": True,
        "slug": slug,
        "topic": req.topic,
        "project_dir": f"videos/{slug}",
        "preview_url": f"/videos/{slug}/index.html",
        "scenes": scenes,
    }


@app.get("/api/projects")
def list_projects():
    """List available video projects and templates."""
    projects = []
    templates_root = REPO_ROOT / "templates" / "shorts"
    if templates_root.exists():
        for t in templates_root.iterdir():
            if t.is_dir() and (t / "index.html").exists():
                projects.append({
                    "name": t.name,
                    "type": "template",
                    "path": str(t.relative_to(REPO_ROOT)),
                    "preview_url": f"/templates/shorts/{t.name}/index.html"
                })

    videos_root = REPO_ROOT / "videos"
    if videos_root.exists():
        for v in videos_root.iterdir():
            if v.is_dir() and (v / "index.html").exists():
                projects.append({
                    "name": v.name,
                    "type": "video",
                    "path": str(v.relative_to(REPO_ROOT)),
                    "preview_url": f"/videos/{v.name}/index.html"
                })

    return {"success": True, "projects": projects}


@app.post("/api/video/render")
def render_video(req: RenderRequest):
    """Render HyperFrames project into MP4 video file."""
    proj_path = REPO_ROOT / req.project_dir
    if not proj_path.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {req.project_dir}")

    res = render_worker.render_hyperframes(
        project_dir=str(proj_path),
        output_file=req.output_file,
        format=req.format or "mp4",
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Render failed"))

    out_file = Path(res["rendered_file"])
    rel_path = out_file.relative_to(REPO_ROOT)
    res["video_url"] = f"/{rel_path}"
    return res


@app.get("/api/jobs")
def get_jobs(limit: int = 30):
    """List durable job records."""
    jobs_dir = REPO_ROOT / ".jobs"
    if not jobs_dir.exists():
        return {"success": True, "jobs": []}

    files = sorted(jobs_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
    jobs = []
    for f in files:
        try:
            data = json.loads(f.read_text())
            jobs.append(data)
        except Exception:
            continue
    return {"success": True, "jobs": jobs}


# ── Static File Mounts ───────────────────────────────────────────────────────
app.mount("/public", StaticFiles(directory=str(REPO_ROOT / "public")), name="public")
app.mount("/templates", StaticFiles(directory=str(REPO_ROOT / "templates")), name="templates")

videos_dir = REPO_ROOT / "videos"
videos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(videos_dir)), name="videos")

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


@app.get("/", methods=["GET", "HEAD"], response_class=FileResponse)
def serve_index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ui.server:app", host="0.0.0.0", port=8000, reload=False)
