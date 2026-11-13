# Setup and run

The complete pipeline needs a room recording, Python dependencies, model checkpoints, and native reconstruction tools. Set up one environment for the full run; use a fresh output/workspace for each recording.

## 1. Python and native dependencies

Use Python 3.10 or later. The vision configuration targets a CUDA-compatible PyTorch environment; AMD ROCm also uses PyTorch's `cuda` device name. Local audio can select Apple MPS or CPU. The GPU setup script has not been validated across all platforms.

```bash
git clone https://github.com/sudhanvad18/SpatialBuild.git
cd SpatialBuild
python3 -m venv .venv
source .venv/bin/activate
# Install torch/torchvision for your chosen GPU platform first.
python -m pip install -r requirements.txt
```

Install system `ffmpeg` and COLMAP. Install SAM 2 and its checkpoint separately:

```bash
git clone https://github.com/facebookresearch/sam2.git vision_pipeline/sam2
SAM2_BUILD_CUDA=0 python -m pip install -e vision_pipeline/sam2
(cd vision_pipeline/sam2/checkpoints && bash download_ckpts.sh)
```

`SAM2_BUILD_CUDA=0` skips the optional CUDA extension. Leave it unset to build the extension on a compatible CUDA system. By default, the pipeline expects `vision_pipeline/sam2/checkpoints/sam2.1_hiera_large.pt`; set `SAM2_CHECKPOINT` to override the path.

Reconstruction also requires an OpenSplat binary. Set `OPENSPLAT_BIN` to an existing installation. Alternatively, review and run `reconstruction_pipeline/setup.sh` on a suitable Ubuntu machine; it installs system packages, LibTorch, and OpenSplat and writes `.pipeline_config`. It performs system-level installation and is not a general macOS setup script.

## 2. Choose the audio backend

Put a single MOV recording in the repository root. Scripts choose the first MOV in `audio_pipeline/`, then the root; remove ambiguity by keeping one input recording in those locations.

Choose one:

```bash
# Whisper transcription + Gemini command extraction
export GEMINI_API_KEY="your-key"
python audio_pipeline/extract_audio.py

# Or Whisper transcription + a local Qwen model
# python audio_pipeline/extract_audio_local.py
```

The local command extractor uses `Qwen/Qwen2.5-3B-Instruct` and downloads approximately 6 GB of model weights on its first run. Both backends write media, transcripts, word timestamps, and `<stem>.commands.json` to `audio_pipeline/outputs/`.

Scripts read credentials from the shell environment. `.env.example` documents variable names but is not automatically loaded. `ELEVENLABS_API_KEY` enables optional voice confirmations; `TRIPO3D_API_KEY` enables optional furniture generation.

## 3. Extract frames and align commands

Replace `walkthrough` with the recording's actual filename stem. This example uses the current 30 fps video configuration. If changing it, update `vision_pipeline/src/config.py` as well as extraction and command conversion.

```bash
ffmpeg -i walkthrough.MOV -vf "fps=30,scale=720:-2" -start_number 0 \
  -q:v 2 vision_pipeline/data/frames/frame_%06d.jpg

cd vision_pipeline
python -m src.adapt_commands \
  --input ../audio_pipeline/outputs/walkthrough.commands.json \
  --output commands.json --fps 30
python -m src.run_pipeline --frames data/frames --commands commands.json \
  --output data/edited_frames --dry-run
```

The dry run prints the planned commands without loading the editing models or writing edited frames. It still imports the installed Python vision dependencies. Remove `--dry-run` to execute the edits. Add `--voice` or `--report` only when the corresponding optional service is configured.

`retexture` and `place_image` requests need the referenced files under `vision_pipeline/data/textures/`. The vision router rejects general furniture `add` actions; use supported frame edits for this stage and pass furniture requests separately to reconstruction.

## 4. Reconstruct edited frames

After the vision commands above, return to the repository root and run:

```bash
cd ..
python reconstruction_pipeline/run_pipeline.py \
  --frames vision_pipeline/data/edited_frames --iterations 2000 --serve
```

After completion, open `http://localhost:8080/viewer.html`. The run writes `reconstruction_pipeline/output/splat.ply` and `viewer.html`. The bundled Three.js viewer displays point-cloud geometry; it does not reproduce full Gaussian rendering.

To use the OpenSplat banana dataset instead of a personal recording:

```bash
python reconstruction_pipeline/run_pipeline.py --test --serve
```

This downloads data and runs reconstruction. Its outputs and workspace are kept in `test_output/` and `test_workspace/`. It is distinct from the mocked regression suite.

Pass `--output` and `--workspace` for separate recording runs. Existing reconstruction artifacts can cause stages to be skipped; use `--force` only when deliberately recomputing them. Run `python reconstruction_pipeline/run_pipeline.py --help` for the full CLI.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| A command targets the wrong moment | Match extraction fps, adapter fps, and `FRAME_RATE`; inspect the command's `frame_idx`. |
| SAM 2 checkpoint not found | Install the checkpoint or export `SAM2_CHECKPOINT`. |
| OpenSplat not found | Export `OPENSPLAT_BIN` to an executable build or inspect the setup-generated configuration. |
| No frames for reconstruction | A vision dry run does not create edited frames; execute the real edit stage first. |
| `unknown action 'add'` | Use supported frame edits in vision and reconstruction's furniture command path for general additions. |
