#!/usr/bin/env python3
"""Scene Pack Generator for HyperFrames AI Video using Modal GPU Fleet.

Takes a video topic and target slug, generates 4 key vertical (9:16) scene
frames in parallel across the Qwen DiT 2.1 / Qwen Image 2.1 fleet,
and wires them directly into the video project assets.
"""

import os
import sys
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workers.orchestrator import FleetOrchestrator


def generate_scene_pack(slug: str, topic: str, video_dir: Optional[str] = None):
    target_dir = Path(video_dir or f"videos/{slug}").resolve()
    assets_dir = target_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"🎬 GENERATING PARALLEL SCENE PACK FOR VIDEO: {slug}")
    print(f"   Topic: {topic}")
    print(f"   Target: {assets_dir}")
    print("=" * 70)

    # 4 Core beats matching Hyperframes shorts rules (5s pacing, thumbnail final frame)
    tasks = [
        {
            "label": "scene_01_hook",
            "prompt": f"Dramatic vertical 9:16 opening hook scene, {topic}, cinematic lighting, 8k ultra detailed, visual impact, volumetric fog, dynamic camera angle",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 101,
            "output_path": str(assets_dir / "scene_01_hook.png"),
        },
        {
            "label": "scene_02_build",
            "prompt": f"Deep dive technical exposition scene, {topic}, detailed mechanical or digital elements, atmospheric neon or studio rim lighting, high contrast, clean composition",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 202,
            "output_path": str(assets_dir / "scene_02_build.png"),
        },
        {
            "label": "scene_03_climax",
            "prompt": f"Intense breakthrough scene showing key insight or transformation, {topic}, striking colors, powerful visual metaphor, sharp focus, cinematic depth of field",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 303,
            "output_path": str(assets_dir / "scene_03_climax.png"),
        },
        {
            "label": "scene_04_thumbnail",
            "prompt": f"Hero thumbnail-grade final frame holding composition, {topic}, iconic framing, bold contrast, memorable visual focal point, studio grade production",
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, text, watermark",
            "aspect_ratio": "9:16",
            "steps": 40,
            "seed": 404,
            "output_path": str(assets_dir / "scene_04_thumbnail.png"),
        },
    ]

    orchestrator = FleetOrchestrator()
    results = orchestrator.run_parallel_generation(tasks, max_workers=4)

    # Write manifest of generated assets
    manifest = {
        "slug": slug,
        "topic": topic,
        "scenes": [
            {
                "label": r.get("label"),
                "saved_to": r.get("saved_to"),
                "sha256": r.get("sha256"),
                "workspace": r.get("workspace"),
                "elapsed_s": r.get("elapsed_s"),
                "success": r.get("success"),
            }
            for r in results
        ]
    }

    manifest_file = assets_dir / "scene_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\n✅ Scene pack manifest saved to: {manifest_file}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate parallel scene pack for a video short")
    parser.add_argument("--slug", required=True, help="Video slug (e.g. ai-future)")
    parser.add_argument("--topic", required=True, help="Topic description for prompt formulation")
    parser.add_argument("--dir", help="Optional target video directory")
    args = parser.parse_args()

    generate_scene_pack(slug=args.slug, topic=args.topic, video_dir=args.dir)
