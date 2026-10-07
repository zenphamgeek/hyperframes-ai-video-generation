#!/usr/bin/env python3
"""Unified CLI for Modal Fleet GPU Workers & HyperFrames Video Generation.

Usage:
  python3 scripts/fleet_cli.py status
  python3 scripts/fleet_cli.py draw --prompt "Futuristic cyberpunk Tokyo street" --aspect 9:16 -o assets/tokyo.png
  python3 scripts/fleet_cli.py edit --image assets/tokyo.png --prompt "Add neon rain and reflection" -o assets/tokyo_rain.png
  python3 scripts/fleet_cli.py batch --file scenes.json -o assets/scenes/
  python3 scripts/fleet_cli.py render --project videos/my-short
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workers.qwen_dit_worker import QwenDitWorker
from workers.qwen_edit_worker import QwenEditWorker
from workers.video_render_worker import VideoRenderWorker
from workers.orchestrator import FleetOrchestrator
from config.fleet_config import DIT_WORKER_ENDPOINTS, QWEN_EDIT_WORKERS, NATIVE_ASPECT_RATIOS


def cmd_status(args):
    """Check health across all Modal fleet workers."""
    print("=" * 70)
    print("🔍 PROBING MODAL FLEET GPU WORKERS (QWEN DIT 2.1 & QWEN EDIT 2.1)")
    print("=" * 70)

    dit_worker = QwenDitWorker()
    edit_worker = QwenEditWorker()

    print("\n[1] Qwen DiT 2.1 Drawing Pool (Text-to-Image / hermes-qwen-img-21):")
    dit_results = dit_worker.check_all_health(timeout=args.timeout)
    print(f"{'Workspace':<20} | {'Status':<12} | {'GPU':<10} | {'Latency':<8} | {'Details'}")
    print("-" * 70)
    for r in dit_results:
        status_icon = "🟢" if r.get("status") == "healthy" else "🔴"
        ws = r.get("workspace", "unknown")
        stat = r.get("status", "unknown")
        gpu = r.get("gpu", "A100-80GB")
        lat = f"{r.get('elapsed_s', 0):.2f}s"
        det = r.get("error", f"VRAM: {r.get('vram_used_gb', 0)}/{r.get('vram_total_gb', 80)} GB")
        print(f"{status_icon} {ws:<18} | {stat:<12} | {gpu:<10} | {lat:<8} | {det[:25]}")

    print("\n[2] Qwen Image 2.1 Dedicated Edit Pool (graydoom-qwen-image-21-edit):")
    print(f"{'Workspace':<20} | {'Status':<12} | {'Pipeline':<20} | {'Latency':<8}")
    print("-" * 70)
    for ew in QWEN_EDIT_WORKERS:
        res = edit_worker.check_health(ew, timeout=args.timeout)
        status_icon = "🟢" if res.get("status") == "healthy" else "🔴"
        ws = res.get("workspace", ew["workspace"])
        stat = res.get("status", "unknown")
        pipe = res.get("pipeline", "QwenImage21Pipeline")
        lat = f"{res.get('elapsed_s', 0):.2f}s"
        print(f"{status_icon} {ws:<18} | {stat:<12} | {pipe:<20} | {lat:<8}")

    print("\n" + "=" * 70)


def cmd_draw(args):
    """Generate a single image with Qwen DiT 2.1."""
    print(f"🎨 Generating image with Qwen DiT 2.1...")
    print(f"   Prompt: {args.prompt}")
    print(f"   Aspect: {args.aspect} | Steps: {args.steps} | Seed: {args.seed}")

    worker = QwenDitWorker()
    res = worker.generate_sync(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        aspect_ratio=args.aspect,
        steps=args.steps,
        guidance_scale=args.guidance,
        seed=args.seed,
        output_path=args.output,
    )

    if res.get("success"):
        print(f"✅ Success! Generated on workspace '{res.get('workspace')}' in {res.get('elapsed_s')}s")
        print(f"   Resolution: {res.get('resolution')} | SHA-256: {res.get('sha256')[:16]}...")
        if res.get("saved_to"):
            print(f"   Saved to: {res.get('saved_to')}")
    else:
        print(f"❌ Generation failed: {res.get('error')}")
        if res.get("details"):
            for d in res["details"]:
                print(f"   - {d}")
        sys.exit(1)


def cmd_edit(args):
    """Edit an image with Qwen Image 2.1."""
    print(f"🖌️  Editing image with Qwen Image 2.1...")
    print(f"   Input:  {args.image}")
    print(f"   Prompt: {args.prompt}")
    print(f"   Steps:  {args.steps} | Strength: {args.strength} | Seed: {args.seed}")

    worker = QwenEditWorker()
    res = worker.edit(
        image_input=args.image,
        prompt=args.prompt,
        mask_input=args.mask,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed,
        output_path=args.output,
    )

    if res.get("success"):
        print(f"✅ Edit complete on workspace '{res.get('workspace')}' in {res.get('elapsed_s')}s")
        print(f"   SHA-256: {res.get('sha256')[:16]}... | Engine: {res.get('engine')}")
        if res.get("saved_to"):
            print(f"   Saved to: {res.get('saved_to')}")
    else:
        print(f"❌ Edit failed: {res.get('error')}")
        if res.get("details"):
            for d in res["details"]:
                print(f"   - {d}")
        sys.exit(1)


def cmd_batch(args):
    """Execute a batch of generation tasks in parallel."""
    json_path = Path(args.file)
    if not json_path.exists():
        print(f"❌ Batch file not found: {json_path}")
        sys.exit(1)

    tasks_data = json.loads(json_path.read_text())
    if not isinstance(tasks_data, list):
        print(f"❌ JSON file must contain a list of task objects")
        sys.exit(1)

    out_dir = Path(args.output_dir or "assets/batch_output")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, t in enumerate(tasks_data):
        if "output_path" not in t:
            t["output_path"] = str(out_dir / f"frame_{i:03d}_{t.get('label', 'scene')}.png")

    orchestrator = FleetOrchestrator()
    results = orchestrator.run_parallel_generation(tasks_data, max_workers=args.workers)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n✨ Batch complete: {success_count}/{len(results)} successful")


def cmd_render(args):
    """Render a HyperFrames project to MP4."""
    worker = VideoRenderWorker()
    res = worker.render_hyperframes(
        project_dir=args.project,
        output_file=args.output,
        format=args.format,
    )

    if res.get("success"):
        print(f"🎬 Video rendered successfully!")
        print(f"   Output: {res.get('rendered_file')}")
        print(f"   Size:   {res.get('file_size_bytes'):,} bytes | Time: {res.get('elapsed_s')}s")
    else:
        print(f"❌ Render failed: {res.get('error')}")
        if res.get("stderr"):
            print(f"   Stderr: {res['stderr']}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Modal Fleet GPU & HyperFrames Video CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Check Modal fleet GPU workers health")
    p_status.add_argument("--timeout", type=int, default=15, help="Probe timeout in seconds")
    p_status.set_defaults(func=cmd_status)

    # draw
    p_draw = subparsers.add_parser("draw", help="Generate image with Qwen DiT 2.1")
    p_draw.add_argument("--prompt", "-p", required=True, help="Image prompt")
    p_draw.add_argument("--negative-prompt", "-n", default="", help="Negative prompt")
    p_draw.add_argument("--aspect", "-a", default="9:16", choices=list(NATIVE_ASPECT_RATIOS.keys()), help="Aspect ratio")
    p_draw.add_argument("--steps", type=int, default=40, help="Inference steps")
    p_draw.add_argument("--guidance", type=float, default=5.0, help="Guidance scale")
    p_draw.add_argument("--seed", type=int, default=42, help="Seed")
    p_draw.add_argument("--output", "-o", help="Output file path (PNG)")
    p_draw.set_defaults(func=cmd_draw)

    # edit
    p_edit = subparsers.add_parser("edit", help="Edit image with Qwen Image 2.1")
    p_edit.add_argument("--image", "-i", required=True, help="Input image path")
    p_edit.add_argument("--prompt", "-p", required=True, help="Edit instruction prompt")
    p_edit.add_argument("--mask", "-m", help="Optional mask image path")
    p_edit.add_argument("--strength", type=float, default=0.75, help="Edit strength (0.0-1.0)")
    p_edit.add_argument("--steps", type=int, default=40, help="Inference steps")
    p_edit.add_argument("--seed", type=int, default=42, help="Seed")
    p_edit.add_argument("--output", "-o", help="Output file path (PNG)")
    p_edit.set_defaults(func=cmd_edit)

    # batch
    p_batch = subparsers.add_parser("batch", help="Run parallel batch generation across Modal fleet")
    p_batch.add_argument("--file", "-f", required=True, help="Path to JSON file containing list of prompts")
    p_batch.add_argument("--output-dir", "-o", default="assets/batch_output", help="Output directory")
    p_batch.add_argument("--workers", "-w", type=int, default=5, help="Max parallel worker threads")
    p_batch.set_defaults(func=cmd_batch)

    # render
    p_render = subparsers.add_parser("render", help="Render HyperFrames video project to MP4")
    p_render.add_argument("--project", "-p", required=True, help="Project directory (e.g. videos/my-slug)")
    p_render.add_argument("--output", "-o", help="Output MP4 path")
    p_render.add_argument("--format", default="mp4", choices=["mp4", "webm"], help="Output format")
    p_render.set_defaults(func=cmd_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
