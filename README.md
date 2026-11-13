# SpatialBuild

SpatialBuild turns a recorded room walkthrough and spoken edit requests into
edited video frames and a navigable Gaussian splat. The camera direction helps
identify which object a command such as “paint this wall green” refers to.

This repository combines the team project from
[archakamk/SpatialBuild](https://github.com/archakamk/SpatialBuild) with Sudhanva
Deshpande's local audio and reconstruction work. See [integration notes](docs/INTEGRATION.md)
for the source revision and reconciliation decisions.

## Pipeline

1. **Audio:** convert MOV to MP4/MP3, transcribe with Whisper, and extract timed
   edit commands using Gemini or a local Qwen model.
2. **Vision:** Grounding DINO identifies the target; SAM 2 segments and tracks it.
   The edit engine recolors surfaces, applies textures/images, or removes objects
   with LaMa inpainting.
3. **Reconstruction:** COLMAP estimates cameras and OpenSplat trains a Gaussian
   splat from the edited frames.
4. **Viewer:** generate a browser viewer, optionally with Tripo3D furniture meshes.
   ElevenLabs confirmations and Gemini reports are optional vision features.

## Setup

Use Python 3.10+ and a GPU environment for the full vision/reconstruction pipeline.
The team configuration targets CUDA or AMD ROCm (PyTorch uses the `cuda` device
name for both). Local audio also supports Apple MPS and CPU.

```bash
git clone https://github.com/deshpa70/SpatialBuild.git
cd SpatialBuild
python3 -m venv .venv
source .venv/bin/activate
# Install the torch/torchvision build appropriate for your GPU first.
python -m pip install -r requirements.txt
```

Install system `ffmpeg`. Install SAM 2 and its checkpoint separately:

```bash
git clone https://github.com/facebookresearch/sam2.git vision_pipeline/sam2
SAM2_BUILD_CUDA=0 python -m pip install -e vision_pipeline/sam2
(cd vision_pipeline/sam2/checkpoints && bash download_ckpts.sh)
```

`SAM2_BUILD_CUDA=0` skips SAM 2's optional CUDA extension. Leave it unset when
building that extension for a compatible CUDA system. The default checkpoint is
`vision_pipeline/sam2/checkpoints/sam2.1_hiera_large.pt`; override it with
`SAM2_CHECKPOINT` if needed.

For reconstruction, install COLMAP and OpenSplat. The optional
`reconstruction_pipeline/setup.sh` targets Ubuntu and installs system packages,
Python dependencies, LibTorch, and OpenSplat. Review it before running it on a
GPU machine. Set `OPENSPLAT_BIN` to an existing build, or use the setup script's
`.pipeline_config`. The setup script has not been validated across GPU platforms.

API credentials are read from the shell environment. [.env.example](.env.example)
lists the optional variables; scripts do not load that file automatically.

```bash
export GEMINI_API_KEY="your-key"       # Gemini audio extraction / reports
export ELEVENLABS_API_KEY="your-key"   # optional voice confirmations
export TRIPO3D_API_KEY="your-key"      # optional furniture generation
```

## Run

Place a MOV recording in the project root. Audio scripts select the first MOV
in `audio_pipeline/`, then the root; use one recording at a time.

```bash
# Choose one audio backend (both write audio_pipeline/outputs/).
python audio_pipeline/extract_audio.py          # Whisper + Gemini
# python audio_pipeline/extract_audio_local.py  # Whisper + local Qwen, no Gemini key
```

The local backend preserves the original `Qwen/Qwen2.5-3B-Instruct` command
extractor and downloads approximately 6 GB of model weights on its first run.

Use the recording's real frame rate consistently for extraction and command
conversion; the example below uses 30 fps. Replace `walkthrough` with your MOV's
filename stem.

```bash
ffmpeg -i walkthrough.MOV -vf "fps=30,scale=720:-2" -start_number 0 \
  -q:v 2 vision_pipeline/data/frames/frame_%06d.jpg

cd vision_pipeline
python -m src.adapt_commands \
  --input ../audio_pipeline/outputs/walkthrough.commands.json \
  --output commands.json --fps 30
python -m src.run_pipeline --frames data/frames --commands commands.json \
  --output data/edited_frames --dry-run
# Remove --dry-run to load the models and apply edits.
# Add --voice and/or --report for optional API features.
cd ..

python reconstruction_pipeline/run_pipeline.py \
  --frames vision_pipeline/data/edited_frames --iterations 2000 --serve
```

Open `http://localhost:8080/viewer.html` when reconstruction finishes.
The bundled Three.js viewer displays the PLY as a point cloud; it does not
implement full Gaussian splat rendering.
`python reconstruction_pipeline/run_pipeline.py --test --serve` downloads the
OpenSplat banana dataset and uses separate test output/workspace directories.

Texture and image-placement commands require the corresponding user-provided
files under `vision_pipeline/data/textures/`. General furniture `add` commands
are handled by reconstruction's optional `--commands` option; the vision router
accepts `recolor`, `retexture`, `remove`, and `place_image`.

## Verification

```bash
python -m unittest discover -s tests -v
python -m compileall -q audio_pipeline vision_pipeline/src reconstruction_pipeline
```

The regression checks cover reconciliation behavior without downloading models,
calling paid APIs, or training a splat. Full model inference and GPU training
require the external dependencies and have not been verified in this checkout.
The source snapshot does not include the separately hosted frontend, demo media,
model checkpoints, or a World Labs/Marble integration.
