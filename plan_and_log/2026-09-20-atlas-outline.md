# Atlas choices and whole-brain outline

Goal: expose other supported BrainGlobe atlases and restore an independent
whole-brain outline checkbox alongside 3D region masks.

1. Check the current loader, installed API registry and official atlas list.
2. Offer editable rat/mouse atlas choices without downloading on startup or
   inventing Bregma calibration for another coordinate space.
3. Load the cached lightweight root mesh on the existing worker; display it as
   a separate white 50%-opacity layer with its own checkbox. Preserve region
   selection, opacity, slice and camera behavior.
4. Inspect scoped diffs and run at most one lightweight changed-file check.

Deferred by user: after deselecting all region masks, some masks remain visible.
Reproduce and fix selection/visibility synchronization in a later task; this
change does not claim to fix that bug. The outline is independently visible.

Sources: BrainGlobe atlas details (accessed 2026-09-20), installed
brainglobe-atlasapi 2.3.1 and the existing local last_versions.conf. Region masks
use annotation labels/hierarchy and require corresponding structures. Only WHS
rat v1.2 currently has an automatic Bregma preset in Atlaxis. No new atlas data
download or atlas-to-animal registration is part of this change.

Outcome (uncommitted):
- Replaced the atlas text field with an editable list of ten rat/mouse choices;
  arbitrary supported BrainGlobe names remain accepted. All suggested names were
  present in the installed API's cached registry. No new Bregma origin was assumed.
- Restored the root surface via existing background `load_display_mesh`/50k-face
  cache. Added a separate initially enabled Brain outline actor/check, white at
  fixed 0.5 opacity. Region visibility/opacity changes do not modify this actor;
  changing atlas replaces the old outline. No annotation or mask logic changed.
- Updated README with atlas choices, calibration limits and the explicitly deferred
  deselect-all issue. Source/diffs reviewed for the loader signal/slot, combo callers,
  scene actor lifecycle and independent visibility state.
- One offscreen startup/checkbox check was attempted using
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -`
  (inline MainWindow creation, atlas combo selection and checkbox state assertions).
  It exited 139 before the success marker. Output included Matplotlib temporary
  font-cache and Qt font-alias messages, with no assertion traceback. The GUI check
  did not pass; the cause was not diagnosed. No retry or broader checks were run.
- Remaining: verify outline appearance/toggling on the normal macOS GUI and load
  alternative datasets. Those atlases were not downloaded or integration-tested.
  Region deselect-all behavior remains deferred as requested. No commits.

## Follow-up: atlas picker and anterior nerve display

Goal: choose atlases in a window opened by Load atlas and omit the protruding
Waxholm trigeminal nerves from the default display, including the white outline.

1. Move the existing editable atlas choices into a modal picker; cancellation
   must retain the current atlas/plan, and loading must remain on the worker.
2. Default Waxholm's exact `5n` label to unselected, keeping it available in
   Region mask. Do not hide optic nerves, olfactory bulbs or other fiber tracts.
3. Generate/cache a display-only outline from native nonzero labels excluding
   `5n`, with the existing 50k-face cap. Keep annotations, mapping, coordinates,
   brain-surface DV and the separate outline checkbox unchanged. Following the
   user's additional request, lower white outline opacity to 20% (80% transparent).
4. Inspect scoped diffs and perform one lightweight changed-file syntax check;
   no GUI rendering or dataset-wide verification in this follow-up.

Identification: the screenshot's anterior extensions appear to be the trigeminal
nerves. WHS v4.01 separately labels these as `504 / 5n`, replacing part of the
older spinal trigeminal tract (NITRC release 4822). The underlying annotation is
not modified. Region mask can restore the colored nerve surface; the simplified
white outline continues to omit it. The existing deselect-all issue stays deferred.

Follow-up outcome (uncommitted):
- Load atlas now opens an editable modal picker with the existing choices and
  current-atlas preselection. Cancel precedes any unsaved-plan prompt or loading;
  the main panel shows the successfully loaded name as a label.
- Waxholm `5n` starts unselected. Its label is also excluded from the separately
  cached outline's native-resolution binary contour. Other atlas labels and
  the original data remain intact. Cache identity includes excluded IDs and
  annotation file size/mtime. Outline opacity is now 0.2.
- The shared contour helper fills a padded Fortran-order mask one plane at a
  time; existing single-label contours retain their coordinates and half-voxel
  boundaries. This avoids extra full-volume mask/layout copies for the outline.
- Reviewed diffs against snapshots of the pre-existing untracked source, plus
  README changes. One syntax check passed (exit 0):
  `PYTHONPYCACHEPREFIX=/tmp/atlaxis-atlas-picker-before.vfXkbU/pycache .venv/bin/python -m py_compile src/probe_planner/ui/main_window.py src/probe_planner/rendering/regions.py src/probe_planner/rendering/scene.py`.
- No GUI, atlas contour generation or cache generation was run in this follow-up;
  visual appearance and first-load performance remain unverified. The first
  subsequent Waxholm load will generate the new outline cache on the worker.
  Temporary snapshots/bytecode were removed after diff inspection and compilation.

## Follow-up: visible full atlas catalogue

The user reports that the generic input dialog shows only the Waxholm text field,
with no discoverable atlas list. Replace it with a dedicated list-based picker.

1. Show a searchable atlas table immediately from BrainGlobe's cached/custom
   catalogue and installed atlas names; include the current atlas.
2. Refresh the official catalogue asynchronously with a bounded Qt network request,
   retaining local choices on failure. Show downloaded versus download-on-load.
3. Load the selected row through the existing worker; preserve cancellation and
   saved-plan behavior. Do not invent Bregma presets or download atlas volumes as
   part of listing. Review the source/diff; no further runtime checks are planned
   in this ongoing task after the already-performed syntax check.

Additional user-reported outline issue: the raw nonzero-label contour also shows
internal void walls and narrow annotation gaps when transparent. For the display
outline only, close gaps with a two-voxel (78 µm at WHS resolution) morphological
radius, then fill enclosed holes before contouring. This is a visual envelope,
not an anatomical segmentation change: region meshes, reference images, contact
mapping and DV retain native data. The outer envelope may fill narrow surface
clefts within that closing radius; no measured geometric error is claimed. Use
an unlit white actor to avoid distracting facet highlights and a new cache key.
Also exclude the remaining anterior optic nerves (`2n`) from the default display
and outline, retaining their selectable region entries and the olfactory bulbs.

Catalogue/outline follow-up outcome (uncommitted):
- Added `ui/atlas_dialog.py`: a permanently visible searchable table, local
  catalogue/installed entries shown immediately, asynchronous official catalogue
  refresh using Qt Network with a 10-second transfer timeout, and explicit
  download status. Selection/cancellation feed the existing atlas worker.
  Registered custom atlases are included; the old free-text-only picker is gone.
- Added optic nerves (`2n`) to default hidden labels alongside `5n`. The outline
  uses the documented display-only closing/filling and unlit 0.2-opacity white.
  Exact individual region contours retain one-voxel padding and no morphology.
  Updated the outline cache suffix to `shell-v2` so old artifacts are not reused.
- Inspected the complete scoped diffs and installed BrainGlobe catalogue and mesh
  generation source. No new runtime, syntax, GUI, network or atlas-generation
  checks were run after these edits; the earlier successful syntax check predates
  this final code. Actual artifact removal and catalogue UI rendering remain to
  be checked in the application. No atlas volumes downloaded, no commits.
- README updated. Temporary source snapshots were removed after review.
