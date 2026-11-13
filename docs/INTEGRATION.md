# Source reconciliation

The public source snapshot is prepared in the **outer** `SpatialBuild/` directory.
The original nested `SpatialBuild/` checkout is preserved locally and ignored by
the outer repository. Run Git publication commands from the outer directory.

## Inputs and decisions

| Input | Resolution |
| --- | --- |
| Team repo `archakamk/SpatialBuild`, revision `ba2536651d0a20c4c04a7effddc783a3af1e339d` | Import the latest audio, vision, and reconstruction source. |
| Original local checkout at `5f689af` plus uncommitted changes | Keep the checkout untouched; preserve its audio implementation byte-for-byte in `audio_pipeline/extract_audio_local.py`. |
| Outer reconstruction files | These matched the team revision exactly before reconciliation; retain this newer implementation. |
| Older inner reconstruction implementation | Carry forward dataset `--test` mode and configurable OpenSplat discovery without reverting the newer COLMAP, viewer, and training fixes. |
| Machine-specific `/workspace/SpatialBuild` defaults | Use checkout-relative defaults for the reconstruction orchestrator, setup workspace, and SAM 2 checkpoint. |
| OpenSplat setup | Create the build directory after cloning, so a fresh install does not fail on a nonempty clone destination. |
| API credentials, SSH keys, source video, generated media, model weights | Exclude from the publication tree. Track empty data directories for fresh clones. |
| Git ancestry | The fetched team history has no common ancestor with the old local checkout. Prepare a fresh, attributed source snapshot in the previously empty outer Git repository; retain both original histories in the nested checkout. |
| World Labs / Marble | No implementation found in either local copy or the current team source tree. Proceed with available changes as requested; existing mesh generation uses Tripo3D. |

The team README referred to frontend files, screenshots, and a license file that
were absent from the source tree. The prepared README describes available code
and does not introduce a new license for the team's work.

## Publishing

The public destination is `sudhanvad18/SpatialBuild`. The outer repository's
`origin` points there; `upstream` identifies the team repository. Nothing is
published by the pipeline scripts themselves.

The public repository has been created. Push subsequent commits from the outer
directory:

```bash
git push -u origin main
```

Use only the outer repository's `main` branch for this source snapshot; the
original nested checkout is a local reference, not the publication source.
