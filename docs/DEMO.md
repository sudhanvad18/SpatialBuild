# Demonstrating SpatialBuild

[Watch the captioned walkthrough](assets/spatialbuild-walkthrough.webm) · [Animated preview](assets/spatialbuild-preview.gif) · [Static poster](assets/spatialbuild-demo-poster.png) · [Captions](assets/spatialbuild-captions.vtt)

The 32-second walkthrough explains the source architecture and a real execution of `vision_pipeline/src/adapt_commands.py`. Its explicit fixture maps a 15.2-second command at 30 fps to frame 456 and resolves `red` to `[255, 0, 0]`. The diagrammed stages follow the implementation.

This is an architecture/component demonstration, not an end-to-end inference recording. It does not show segmentation, edited camera frames, GPU reconstruction, or a hosted frontend. The pipeline graphic is also an implementation diagram rather than model output.

## Record the complete pipeline

Use one recording that can be shared publicly and one simple edit, such as recoloring a wall. Keep the original camera movement visible so viewers can follow the same surface through multiple frames.

A 45–60 second recording should show:

1. The original walkthrough and the spoken request.
2. The extracted command, timestamp, and selected frame.
3. Original and edited frames at matching timestamps.
4. The reconstructed PLY in the bundled point-cloud viewer, explicitly labeled as that rendering mode.

Pair the clip with one side-by-side still image near the top of the README. Describe the input, selected command, hardware, model versions, reconstruction iterations, and observed runtime in its caption or a linked run note. Publish measurements only when they come from a recorded run.

## Keep the result reproducible

Save a small command JSON example and the exact invocation used. If distributing the input recording is appropriate, link it from the run note; otherwise explain which steps a reader can reproduce using their own recording. Keep large videos and model files outside Git history and provide a lightweight screenshot fallback.

For a controlled reconstruction check, use `python reconstruction_pipeline/run_pipeline.py --test --serve` after installing the native tools. This demonstrates reconstruction on a downloaded reference dataset, rather than the full speech-to-edit workflow.
