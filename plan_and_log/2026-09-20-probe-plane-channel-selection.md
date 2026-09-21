# Probe plane and Neuropixels channel selection

## Goal and scope
Show a native-resolution atlas section in the probe's physical plane, integrate
NeuroCarto automatic site selection and IMRO routing, and show per-probe Geometry
and Channel map tabs. Distinguish local CA1 targets by user-drawn site ranges,
without inventing dorsal/ventral atlas labels. Selected shank: thin cyan edge;
active sites: magenta. Preserve poses, physical geometry and existing atlas views.

## Implementation steps
1. Add a probe-plane sampler using the existing physical transform. Sample labels
   by voxel containment (floor), reference intensities with linear interpolation;
   use the smallest native voxel pitch, bounded row chunks and background work.
2. Add zoomable geometry/plane views, channel/region labels at readable zoom and
   tooltips; add per-probe Geometry / Channel map tabs retaining the existing table.
3. Adapt supported catalog NP1000/NP2003/NP2013 topology to NeuroCarto 0.2.2.
   Retain actual hardware channel IDs, validate geometry and IMRO type/routing,
   persist per-site density categories and generated/imported routing in plans.
4. Add manual rectangle + atlas-region filtering, NeuroCarto Generate, IMRO import
   and export. Exclude unannotated/outside sites during automatic selection. Never
   fill excluded sites to reach 384; report incomplete maps and disable IMRO export.
5. Review scoped changes and run one permitted lightweight changed-file check.

## Semantics and boundaries
- Probe plane: local XY at the reference shank's contact-face Z; all sites are
  projected for display, with off-plane distances disclosed. Site region lookup
  always uses its true 3D position, not the sampled pixel. Probe roll is preserved.
- Reference resampling is display-only; labels and channel targeting use native
  voxel containment. No resolution or scientific-coordinate changes.
- Density categories are site selections, retained when pose changes. Generate is
  explicit; moving the probe updates region labels but never silently remaps it.
- Dorsal/ventral CA1 ranges are manual selections intersected with atlas regions;
  they are not inferred anatomical labels. NeuroCarto's stochastic default selector
  and hardware routing are reused directly. Store results, not a claimed seed.
- Supported hardware: catalog NP1000 (IMRO 0), NP2003, NP2013 only. Existing NP2
  tip-offset uncertainty remains. IMRO export requires all 384 channels.
- New optional ChannelMap fields preserve loading of existing plans. No tests or
  broad verification added. No independent agent workflow under project rules.

## Result (uncommitted)
- Added the asynchronous Probe plane tab, site-range painting intersected with
  atlas regions/descendants, per-probe Geometry / Channel map tabs, cursor zoom,
  readable channel/region labels and site tooltips. The existing 3D scene remains
  the default. Cyan outlines and magenta active sites are shared across views.
- Added the real NeuroCarto default selector, strict catalog topology adapter,
  complete-map IMRO import/export and optional persisted `blueprint`/`source_imro`
  ChannelMap fields. Selection runs in a background thread. Routing changes do
  not reset the 3D camera. Partial maps remain partial and cannot be exported.
- Pinned NeuroCarto 0.2.2, updated the lockfile and retained its BSD-3-Clause
  license. Existing dependency versions were unchanged. Catalog routing notices
  and usage documentation now describe the available workflow.
- UI scope was refined by the user during implementation: right-hand nested tabs,
  scrollable geometry, cyan reference-shank edge and magenta active channels.
  These refinements are included; no scientific coordinate semantics changed.

### Verification actually performed
- Reviewed task-scoped source/diffs against pre-edit snapshots (repository files
  were already untracked). No tests, fixtures or broad checks were added/run.
- Ran the one permitted lightweight import check:
  `.tools/bin/uv run --locked --offline --cache-dir .uv-cache python -c 'from probe_planner.ui.main_window import MainWindow; print("MainWindow import OK")'`
  Result: exit 0, `MainWindow import OK`. Matplotlib used a temporary font cache
  because the sandbox did not allow writing its default cache directory.
- Feature dependency installation: `.tools/bin/uv add --cache-dir .uv-cache 'neurocarto==0.2.2'`
  completed successfully. This was required for the requested integration.

### Remaining verification and limitations
- GUI interactions, real atlas oblique rendering, numerical sampling behavior,
  selection results and hardware IMRO round trips were not executed in this task.
  The import check does not establish runtime correctness of those paths.
- Automatic selection supports the three catalog NP variants only. IMRO imports
  require the matching type code, a uniform reference and one bank per channel;
  multi-bank and per-channel-reference configurations are rejected.
- CA1 subdivisions remain user-selected ranges, not inferred atlas labels.
  Pose changes retain physical site categories/maps; Generate re-evaluates brain
  eligibility. NP2's existing provisional tip offset is unchanged.
- The plane includes a 1.5 mm margin around sites/tip; non-coplanar contacts are
  projected and disclosed, while their region lookup uses original 3D positions.

## Follow-up: fixed-channel probes and wider plane
Requested: all contacts of non-Neuropixels probes are active; widen Probe plane.
Steps:
1. Share active-site classification across 3D, Geometry, tooltips, counts and
   region rows/CSV. Non-NP contacts are all active, including unmapped contacts;
   preserve NP routing/skipped-channel behavior and never invent hardware IDs.
2. Increase the sampled margin from 1.5 to 5 mm on each side, keeping native
   pixel pitch, plane transforms and background chunked sampling unchanged.
3. Review the scoped diff and record verification. No new tests or broad checks.

Follow-up result (uncommitted): implemented the shared active-site policy for
all display/summary/CSV paths. Ordinary probes show N/N active contacts, retaining
unknown channel IDs rather than generating wiring assignments. NP activity still
depends on the routed, non-skipped sites. Increased all plane margins to 5 mm;
native sampling pitch and transformations are unchanged.

Reviewed the scoped diff against pre-edit snapshots. One lightweight syntax
check passed (exit 0):
`PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-active-pycache .venv/bin/python -m py_compile src/probe_planner/probes/neuropixels.py src/probe_planner/implant/region_mapping.py src/probe_planner/rendering/scene.py src/probe_planner/rendering/probe_view.py src/probe_planner/ui/probe_summary.py src/probe_planner/atlas/probe_section.py`
No tests were added or run. GUI interactions and live atlas rendering remain
unverified in this follow-up.

## Follow-up: partial export, reset and marker appearance
The reported 288/384 selection cannot be exported because the UI only enables
complete IMRO maps. Reset currently edits density categories without clearing
the active map. User also requests 50% marker opacity, smaller markers and an
orientation cube at 80% of its current size.

Steps:
1. Make partial selections exportable while preserving selected hardware IDs;
   determine whether acquisition IMRO completion or selected-only JSON/CSV is
   preferred. Never silently present added acquisition channels as target sites.
2. Make Reset clear only the current NP map/blueprint and refresh counts, sites,
   default selection controls and fitted views; keep poses and other probes.
3. Apply 0.5 opacity and smaller active markers consistently, and reduce the cube
   viewport side from 144 to 115.2 logical pixels without changing picking.
4. Review the scoped diff and run at most one focused permitted check. No new tests.

IMRO format reference: https://billkarsh.github.io/SpikeGLX/help/imroTables/ .
The installed NeuroCarto 0.2.2 serializer explicitly requires 384 populated slots.

User chose acquisition IMRO plus a separately saved target-channel list. Export
completion must not mutate the plan or mark filler sites as targets. Selection
JSON import restores the original partial map; IMRO alone represents all 384
acquisition assignments. Selected-only JSON/CSV remain available.

Additional request: incremental ROI assignment with independent densities.
Extend steps 1–2 to persist a pending site set alongside density categories.
Drawn ranges populate that set; Generate becomes Add channels and uses NeuroCarto
`CATE_SET` for existing active sites, while only newly drawn, eligible sites are
candidates. Each ROI keeps its chosen density category. Existing site/channel
assignments take precedence on overlapping ranges and must not move, disappear
or change IDs. Pending ranges are consumed after assignment; Reset clears them.
Empty/full-capacity/conflicting ROIs report the number added without replacing
existing selections. Preserve imported reference/gain settings for locked sites.

Result (uncommitted):
- Export is enabled for any nonempty NP selection. Acquisition export preserves
  selected hardware IDs, completes remaining slots and writes a companion
  `.selection.json` with the exact target map/list and pending ranges. The UI
  reports additional recorded sites and offers selected-only JSON/CSV as well.
  Importing the companion restores the partial target map; importing IMRO alone
  restores the complete acquisition map. Export never mutates the plan.
- Add channels processes only newly drawn pending sites and locks all existing
  sites with NeuroCarto's `CATE_SET`. Overlapping drawings and Exclude all preserve
  existing site categories; new ROI densities apply only to new candidates.
  Pending-site storage is an optional backward-compatible ChannelMap field.
- Reset clears the current NP map and restores fitted plane/Geometry views,
  default selection controls, oblique orientation and tip-following sections.
  Probe pose, mask settings, other probes and ordinary-probe activity are retained.
- Active markers/text use 0.5 opacity; active 2D markers use 3.5 µm visual radius
  with a 1.6 px minimum, and active 3D markers use 5 px instead of 7 px. Contacts
  render once in the overlay to avoid compounding alpha. Cube side is 115.2 px.

Verification: reviewed the scoped diffs against pre-edit snapshots. The original
disabled export was traced to `active == 384`; the UI now permits `active > 0`
and separates selected target sites from completed acquisition assignments.
One lightweight changed-file syntax check passed (exit 0):
`PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-export-pycache .venv/bin/python -m py_compile src/probe_planner/probes/model.py src/probe_planner/probes/neuropixels.py src/probe_planner/rendering/scene.py src/probe_planner/rendering/probe_view.py src/probe_planner/rendering/slice_view.py src/probe_planner/ui/probe_summary.py src/probe_planner/ui/probe_plane.py src/probe_planner/ui/main_window.py`
No new tests or broad checks were added/run. GUI reset/appearance, incremental
selection execution and exported IMRO acquisition/hardware behavior were not
executed. Existing full-map format/import restrictions remain unchanged.

## Follow-up: ROI table and planning bundles

Goal: manage independent NP ROIs without replacing existing selections, correct
cursor-centred Probe plane zoom, and save reusable multi-probe planning outputs.

Steps:
1. Persist ROI rows (local plane bounds in µm, region, density, physical sites,
   registration and owned assignments). Direct dragging replaces the selected
   draft only; Register freezes it. Add ROI appends a draft. Activate Channels
   assigns once per registered ROI, preserving all prior hardware assignments.
   Remove deletes only that ROI and its newly assigned channels; imported or
   earlier unowned channels and other ROIs are preserved. Reset all clears the
   current probe's ROI/map state and restores the existing default views.
2. Put the ROI table and mapped count centrally, remove Draw range / Exclude all
   and Export contacts, retain one right-side Export. Ordinary probes remain all
   active and expose no channel-selection controls. Fix zoom using the wheel
   event's cursor position rather than Qt's cached hover position.
3. Default geometry import to `probes/`; default new plans to `planning/` with
   planned coordinates, one combined XML and interoperable NP active-selection
   files. Preserve existing plan loading and physical/channel numbering; do not
   invent hardware wiring for geometry-only probes. Confirm XML convention.
4. Update affected user documentation, inspect task diffs and run at most one
   lightweight changed-file check. No new tests or broad validation.

Registered ROIs retain physical sites when the probe moves. Density uses the
existing NeuroCarto categories, not an exact count guarantee; routing conflicts
and previously locked sites still take precedence. Repeated activation must not
progressively densify an already assigned ROI. Selection ownership and ROI rows
must round-trip in plans and selection JSON. Acquisition IMRO filling remains
separate from target activity; saved coordinates explicitly state units/origin.

User confirmed NeuroScope channelGroups XML with concatenated probe-local
channels. Existing ordinary catalog geometry has no verified physical wiring:
keep unknown channels in one probe-level group, rather than inventing shank
assignments. XML is a channel-group template; no acquisition sampling/gain values
are guessed. Save each new named plan in its own `planning/<name>/` bundle,
including per-shank coordinates, channel-index CSV, NP target CSV/selection JSON
and complete acquisition IMRO for nonempty NP selections. Rename the editable
`Probe file/` library to `probes/` and update its generator/wheel inclusion.

Result (uncommitted): implemented the central ROI table, direct draft drawing,
Register/Remove, per-row activation, Add ROI, Reset all and central mapped count.
Only NP exposes selection/filter controls. Existing maps without ROI ownership
remain locked. ROI removal releases owned assignments, including from a full
map; a complete IMRO template retains remaining reference/gain settings through
partial selections. Plans/selection JSON retain rows, bounds and ownership.
Removed Export contacts, Draw range and Exclude all; ordinary probes retain
right-side CSV Export. Probe import starts at the renamed `probes/` library.

Save plan now creates `planning/<name>/plan.json` with coordinate CSV, combined
NeuroScope channelGroups XML, global/local channel-index CSV, NP target CSV/JSON,
and acquisition IMRO when targets exist. A manifest identifies obsolete NP
outputs for removal on subsequent saves. All outputs are prepared in staging
before replacement; replacement is per-file, not a filesystem-wide transaction.
XML includes no guessed sampling/gain or physical wiring; merge with actual
recording metadata and account for any auxiliary/sync channels externally.

Reviewed scoped source/diffs against `/private/tmp/atlaxis-roi-table.Xl1KgQ`.
One permitted lightweight changed-file check ran: offscreen ProbeView wheel
events at three noncentral/subpixel positions, including an image edge, with
12 zoom-in / 24 zoom-out / 12 zoom-in steps at each. Maximum cursor-anchor drift
was 0.000000000 viewport pixels over 144 events (exit 0). The assertion allows
one pixel for Qt's integer scrollbar rounding; tolerances were not adjusted.
Exact command:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-roi-zoom-pycache .venv/bin/python - <<'PY'
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication
from probe_planner.rendering.probe_view import ProbeView

app = QApplication([])
view = ProbeView(labels=False)
view.resize(900, 650)
view.bounds = QRectF(-200, -10000, 3000, 11000)
view.show()
app.processEvents()
view.fit()
errors = []
for position in (QPointF(93.25, 121.75), QPointF(740.5, 512.25), QPointF(11.5, 20.25)):
    for delta in [120] * 12 + [-120] * 24 + [120] * 12:
        anchor = view.viewportTransform().inverted()[0].map(position)
        event = QWheelEvent(position, position, QPoint(), QPoint(0, delta), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
        view.wheelEvent(event)
        after = view.viewportTransform().map(anchor)
        error = ((after.x() - position.x()) ** 2 + (after.y() - position.y()) ** 2) ** 0.5
        errors.append(error)
print(f'Maximum cursor-anchor drift: {max(errors):.9f} viewport pixels over {len(errors)} wheel events')
assert max(errors) <= 1.0, 'Cursor anchoring exceeds one pixel of Qt scrollbar rounding'
view.close()
PY
```

No test files, broad checks or environment changes were added. ROI activation,
save/load bundle round-trips, live atlas/GUI interactions and external software
import were not executed in this follow-up. NeuroScope acquisition settings and
ordinary-probe physical wiring remain user/recording metadata requirements.

## Follow-up: save revisions and explicit acquisition export

Problem: Save automatically creates IMRO/selection outputs, while later manual
Export refreshes only IMRO/JSON, leaving saved README/counts from an older state.
Goal: make saving edits predictable and keep each manual export's description
and channel files consistent with the selection that produced them.

Steps:
1. Save an existing plan directly to its current path; add Save as for a new
   named bundle. Preserve first-save naming and backward-compatible loading.
2. Save updates the plan, coordinates, combined XML/index and saved-plan README
   only. Do not generate/fill acquisition maps on Save or delete prior exports.
3. Manual NP Export builds all requested files from the current map together;
   IMRO export includes target JSON, target CSV and a matching timestamped README.
   After export preparation/confirmation, synchronize an already-saved plan and
   its README before writing the export. Unsaved plans can still export directly.
4. Update workflow docs, inspect scoped diffs and perform one lightweight check
   targeted at partial-to-full selection output consistency. No new test files.

Save must not change active sites or routing, and Export still preserves targets
when completing IMRO's 384 slots. Saved-plan XML describes current target wiring;
unselected NP slots remain skipped with unknown physical sites until acquisition
export. Prior output files remain snapshots until manually exported again.

User requested the label **Save & Update**. It is the existing-plan overwrite
action (Cmd+S on macOS), while Save as creates a separate named bundle.

Result (uncommitted): Save & Update now writes the existing path without another
dialog, with Save as for a new copy. Save refreshes plan/coordinate/XML/index/
README only; it no longer creates or deletes acquisition export files. README
records the current saved count and timestamp and identifies older exports as
separate snapshots. Manual IMRO Export refreshes IMRO, selection JSON, target CSV
and `<name>.README.txt` together, after synchronizing any already-saved plan.
Destination checks prevent an export from overwriting the current plan/reports.
Existing automatic exports remain intact until the user explicitly re-exports.

Reviewed scoped diffs against `/private/tmp/atlaxis-save-export.o3NIiC`. One
lightweight export-update check passed (exit 0):
`PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-save-export-pycache .venv/bin/python -`
The stdin check used the actual NP1000 catalog geometry and NeuroCarto routing,
exported 324 then 384 targets into the same OS temporary directory/name, imported
both selection JSONs, and asserted CSV counts, exact original site/channel maps,
README selected/filler counts, IMRO/JSON acquisition agreement and non-mutation
of source maps. The final README no longer contained the earlier 324 count.
Temporary output was cleaned by TemporaryDirectory. No test files or broad
checks were added/run. GUI Save/Save as interaction, full atlas-based bundle
saving and external acquisition-software import were not executed. Export and
plan replacements remain per-file; filesystem failures may interrupt a batch.

## Follow-up: include every acquisition channel in CSV

User requests all channels in CSV, including the slots filled for IMRO, and
confirmation that the exported IMRO can configure SpikeGLX/Open Ephys.

Steps:
1. Build IMRO-companion and standalone NP CSVs from the complete acquisition
   routing (384 channels), preserving exact site/hardware/shank correspondence.
   Add `is_target` (1 for a user-selected site, 0 for a filler); retain the existing
   companion filename so re-export updates it rather than leaving a stale copy.
2. Keep target JSON/GUI activity unchanged; update labels, confirmation and README
   to distinguish all recorded channels from the ROI target subset.
3. Inspect scoped diffs and run one lightweight check comparing CSV rows to the
   actual IMRO for a partial selection. Do not add tests or change routing rules.

Official references: https://billkarsh.github.io/SpikeGLX/help/imroTables/ and
https://open-ephys.github.io/gui-docs/User-Manual/Plugins/Neuropixels-PXI.html .
Software import instructions do not constitute live hardware verification.

Result (uncommitted): both NP CSV export paths now contain channels 0–383,
decoded from the completed IMRO itself, with site, shank, region and `is_target`.
The existing `.active_channels.csv` filename is retained. Target JSON/GUI activity
and all routing rules are unchanged. Export labels, counts and README explain
all acquisition rows versus selected targets.

Scoped diffs reviewed against `/private/tmp/atlaxis-all-channels.Do4KiW`.
One lightweight check passed (exit 0), invoked with
`PYTHONPATH=src PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-all-channel-pycache .venv/bin/python -`.
The stdin check used actual NP2013 geometry/routing with 324 selected sites,
verified all 384 CSV channel/site pairs against the emitted IMRO, checked every
shank and target flag (324 targets, 60 fillers), compared standalone/companion
CSV contents, restored the original target JSON and checked map non-mutation.
No test files, broad suites or hardware/software acquisition runs were added.
Live GUI and SpikeGLX/Open Ephys loading remain unverified.

## Follow-up: polygon ranges, balanced ROI activation, and Brain hierarchy

Goal: separate Rectangle/Polygon drawing, add Activate channels immediately left
of Reset all, and use the same Brain-only region hierarchy for masks and ROI
region selection. The user's corrected choice locks all existing active channels;
only remaining capacity is shared between registered, unassigned ROIs.

Steps:
1. Persist optional probe-plane polygon vertices alongside existing rectangle
   bounds. Add click vertices / double-click finish / Escape cancel interactions;
   keep ordinary probes free of selection controls and retain pan/zoom.
2. Share Brain subtree filtering and hierarchical region-tree construction.
   Exclude Waxholm Root siblings (spinal cord / inner ear); atlases without a
   named Brain node retain their native hierarchy. Filter initial masks too.
3. Add a batch activation action, registering valid drawn ranges first. Build
   independent per-ROI candidate maps with existing NeuroCarto density selection,
   then share free hardware channels using round-robin augmenting matching.
   Augmenting paths resolve channel conflicts without reducing another ROI's
   allocation. Exhausted ROIs yield remaining capacity to other ROIs. Preserve
   existing site/channel pairs and reference/gain settings, unique ROI ownership,
   and all per-row activation/removal/reset behavior.
4. Run allocation off-thread and reject stale results, including ROI edits.
   Report achieved per-ROI counts. Persist polygons in existing plan/selection
   JSON via optional dataclass fields, without changing geometry or routing IDs.
5. Review scoped diffs and run at most one lightweight changed-file check; no
   new tests or broad validation under the current repository instructions.

The allocation target is equal channel counts among new ROIs, subject to the
existing NeuroCarto density candidate maps and hardware conflicts. Matching is
max-min fair over those candidates, not a promise of 384 sites or global density
optimization over all electrodes. Overlap consumes one channel and has one ROI
owner. Existing/imported active sites are immutable and excluded from new quotas.
No atlas voxels, scientific coordinates, or saved rectangle semantics change.

Acceptance: both shape types survive saving/loading; polygon selection uses its
interior rather than its bounding box; parents include their actual descendants;
Brain-only masks exclude other root branches; allocations cannot duplicate a
channel, use sites outside the ROI/tissue, or change existing active assignments.
Empty/insufficient/overlapping/full-capacity cases must remain explicit.

Outcome (uncommitted): implemented both drawing modes and optional polygon
storage. Rectangle remains the default; Polygon uses odd-even interior selection,
click vertices, double-click or click the first vertex to finish, and Escape to
cancel. ROI changes/reset clear incomplete drawing. The batch button sits left
of Reset all, registers drawn ranges, and preserves existing active assignments.
Independent density candidates are matched across free channels; the status
reports each processed ROI's assigned count. Previous ROI removal ownership and
per-row activation remain intact. Background results compare the complete ROI
snapshot before applying.

Both dialogs use the same Brain-subtree tree builder and search behavior. ROI
selection includes descendants of the chosen parent. Initial/current masks also
exclude non-Brain branches; tissue eligibility is restricted to the same scope.
The raw atlas and brain-outline mesh are unchanged. Atlases lacking an explicit
Brain node keep their ontology. No plan or acquisition file was rewritten.

Reviewed scoped diffs, signal connections, routing construction, and persistence
paths. One lightweight syntax check passed (exit 0):
`PYTHONPYCACHEPREFIX="$roi_check_dir" .venv/bin/python -m py_compile src/probe_planner/atlas/regions.py src/probe_planner/probes/model.py src/probe_planner/probes/neuropixels.py src/probe_planner/rendering/probe_view.py src/probe_planner/ui/region_dialog.py src/probe_planner/ui/probe_plane.py src/probe_planner/ui/main_window.py`.
The unique `/tmp/atlaxis-roi-check.XXXXXX` cache directory was cleaned afterward.
No tests were added or run. Live drawing, save/load round trips and numerical
allocation were not executed; hardware/density limits can prevent equal counts.

Additional display correction: exclude Waxholm spinal cord (`SpC`) from the
brain outline as well as the already filtered region masks. The existing cache
key includes excluded region IDs, so the next atlas load builds a new outline.
Atlas annotations remain intact. Source/diff inspection only; rendering not run.

The follow-up screenshot still showed the sagittal grayscale texture extending
into the spinal cord: `section_rgba` used every nonzero annotation for alpha,
independently of the color-mask and outline filters. Added optional tissue
visibility to the shared texture function and passed the Brain subtree for both
orthogonal sections and the probe plane. This makes non-Brain labels transparent
even at zero mask opacity, without changing atlas arrays, contrast scaling,
sampling, or contact lookup. Source/call-site diffs reviewed. Syntax check passed
(exit 0): `PYTHONPYCACHEPREFIX="$slice_check_dir" .venv/bin/python -m py_compile
src/probe_planner/rendering/slice_view.py src/probe_planner/ui/probe_plane.py`.
The unique `/tmp/atlaxis-slice-check.XXXXXX` cache was cleaned. No live rendering
or image comparison was run; restarting the app rebuilds in-memory textures.

### Remaining spinal tail: preserve brain portions of shared labels

Read-only inspection of native Waxholm AP planes 850/900/950/1000 found the
remaining tail labels PVG (56) and CC (70), both classified under Brain. In planes
850/950/1000 their voxels lie entirely inside the filled SpC cross-section. At
750/800, PVG/CC have brain voxels but no surrounding SpC. Hiding these labels
globally would incorrectly remove the brain portions.

Implementation steps:
1. Derive sparse display-only exclusions from holes enclosed by the native SpC
   label in each AP cross-section (4-connected background fill, no dilation or
   coordinate cutoff). Keep original annotation and anatomical lookup unchanged.
2. Apply the same exclusions to region surfaces, the outer outline, orthogonal
   textures and oblique probe-plane textures; retain the original section labels
   separately from display visibility. Invalidate affected display-mesh caches.
3. Prepare/cache cross-section exclusions during existing background atlas mesh
   processing. Avoid a second full-volume annotation or mask allocation.
4. Review the changed paths and perform one narrow changed-code check using the
   observed posterior cross-sections and a brain cross-section, without a broad
   atlas/GUI validation or new test infrastructure.

Result (uncommitted): implemented sparse per-AP-plane exclusion indices for
non-SpC voxels enclosed by the native cord cross-section. They are prepared in
the existing background mesh pass and cached on the loaded AtlasModel. No extra
volume-sized array is allocated. Region surfaces containing these voxels are
contoured with the exclusions and cached separately; the outline cache moved to
shell-v3. Both section types carry a separate display mask; original labels,
sampling coordinates, contact lookup, and source TIFFs remain unchanged.

Scoped source/diff inspection completed. One focused changed-code check passed
(exit 0): `PYTHONPATH=src .venv/bin/python -B -`, reading the actual installed
Waxholm annotation/reference TIFFs read-only and invoking `section_at` and
`section_rgba` on AP slices 750, 850, 950 and 1000. At 750, all 1,080 original PVG
voxels remained visible. At 850/950/1000, SpC/PVG/CC visibility was zero and all
pixels in those cord-only sections were transparent. Source annotation equality
was checked after each section. No new test files, full-volume validation or GUI
rendering was run. Full 3D remeshing remains unexecuted in this check; it uses the
same exclusions and will rebuild its affected caches on the next atlas load.

### Ear-side nerve projection

Added Waxholm `7n-u` (facial nerve, unspecified; label 35) to display exclusions.
Its magenta color and native mesh AP extent (24,121.5–26,617.5 µm) identify the
ear-side projection. The separately annotated intracranial branches `asc7` and
`g7` remain available. A shared display-region scope now drives region-mask
availability and orthogonal/oblique textures, so Select all and same-atlas reload
cannot restore excluded peripheral nerves. Outline cache keys already include
excluded IDs and therefore rebuild for label 35. Raw annotations and channel
region lookup are unchanged.

Scoped diff/call-site inspection completed. One focused changed-code check
passed (exit 0): `MPLCONFIGDIR="$ear_check_dir/matplotlib" PYTHONPATH=src
.venv/bin/python -B -`. It read the actual Waxholm AP slice 650, passed it through
`section_at`/`section_rgba`, and confirmed all 653 label-35 voxels were transparent,
35 was excluded from surface/outline selection, 57/72 remained available, and
the source annotation was unchanged. The unique `/tmp/atlaxis-ear-check.XXXXXX`
directory was cleaned. No new tests or full GUI/3D rendering runs were added.

### ROI drawing and per-row controls (2026-09-21)

Goal: restore rectangle drawing, finish polygons at the double-click position,
and make each ROI's settings and channel assignment accessible in a compact table.
BrainGlobe's StructuresDict rejects a None lookup key: the default unrestricted
ROI currently interrupts row creation before drawing is enabled.

Steps:
1. Avoid the invalid lookup and keep table signal blocking scoped to its rebuild.
2. Store the drawing mode per ROI, retaining compatibility with existing polygon
   and rectangle plans; include the double-click location as the final vertex.
3. Bound the Region column and expose per-row activation. Preserve assigned
   site/channel pairs; batch activation shares remaining channels among unset
   ROIs only. The user confirmed per-row Activate buttons, without numeric quotas.
4. Inspect the scoped diff and run one focused changed-code check covering the
   real StructuresDict failure and ROI interaction; no broad suite or new tests.

Result (uncommitted): guarded the unset-region lookup and used QSignalBlocker
around table rebuilding. Each ROI now persists its drawing mode; older plans
infer it from their existing polygon or rectangle. Double-click includes the
clicked position as the final polygon vertex. The Region column is 120 px,
with compact per-row Shape, Density, Register, Activate and Remove controls.
Activate also registers a drawn draft. Batch activation ignores undrawn rows
and reuses the existing allocator that locks assigned site/channel pairs and
shares free channels among unassigned ROIs. No numeric quota or allocator
semantics change was introduced.

Scoped diff and captured widget image inspected. One focused check passed
(exit 0): `QT_QPA_PLATFORM=offscreen MPLCONFIGDIR="$roi_check_dir/matplotlib"
PYTHONPATH=src .venv/bin/python -B -`, using the installed Waxholm structures and
read-only TIFFs, catalog NP2 four-shank geometry, QTest input events and real
NeuroCarto allocation. It reproduced the original StructuresDict TypeError,
then checked rectangle drawing, the exact final polygon vertex, per-row modes
and JSON round-trip, individual Activate, and batch Activate with an empty row.
The original 24 site/channel pairs remained unchanged; two new ROIs received
180 channels each; the empty row received zero (384 total). Temporary files
under `/tmp/atlaxis-roi-check.LTfOhT` were cleaned. No tests were added and no
broad suite/build or manual macOS interaction was run.

### Multiple channel-selection regions per ROI (2026-09-21)

Goal: allow a single ROI to target a union such as CA1 + DG. A contact must
remain inside the drawn range and Brain scope, and its native label or an
ancestor must match at least one selected region. Parent selections include
their direct annotation and descendants; overlapping selections never duplicate
contacts. Existing assignments, geometry, densities and allocation stay unchanged.

Steps:
1. Add optional region_ids to SelectionROI, retaining legacy region_id lookup
   for old plans. An explicit empty list matches nothing; unrestricted Brain
   remains the default. Preserve the settings in existing dataclass serialization.
2. Add independent checkboxes to the existing hierarchical region picker, with
   search, clear and explicit All Brain controls. A cleared picker cannot Apply
   an accidental unrestricted selection; Cancel leaves the ROI unchanged.
3. Display combined acronyms with full names in the tooltip, and register the
   union of the selected regions/subtrees inside each drawn ROI.
4. Review the scoped diff and run one focused real-atlas selection/persistence
   check; no new tests or broad validation.

Result (uncommitted): implemented independent multi-region checkboxes, combined
acronyms/full-name tooltips and union filtering at registration. Search preserves
checked regions outside the current results. Apply is disabled when no regions
are checked; All Brain is an explicit action. The optional region_ids list takes
precedence when present; otherwise legacy region_id retains its original meaning.
Existing plan/selection JSON serialization preserves the new field automatically.
No allocator, assignment, atlas annotation or coordinate changes were needed.

Scoped diff reviewed. One focused check passed (exit 0):
`QT_QPA_PLATFORM=offscreen MPLCONFIGDIR="$region_check_dir/matplotlib"
PYTHONPATH=src .venv/bin/python -B -`. With actual Waxholm StructuresDict/native
annotation and NP2 four-shank geometry, Qt input selected CA1 and DG across search
filters. Registration retained exactly their 440 physical sites in the drawn
span (174 CA1 + 266 DG), excluding other labels. The same flow checked cleared
Apply/Cancel, overlapping parent/child selection without duplicate sites, empty
filter rejection, legacy single-region loading, and plan/NP selection JSON
round-trips. The temporary cache/plan directories were cleaned. No new tests,
broad suite, full application launch or manual macOS interaction was run.
