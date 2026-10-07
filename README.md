# hyperframes-ai-video-generation (Modal GPU Fleet Edition)

Next-generation AI video generation powered by **HyperFrames** HTML/GSAP motion compositions and **Modal Fleet GPU Swarm** featuring:
- **Qwen DiT 2.1** (Text-to-Image / Concepts / Scene Visuals via `hermes-qwen-img-21` across A100-80GB pool).
- **Qwen Image 2.1 Edit** (Image-to-Image / Inpainting / Character Consistency via `graydoom-qwen-image-21-edit`).
- **Parallel Fleet Orchestrator** (Multi-workspace load balancing across `verticalresilience`, `lovenovel`, `mvlm`, `zenonmind`, `mojopham`).
- **HyperFrames HTML/GSAP Engine** (1080×1920 vertical shorts and 16:9 cinematic compositions rendered to MP4/WebM).

---

## ⚡ Modal Fleet GPU Quick Start

```bash
# 1. Probe the health and latency of all active GPU worker nodes
npm run fleet:status

# 2. Generate a single frame using Qwen DiT 2.1 with automatic failover
npm run fleet:draw -- -p "Cinematic cybernetic astronaut in alien crystalline nebula" -a 9:16 -o assets/hero.png

# 3. Edit an existing frame using Qwen Image 2.1 (consistency & inpainting)
npm run fleet:edit -- -i assets/hero.png -p "Add glowing cyan telemetry holographic visor" -o assets/hero_edit.png

# 4. Generate a complete 4-frame scene pack in parallel across the Modal fleet
npm run fleet:scene -- --slug ai-breakthrough --topic "Autonomous Agentic AI Coding on A100 GPUs"

# 5. Preview or render video with HyperFrames
npm run video:lint templates/shorts/qwen-ai-video
npx hyperframes preview templates/shorts/qwen-ai-video
npm run video:render -- -p templates/shorts/qwen-ai-video -o out/demo.mp4
```

---

Turn a topic prompt into a polished, AI-voiced vertical YouTube Short. One command, fire and forget.

```bash
archon workflow run create-classic-short --no-worktree "What is RAG?"
```

That's it. The workflow researches the topic, drafts a paced narration, generates TTS (free Kokoro locally, or paid ElevenLabs — your choice), edits an HTML+GSAP composition, lints it, and opens a browser preview. Render is always manual — `npx hyperframes render videos/<slug>` when you're ready.

The repo ships with **three templates out of the box** — `classic` (brand-neutral default, blue + dark), `archon` (Archon-branded), `anthropic` (Anthropic-branded) — and you can [build your own brand](#want-a-different-brand-or-look) by asking your coding agent.

> ## 🚀 Just tell your coding agent to do it
>
> The fastest way through this whole README is to **not** read it yourself. Open this repo in [Claude Code](https://claude.ai/code) (or any agentic coding tool) and paste one of these:
>
> **To generate a video with a shipped template:**
>
> > _"Read the README and set everything up so I can generate my first video. The topic is: **[your idea or URL here]**."_
>
> **To build your own brand/style first, then generate:**
>
> > _"Read the README. Look at `templates/shorts/classic/`, `templates/shorts/archon/`, and `templates/shorts/anthropic/` as references, then create a new short template for **[your brand name, URL, or vibe — e.g. "my SaaS at example.com", "a cyberpunk dev tool", "Linear"]**. Pick the palette, gradient, wordmark, and CTA URL yourself based on the brand. When the template is built and lints clean, generate my first video with it. The topic is: **[your idea or URL here]**."_
>
> The agent will install the system deps, walk you through any keys it needs (Kokoro is free / no key required; ElevenLabs needs an API key), optionally clone + restyle a template for your brand, run the matching `archon workflow run create-<brand>-short`, and hand you the preview URL. You just supply the inputs.

The stack: **[Archon](https://archon.diy)** (workflow harness) + **[Claude Code](https://claude.ai/code)** (planning + composition editing) + **[HyperFrames](https://hyperframes.heygen.com/)** (HTML/GSAP video framework) + **[Kokoro](https://github.com/hexgrad/kokoro)** (free local TTS, default) or **[ElevenLabs](https://elevenlabs.io)** (paid premium TTS) — both return word-level timestamps. Total runtime per short: ~20-30 min depending on research depth.

## Quick Start

> ### 🤖 For the coding agent — ask the user these two questions first
>
> If you're an AI coding agent reading this README to set things up, **do not assume defaults**. Ask the user these two questions and tailor everything below to their answers.
>
> **1. Which TTS engine do you want — Kokoro or ElevenLabs?**
>
> - _Kokoro_ — free, local, no API key, Apache-licensed, ~325MB one-time model download, runs on CPU. High quality (MOS 4.5). Preset voices only — no voice cloning.
> - _ElevenLabs_ — paid (~$5/M chars), premium quality, supports Instant Voice Cloning. Requires an `ELEVENLABS_API_KEY` from [elevenlabs.io](https://elevenlabs.io).
>
> Install ONLY the deps for the engine they picked (don't install both) and configure ONLY that engine's block in `.archon/.env`.
>
> **If they pick ElevenLabs, walk them through getting set up — don't just point them at a link.** Specifically:
>
> 1. **Tell them to create an ElevenLabs account** at https://elevenlabs.io. The free tier is fine for testing (10,000 chars/month ≈ 5-6 shorts); the Starter plan ($5/mo, 30,000 chars) is the realistic minimum for regular use.
> 2. **Walk them to the API key page**: log in → click their avatar (top-right) → "API Keys" → "Create API Key" → copy the value. Tell them to paste it as `ELEVENLABS_API_KEY=...` in `.archon/.env`. **Never commit this file** — it's already gitignored.
> 3. **Ask whether they want a preset voice or their own voice clone:**
>    - _Preset voice_ — set `ELEVENLABS_VOICE_ID=nPczCjzI2devNBz1zQrb` (Brian, mature American male — the documented default for shorts). Other presets: Adam `pNInz6obpgDQGcFmaJgB`, Daniel `onwK4e9ZLuTAKqWW03F9`. Or run `python scripts/list_voices.py` after setup to browse.
>    - _Voice clone_ — direct them to elevenlabs.io → "Voices" → "Add Voice" → "Instant Voice Clone", upload 1-3 minutes of clean audio (their own voice for personalized narration), then copy the new voice's ID from the voice page URL or the voice library detail panel.
> 4. **Confirm the rest of the tuning vars are filled in** with the tested-good shorts defaults from `.env.example` (these are NOT the ElevenLabs platform defaults — the platform defaults sound flatter on shorts):
>    - `ELEVENLABS_MODEL_ID=eleven_multilingual_v2`
>    - `ELEVENLABS_STABILITY=0.40`
>    - `ELEVENLABS_SIMILARITY_BOOST=0.75`
>    - `ELEVENLABS_STYLE=0.70`
>    - `ELEVENLABS_SPEED_SHORTS=1.15`
>    - `ELEVENLABS_USE_SPEAKER_BOOST=true`
> 5. **Verify**: after `.archon/.env` is filled in, run a one-line smoke test before kicking off the full workflow:
>    ```bash
>    python -c "import os; from dotenv import load_dotenv; load_dotenv('.archon/.env'); print('OK' if os.getenv('ELEVENLABS_API_KEY') else 'MISSING KEY')"
>    ```
>    If it prints `MISSING KEY`, the `.env` file isn't being read — most likely the path is wrong or the line is commented out.
>
> The full tuning matrix (what each knob does, when to adjust it) is in [`.env.example`](.env.example) and the ["Voice tuning"](#voice-tuning-elevenlabs) section below — surface that to the user if they ask "what does X setting do?"
>
> **2. Do you want to use one of the shipped templates as-is, or customize the look first?**
>
> - _Use shipped as-is_ — pick `classic` (brand-neutral default), `archon`, or `anthropic`. No template work needed; go straight to step 5 (run the workflow).
> - _Customize the style only (reskin)_ — different palette, wordmark, and CTA URL, but the same scene layouts as the source template. Route to ["Adding your own template" → Option A or B](#adding-your-own-template-let-your-coding-agent-do-it).
> - _Customize the scenes too (redesign)_ — different visual layouts inside each phase, so the video doesn't look identical to the shipped templates. Route to ["Adding your own template" → Option C](#option-c--redesign-the-scenes-different-layouts-same-phase-rhythm).
>
> **If they want to customize, ask a follow-up: "briefly describe what you want."** Brand name, target website, vibe, palette inspiration, any specific scene layouts they care about. One or two sentences is enough for Option B; Option C benefits from a per-phase layout direction (see the alternatives table in that section).
>
> Only after both answers are confirmed: proceed with the install steps below, then build/pick the template, then run the matching workflow.

Three install commands, one config file, one workflow run.

### 1. Install Claude Code

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

Then `claude /login` once to authenticate.

### 2. Install Archon (binary, no setup wizard needed)

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

# Homebrew
brew install coleam00/archon/archon
```

Point Archon at Claude Code (binary installs don't bundle it):

```bash
# macOS / Linux / WSL — add to ~/.bashrc or ~/.zshrc
export CLAUDE_BIN_PATH="$HOME/.local/bin/claude"

# Windows (PowerShell profile)
$env:CLAUDE_BIN_PATH = "$env:USERPROFILE\.local\bin\claude.exe"
```

You do **NOT** need to run `archon setup` — that's only for the source-install path (which clones the Archon repo). The binary just works against this repo's pre-configured `.archon/` directory. On first workflow run, Archon lazily creates `~/.archon/archon.db` (SQLite, single file, no schema setup required).

### 3. Install system deps

You need Node ≥22, Python ≥3.10, ffmpeg, jq, and bun.

```bash
# macOS (Homebrew)
brew install node python ffmpeg jq oven-sh/bun/bun

# Windows (winget + bun installer)
winget install OpenJS.NodeJS Python.Python.3.12 Gyan.FFmpeg jqlang.jq
irm bun.sh/install.ps1 | iex

# Linux (Debian / Ubuntu) — apt's `nodejs` is too old on most LTS releases;
# use NodeSource for Node 22.
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -
sudo apt install -y nodejs python3 python3-venv python3-pip ffmpeg jq unzip
curl -fsSL https://bun.sh/install | bash
```

Then the Python TTS deps. Use a virtualenv so `pip` doesn't fight your system Python (Ubuntu 24.04+ blocks bare `pip install` via PEP 668):

```bash
python3 -m venv .venv
source .venv/bin/activate           # macOS / Linux
# .venv\Scripts\activate            # Windows PowerShell

# Pick ONE of these — see "TTS engines" below for the tradeoff.

# Free local TTS (Kokoro, no API key)
pip install kokoro python-dotenv soundfile numpy

# OR commercial TTS (ElevenLabs, paid API)
pip install elevenlabs python-dotenv
```

If you chose Kokoro, also install **espeak-ng** system-wide (needed for phoneme conversion):

```bash
# macOS
brew install espeak

# Ubuntu / Debian
sudo apt install espeak-ng

# Windows: download the .msi installer
# https://github.com/espeak-ng/espeak-ng/releases
```

Activate the venv (`source .venv/bin/activate`) in any shell where you'll run `archon workflow run` — the workflow's TTS step calls `python scripts/kokoro-tts.py` or `python scripts/elevenlabs-tts.py` and needs the chosen package on the active interpreter's path.

### 4. Clone + configure

```bash
git clone https://github.com/coleam00/hyperframes-ai-video-generation
cd hyperframes-ai-video-generation
cp .env.example .archon/.env
```

Open `.archon/.env` and fill in the TTS settings for whichever engine you picked:

**For Kokoro (free, local):**
- `KOKORO_VOICE=af_heart` (or any voice from the [Kokoro voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md))
- `KOKORO_LANG_CODE=a` (`a`=American English, `b`=British, `j`=Japanese, etc.)
- Speed defaults already shipped — see `.env.example`.

**For ElevenLabs (paid, premium quality):**
- `ELEVENLABS_API_KEY` — your key from [elevenlabs.io](https://elevenlabs.io)
- `ELEVENLABS_VOICE_ID` — either your clone's ID or a preset (Brian `nPczCjzI2devNBz1zQrb` is the documented default)
- The other 7 settings ship with the **tested-good defaults** for shorts (see "Voice tuning" below).

### 5. Run it

Pick a template aesthetic. **`classic` is the default** — brand-neutral, works for any topic:

```bash
# Classic (brand-neutral dark theme, bright blue + sky blue) — DEFAULT
archon workflow run create-classic-short --no-worktree "Your topic here"

# Archon-themed (dark blue + cyan/magenta gradient hero)
archon workflow run create-archon-short --no-worktree "Your topic here"

# Anthropic-themed (near-black + warm orange/cream gradient hero)
archon workflow run create-anthropic-short --no-worktree "Your topic here"
```

Want a different brand? See "[Want a different brand or look?](#want-a-different-brand-or-look)" below — the fastest path is asking your coding agent to clone an existing template and re-skin it.

20-30 minutes later the studio opens with the finished short. Render with `npx hyperframes render videos/<slug> -o videos/<slug>/out/<slug>.mp4`.

---

## What the workflow does

Each template ships with its own three-node Archon workflow at `.archon/workflows/create-<template>-short.yaml` — all three are structurally identical, only the template path and brand strings differ:

1. **`parse-input`** (bash + bun) — derives `{topic, slug, duration, title}` from the topic phrase.
2. **`precheck`** (bash) — verifies `templates/shorts/<template>/` exists, `videos/<slug>/` doesn't, `npx` is on PATH.
3. **`create-short`** (Claude) — runs the matching playbook at `.claude/skills/diy-yt-creator/new-<template>-short.md`:
   - Researches the topic (WebFetch + WebSearch grounding)
   - Drafts narration paced to the duration target — with mandatory SSML `<break>` tags between sentences and natural abbreviations (MIT, not M I T)
   - Generates TTS via `python scripts/kokoro-tts.py --shorts` (default, free) or `python scripts/elevenlabs-tts.py --shorts --no-chunk` (paid)
   - Computes phase-transition anchors via `python scripts/compute_timings.py` (strips break tags, filters phantom punctuation)
   - Edits `videos/<slug>/index.html` — title, content, GSAP timeline anchors, audio element
   - Runs `npx hyperframes lint` + `inspect` until clean
   - Launches `npx hyperframes preview` in the background
   - Prints the preview URL + the manual `render` command

## Want a different brand or look?

The repo ships **three templates** out of the box at `templates/shorts/`:

| Template | Aesthetic | Workflow |
|---|---|---|
| `classic/` **(default)** | Deep navy + bright blue / sky blue gradient hero, "YOUR BRAND" wordmark, `your-domain.com` CTA — placeholders ready for you to swap | `archon workflow run create-classic-short --no-worktree "<topic>"` |
| `archon/` | Dark blue + cyan→magenta gradient hero, Archon logo banner, `archon.diy` CTA | `archon workflow run create-archon-short --no-worktree "<topic>"` |
| `anthropic/` | Near-black + warm orange→cream gradient hero, "ANTHROPIC" wordmark banner, `anthropic.com` CTA | `archon workflow run create-anthropic-short --no-worktree "<topic>"` |

**The classic template is the brand-neutral default.** Use it for any topic that isn't specifically about Archon or Anthropic — you'll need to swap the `YOUR BRAND` wordmark and `your-domain.com` CTA for your own (one-line CSS edits, documented in the template's README).

All three templates share the same **4-phase rhythm** (Phase 1 → 2 → 3 → 4 across ~24s), the same playbook contract (phase IDs `#phase1-4`, timing constants `T1/T2/T3` and `P2/P3/P4`, the `slam_t` shake anchor, the audio insertion point), and the same `compute_timings.py` math.

**What can differ between templates:** the *visual pattern inside each phase*. Two templates can share Phase 2 as "the 6-12s slot" but use completely different layouts to fill it — `archon/` uses a side-by-side stat-pill row; `anthropic/` uses a single oversized metric with a hairline rule; you could write one that uses a full-screen quote with attribution. Same rhythm, different scene design.

Think of the phase contract as the song's tempo and bar count, and the per-template HTML/CSS as the chord voicing and instrumentation.

### Adding your own template (let your coding agent do it)

If neither shipped template fits, **ask your coding agent to clone one and modify it**. Three options below, ordered by how much design effort the agent is taking on. Pick the one that matches what you actually want — they get progressively more transformative.

> **Heads-up before you start:** Option A and Option B produce a template that looks like the source template with a new coat of paint. If your goal is "my videos shouldn't look identical to Archon's or Anthropic's videos," you want **Option C**. The shipped templates intentionally share scene layouts within their phases — that's the reskin path. Visually distinct scenes are a separate, larger design pass.

#### Option A — reskin only (you have your brand specs ready)

Use this when you already know your palette, brand name, and CTA URL, and you're fine with the source template's scene layouts. Fastest path, fewest decisions delegated:

> _"Create a new short template at `templates/shorts/<your-brand>/` by cloning `templates/shorts/anthropic/` and restyling it for **\<your brand name\>**. Specifically:_
>
> 1. _Palette: `--bg = <hex>`, `--accent-1 = <hex>` (hero/signature accent), `--accent-2 = <hex>` (CTA), `--accent-3 = <hex>` (secondary), `--accent-4 = <hex>` (workhorse). The hero gradient text-fill should be `--accent-1 → --accent-2`._
> 2. _Top banner: CSS-rendered wordmark reading **"\<BRAND IN ALL CAPS\>"** in the hero gradient, OR drop an SVG into `assets/` and follow the swap pattern in `templates/shorts/anthropic/DESIGN.md`._
> 3. _Default CTA URL: **<your-domain>**._
> 4. _Update `meta.json`, `hyperframes.json`, `DESIGN.md`, `README.md`, `PRONUNCIATION.md` for the new brand. Keep class names (`.cyan`, `.magenta`, etc.) and phase IDs (`#phase1-4`, `#p1-hero`, `#p2-pill-1/2`, `#p3-card-1/2/3`, `#p4-url`, the `T1/T2/T3` and `P2/P3/P4` timing constants, `slam_t`, `shake_offsets`) identical to the source so `compute_timings.py` and the playbook work unchanged._
> 5. _Add a sibling playbook at `.claude/skills/diy-yt-creator/new-<brand>-short.md` mirroring `new-anthropic-short.md` — same 11 steps, just with the new template path, palette names, and CTA URL._
> 6. _Add an Archon workflow at `.archon/workflows/create-<brand>-short.yaml` and command at `.archon/commands/create-<brand>-short.md` mirroring the anthropic versions. Keep the parse-input logic identical; only the workflow name, description, template path, and command reference change._
> 7. _Add the new template's row to the table in this repo's README and to `.claude/skills/diy-yt-creator/SKILL.md`._
> 8. _Run `npx hyperframes lint templates/shorts/<your-brand>` to confirm clean."_

**Result:** Same scenes as the source template, your brand colors and wordmark. ~5-10 minutes.

#### Option B — agent-designed reskin (you supply the vibe, agent picks the palette)

Use this when you don't want to pick hex codes yourself but still want a reskin (same scene layouts, your brand). Hand the agent inspiration and let it derive the palette:

> _"Look at the existing short templates at `templates/shorts/archon/` and `templates/shorts/anthropic/` as reference for the structure and design system. Then design a new short template for **\<your brand or vibe — e.g. "Linear", "a cyberpunk dev tool with green-on-black terminal vibes", "my SaaS company's brand at https://example.com">**. You decide the palette, the gradient direction, the wordmark treatment, and the CTA URL — pick choices that match the brand's actual identity (visit the site if a URL was provided; otherwise use your judgment). Keep the scene layouts and all timing-contract IDs from the source template unchanged — this is a reskin pass, not a redesign. Create the template at `templates/shorts/<slug>/` along with the playbook, workflow YAML, command file, and SKILL.md entry. When you're done, show me the palette you picked and why, run `npx hyperframes lint templates/shorts/<slug>` to confirm it's clean, and tell me how to invoke the new workflow."_

**Result:** Same scenes as the source template, agent-picked brand identity. ~10-15 minutes.

#### Option C — redesign the scenes (different layouts, same phase rhythm)

**Use this when you want your videos to look visually distinct from the shipped templates** — not just a color swap, but actually different scene compositions in each phase. This is the answer to "why does my Anthropic short look just like the Archon one?"

The phase rhythm stays the same (4 phases, same timing windows, same playbook contract). What changes is *what fills each phase visually*. Concrete examples of layout substitutions that work without breaking the playbook:

| Phase | Default (archon-style) | Possible alternatives |
|---|---|---|
| **Phase 1 — Hero** | Overline + pre-line + gradient slam word + caption pill | Full-bleed quote + tiny attribution; oversized number + label; brand logo entrance + tagline |
| **Phase 2 — Insight slot** | Side-by-side stat pill row (2 stats) | Single oversized metric + hairline rule (anthropic now); split-screen comparison; pull-quote with attribution; vertical stack of 3 micro-stats |
| **Phase 3 — Detail slot** | Color-card grid (3 feature cards) | Typographic chapter list (anthropic now); horizontal timeline strip; hub-and-spoke diagram; before/after pair; receipt-style itemized list |
| **Phase 4 — CTA** | Overline + URL pill + subscribe arrow | QR code + URL; multi-line manifesto end-card; logo lock-up with URL beneath |

Sample prompt to redesign two scenes against a fresh template:

> _"I want a new short template at `templates/shorts/<brand>/` cloned from `templates/shorts/anthropic/`, but with **visually distinct scene layouts** — not just a reskin. Redesign:_
>
> - _**Phase 2** as **\<one of: single oversized metric / split-screen comparison / pull-quote / micro-stat stack\>** — different from both Archon's pill-row and Anthropic's single-metric layout._
> - _**Phase 3** as **\<one of: horizontal timeline strip / hub-and-spoke / before-after pair / receipt list\>** — different from both Archon's card grid and Anthropic's chapter list._
>
> _Keep Phase 1 and Phase 4 the same shape as the source (hero slam + CTA URL — these are the load-bearing thumbnail moments). Critically: **preserve the playbook contract** — the phase IDs `#phase1-4`, the inner element IDs the playbook fills (`#p1-hero`, `#p1-caption`, `#p2-headline`, `#p2-overline`, `#p3-overline`, and a sensible mapping for the new P2/P3 elements like `#p2-pill-1/2` or `#p2-metric` and `#p3-card-1/2/3`), the timing constants `T1/T2/T3` and `P2/P3/P4`, `slam_t`, `shake_offsets`, and the audio insertion point at the end of the body. The playbook will read your new structure and fill it; just keep enough IDs intact that it can find its anchors. Then write the playbook at `.claude/skills/diy-yt-creator/new-<brand>-short.md`, the workflow YAML, and the command file. Run `npx hyperframes lint templates/shorts/<brand>` until clean."_

**Result:** Visually unique scenes that still play nicely with the playbook and `compute_timings.py`. ~20-40 minutes depending on layout complexity.

For an in-repo reference: the **anthropic template's Phase 2 (single oversized metric) and Phase 3 (typographic chapter list)** are concrete examples of Option C applied to a real template. Compare `templates/shorts/anthropic/index.html` against `templates/shorts/archon/index.html` to see what "redesigned scenes within the same phase rhythm" actually looks like in code.

### Going further — change the phase rhythm itself

Option C keeps the 4-phase rhythm and only changes what's inside each phase. If you want to change the *rhythm itself* — different phase count (3-phase or 5-phase), different total duration, a hub-and-spoke structural pattern instead of phase mutex, a long-form 16:9 layout — that's a bigger lift. You'll need to update `scripts/compute_timings.py` to compute boundaries for your new phase count and rewrite the GSAP timeline math in `index.html`. Ask the agent to walk you through it:

> _"I want a 5-phase short template (Hero → Problem → Solution → Receipt → CTA) instead of the 4-phase default. Clone `templates/shorts/archon/`, add a `#phase5` div, extend the GSAP timeline with `T4`/`P5` anchors, update `scripts/compute_timings.py` to compute boundaries for 5 phases (the current logic assumes 4), and write a playbook for it."_

Both the agent and the codebase are designed to make these changes one-file-at-a-time and lintable at every step.

## TTS engines

The workflow generates narration via one of two TTS pipelines. Pick whichever fits your situation — the rest of the workflow is identical (same playbook, same composition edit, same lint pass):

| Engine | Cost | Quality | Voice cloning | Setup | Best for |
|---|---|---|---|---|---|
| **[Kokoro](https://github.com/hexgrad/kokoro)** (default) | Free | High (MOS 4.5 on the [LMSYS Eval](https://huggingface.co/blog/leaderboard-tts)) | No (preset voices only) | `pip install kokoro` + espeak-ng | Anyone testing the workflow, no-budget creators, fully offline use |
| **[ElevenLabs](https://elevenlabs.io)** | ~$5/M chars | Premium | Yes (Instant Voice Clone) | `pip install elevenlabs` + API key | Production channels, voice-cloned narration, max polish |

**Which Python script runs:** the create-* workflows call whichever TTS script is paired with the playbook. By default the playbooks assume Kokoro. To switch to ElevenLabs, edit the playbook step 5 to call `python scripts/elevenlabs-tts.py …` instead of `python scripts/kokoro-tts.py …` — same flags, same output contract (`narration.wav` + `transcript.json` with the same word-timestamp shape).

**Output is identical from the downstream pipeline's perspective.** Both scripts write a flat-array `transcript.json` keyed on `{word, start, end}`. `scripts/compute_timings.py`, `npx hyperframes lint`, and the GSAP timeline edits all work without modification.

**First-run cost for Kokoro:** a one-time ~325MB model download from Hugging Face. After that, generation is fully offline and runs on CPU at roughly real-time speed (a 30-second short generates in ~30-40 seconds on a modern laptop).

## Voice tuning (ElevenLabs)

The defaults in `.env.example` are the tested sweet spot for an Instant Voice Clone on shorts:

| Setting | Default | Effect of going up | Effect of going down |
|---|---|---|---|
| `ELEVENLABS_STABILITY=0.40` | | More monotone | Phoneme artifacts ("incoherent words") |
| `ELEVENLABS_STYLE=0.70` | | Artifacts return at high style + low stability | Flatter, less excitement |
| `ELEVENLABS_SIMILARITY_BOOST=0.75` | | Locks to reference timbre, suppresses prosody | Drifts further from the reference voice |
| `ELEVENLABS_SPEED_SHORTS=1.15` | | Compresses phonemes + sentence-final intonation (sentences sound mid-thought) | Slower, more breathing room |
| `ELEVENLABS_MODEL_ID=eleven_multilingual_v2` | | `eleven_v3` is more expressive but drifts further from clone voice | `eleven_turbo_v2_5` is faster + cheaper but flatter |

See the comment block inside `.env.example` for the full tuning matrix. If a clone sounds monotone, the first knob is stability ↓. If it sounds garbled, stability ↑ first.

Script-level rules (enforced by the playbook): SSML `<break time="0.35s"/>` between sentences, `<break time="0.4s"/>` at phase boundaries (NOT 0.65s — causes re-entry artifacts), natural abbreviations only, selective CAPS on 1-2 power words per phase.

## Remote workflow state (optional Postgres / Neon)

By default Archon stores workflow runs, conversation messages, and isolation state in a local SQLite file at `~/.archon/archon.db`. Fine for a single machine. If you want shared/remote state — multiple machines hitting the same history, queryable from a dashboard, or just durability beyond the laptop — point Archon at a Postgres database instead.

### Switch to Postgres

Set `DATABASE_URL` in `~/.archon/.env` (applies to every project on this machine) or `<project>/.archon/.env` (this project only):

```bash
# Neon (recommended for zero-ops Postgres)
DATABASE_URL=postgresql://USER:PASSWORD@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require

# Self-hosted / Supabase / RDS
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/dbname
```

Verify it took:

```bash
archon doctor   # Database line should now read: reachable (postgresql)
```

That's it. No migration command — Archon initializes its schema on first connect.

### Caveats

- **One-way switch.** Setting `DATABASE_URL` does not import your existing SQLite history. Dump it manually if you care: `sqlite3 ~/.archon/archon.db .dump > archon-backup.sql`.
- **Per-repo override wins.** If you put `DATABASE_URL` in both `~/.archon/.env` and `<project>/.archon/.env`, the project file wins for workflows run inside that repo.
- **Neon free tier suspends idle.** First connect after suspend pays a cold-start (~1s). Not a problem for `archon workflow run` (long-running anyway), but `archon doctor` may feel slow on a cold DB.
- **SSL is mandatory on managed hosts.** Always append `?sslmode=require` to the Neon URL (their dashboard does this for you).

## Output

```
videos/<slug>/
├── index.html              ← root composition (HTML + GSAP timeline)
├── meta.json, hyperframes.json, DESIGN.md, README.md
├── script.txt              ← narration source (with <break> tags inline)
├── audio/
│   ├── narration.wav       ← Kokoro 24kHz PCM, or ElevenLabs (MP3 decoded via ffmpeg)
│   └── narration-chunks/   ← per-chunk intermediates if you use chunked ElevenLabs mode (gitignored)
├── transcript.json         ← word-level timestamps (same shape from either TTS engine)
├── assets/                 ← per-template assets (logos, etc.)
└── out/                    ← rendered MP4 (gitignored)
```

`videos/<slug>/` is committed to git so every generation is a permanent gallery entry. Only the rendered MP4 and per-chunk TTS intermediates are gitignored.

## Customization

- **TTS engine** — pick Kokoro (free, default) or ElevenLabs (paid) via the appropriate `.env` vars; see "TTS engines" above.
- **Voice (Kokoro)** — set `KOKORO_VOICE` in `.archon/.env`. Catalog: <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md>.
- **Voice (ElevenLabs)** — set `ELEVENLABS_VOICE_ID` in `.archon/.env`. Documented presets: Brian `nPczCjzI2devNBz1zQrb`, Adam `pNInz6obpgDQGcFmaJgB`, Daniel `onwK4e9ZLuTAKqWW03F9`. Or use your own clone's ID.
- **Voice tuning matrix (ElevenLabs)** — see `.env.example` and the table above.
- **Default duration** — edit `let duration = 30;` in any `.archon/workflows/create-<template>-short.yaml` (the `parse-input` JS).
- **Range guard** — same file: `if (duration < 10 || duration > 300)` clamps to 10s-5min.
- **Slug stopwords** — same file: `STOPWORDS` Set; add product/company names so they don't bloat slugs.
- **Script style rules** — each playbook at `.claude/skills/diy-yt-creator/new-<template>-short.md` step 4 documents break-tag layout, CAPS guidance, abbreviation conventions.

## Repo layout

```
.
├── .archon/
│   ├── workflows/
│   │   ├── create-classic-short.yaml           ← spawns a brand-neutral short (DEFAULT)
│   │   ├── create-archon-short.yaml            ← spawns an Archon-themed short
│   │   └── create-anthropic-short.yaml         ← spawns an Anthropic-themed short
│   ├── commands/
│   │   ├── create-classic-short.md             ← AI command driving the classic playbook
│   │   ├── create-archon-short.md              ← AI command driving the Archon playbook
│   │   └── create-anthropic-short.md           ← AI command driving the Anthropic playbook
│   ├── plans/port-create-archon-short.md       ← origin-port reference
│   └── config.yaml
├── .claude/
│   ├── rules/                                  ← project-wide rules the AI follows
│   └── skills/
│       ├── diy-yt-creator/                     ← the playbooks (one per template)
│       ├── hyperframes/                        ← framework patterns (palettes, refs)
│       ├── hyperframes-cli/                    ← CLI command reference
│       └── archon/                             ← Archon workflow authoring docs
├── templates/shorts/
│   ├── classic/                                ← brand-neutral template (deep navy + blue/sky-blue) — DEFAULT
│   ├── archon/                                 ← Archon-themed template (dark blue + cyan/magenta)
│   └── anthropic/                              ← Anthropic-themed template (near-black + orange/cream)
├── scripts/
│   ├── kokoro-tts.py                           ← FREE local TTS (Apache-licensed, ~325MB model, espeak-ng)
│   ├── elevenlabs-tts.py                       ← PAID ElevenLabs TTS with MP3 + ffmpeg decode
│   ├── tts_lib.py                              ← chunked-generation lib for ElevenLabs (delta-regen)
│   ├── compute_timings.py                      ← derives phase boundaries, slam_t, hero entrance, etc.
│   └── list_voices.py                          ← list available ElevenLabs preset voices
└── videos/<slug>/                              ← one folder per generated short
```

## Caveats

- **Kokoro first run downloads ~325MB.** The Hugging Face model cache lives at `~/.cache/huggingface/`. After the first run, generation is fully offline. If you see a "model not found" error, your network blocked the download — set `HF_HUB_OFFLINE=0` and retry.
- **Kokoro needs `espeak-ng` system-wide.** This is a separate install (not in pip). See Quick Start step 3 for the OS-specific install command. If the script errors with "espeak-ng not found," that's the cause.
- **ElevenLabs PCM output is Pro-tier only.** `scripts/tts_lib.py` requests `mp3_44100_128` (available on Creator and below) and decodes to PCM via ffmpeg. If you're on Pro and want pure PCM, edit `tts_lib.py` to switch `output_format`.
- **Phantom punctuation in transcripts.** ElevenLabs occasionally emits a standalone `.` word around `<break>` tags. `clean_sync_data` in `tts_lib.py` filters these defensively so phase-boundary math doesn't drift. (Kokoro doesn't have this issue.)
- **Break-tag re-entry artifacts (ElevenLabs).** Phase-boundary `<break>` durations of 0.65s+ can cause an audible click/breath when the model resumes. The playbook uses 0.4s for phase breaks and 0.35s for inter-sentence breaks — proven artifact-free in 20+ test runs.
- **Speed ceiling is 1.15 (both engines).** Going to 1.20 compresses phonemes (more garbled output) AND flattens sentence-final intonation (sentences sound mid-thought, like they didn't end).
- **Bun on Windows + multi-line `bun -e`.** Archon spawns inline bun scripts via Node's `execFile`; on Windows, bun truncates the script at the first newline (silent — exit 0, no error). The `parse-input` node uses a bash wrapper (`mktemp` + `bun run`) to avoid this.
- **AI fabrication risk.** If WebFetch / WebSearch fails, the playbook may invent statistics. If you spot fabrications, restart with a source URL embedded in the topic ("Topic — see https://example.com/blog/").
- **Repo name is historical.** This stack pivoted from Remotion to HyperFrames mid-2026. The repo name reflects the original Remotion-based project; the active stack on `main` is HyperFrames.

## Provenance

Ported from `diy-yt-creator-hyperframes`. Current `main` is HyperFrames + (Kokoro or ElevenLabs) single-call with the tuned settings matrix documented above. ElevenLabs voice settings, break-tag durations, and the MP3 + ffmpeg decode pipeline were validated over a live tuning session. Kokoro support was added once the engine matured to MOS 4.5 with native word-level timestamps — the same `transcript.json` shape works for both engines downstream.

## License

MIT
