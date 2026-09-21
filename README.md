# Atlaxis · Probe Planner

A desktop pilot for generic electrophysiology probe planning. One 3D workspace
contains coronal and sagittal atlas planes, brain-surface boundaries, a brain
silhouette and solid probe bodies. Multiple independent probes and shanks can
coexist in one plan.

## Run

```sh
uv sync --locked
uv run python -m probe_planner
```

Python 3.11 is selected automatically. This workspace also has a local uv:

```sh
.tools/bin/uv run python -m probe_planner
```

macOS Apple Silicon and Windows x64 are the intended platforms. Configured CI
checks installation and module imports; interactive Windows validation remains
outstanding. See `plan_and_log/2026-09-19-pilot.md` for actual checks.

## Workflow

1. **Load atlas** opens a searchable atlas table, initially choosing
   `whs_sd_rat_39um` (or the currently loaded atlas). Select a row, then click
   **Load** or double-click the row. **Cancel** leaves the current plan intact.
   The list includes BrainGlobe's cached/custom catalogue and downloaded atlases,
   then refreshes the official catalogue asynchronously. If refresh fails, local
   choices remain available. The Data column distinguishes downloaded atlases
   from those requiring a download. Search names such as `rat`, `mouse` or `Allen`.
   First use downloads the atlas; later loads use BrainGlobe's cache. The main
   panel displays the name only after loading succeeds.
   Only the existing WHS rat v1.2 has an automatic Bregma preset;
   other atlases require a verified Bregma origin before placing probes.
   Reference and annotation TIFFs are
   memory-mapped; native region surfaces load in a background worker and only
   the requested 2D sections are textured.
   The app starts with no probes. An atlas alone shows its central sections.
2. Click **+ Probe** below Atlas and choose a JSON or CellExplorer
   `chanCoords.channelInfo.mat` file. A separate window shows the body, sites
   and import details. **Import** adds the probe; **Cancel** leaves the plan
   untouched. The chooser opens `probes/`, containing 171 Cambridge NeuroTech
   models plus the NeuroNexus and Neuropixels layouts. The preview includes a
   zoom-aware scale bar; source and dimensional limitations are recorded in
   [the library documentation](probes/README.md).
3. Each imported probe gets a **number · probe name** tab. Click its **×** to
   remove it. Click **☆** to register the design in **Favorite probes**; a yellow
   **★** means it is saved. Click again to remove the favorite. The menu opens
   the same Import/Cancel preview, and favorites persist between app sessions.
   Favorites store the design and chosen headstage, not coordinates or NP ROIs.
   Library favorites use the current library file; custom designs are stored
   as independent templates in the application's user settings.
   For supported passive Cambridge probes, choose the connected **Headstage**
   in the preview or the probe tab. **Unassigned** keeps physical Site IDs.
   The preview identifies unsupported wiring and always reminds you to check
   Channel ID against physical Site using the documents for your actual probe,
   headstage, adapter and recording setup. Registered profiles link their sources.
   Save & Update preserves the choice and updates XML/channel-index routing.
   Selecting a tab selects that probe's coordinates and the matching
   summary tab on the right. Coordinate controls appear inside the selected
   tab only after import. **Reference shank** sets the coordinate reference and
   centers both sections on its physical tip. Shank 0 is the default
   when present; otherwise the lowest existing ID is used. Imported IDs remain.
   Changing reference preserves the physical probe placement and updates the
   displayed entry coordinates. Depth still advances the selected shank tip.
4. Change AP/ML, **AP tilt**, **ML tilt**, roll and insertion depth below the tabs.
   AP/ML locate the insertion entry relative to Bregma. **Insertion depth** is
   distance advanced along the probe axis. **DV (tip)** is the vertical
   depth of the reference-shank tip below the brain surface at the entry AP/ML;
   it updates with depth and tilt. New probes start at surface DV 0. For a surface
   entry, DV = insertion depth × cos(AP tilt) × cos(ML tilt): 2 mm of travel
   with one tilt at 60° and the other at 0° gives 1 mm of DV. Positive AP tilt
   leans anterior, negative posterior; positive ML tilt leans right, negative
   left. Moving AP/ML retains the entry's surface-relative offset.
   Editing DV adjusts insertion depth along the same axis while keeping the
   entry fixed. For a surface entry, entering DV 0 returns insertion depth to 0.
   A horizontal probe cannot reach a different DV by insertion; targets needing
   negative travel or exceeding the insertion limit are rejected without moving
   the probe. Saved entry offsets are retained, not silently reset to the surface.
   Controls show two decimals; unchanged values and exports retain full precision.
   Main views show probes once an atlas and calibration are available.
5. Check **Brain outline**, **3D regions**, **Coronal** and **Sagittal** to toggle individual layers
   in the same 3D scene. The two section planes intersect inside the brain and
   rotate together with the region surfaces and probes. Navigation sensitivity
   is fixed at 100%. Left-drag rotates; right-drag or Mac
   two-finger click-drag pans (with secondary click enabled in macOS).
   Two-finger swipe, mouse wheel and trackpad pinch zoom around the cursor.
   Double-click restores the default oblique view and overview. Gold contacts identify
   the selected shank. Contact markers are drawn over probe bodies and
   atlas surfaces; their centers retain the actual projected contact
   positions. Section coordinates/orientation are in the viewer tooltip;
   no labels are embedded in the scene. Hiding 3D regions leaves the planes
   and probes visible; hiding all four atlas layers still leaves placed probes.
   Brain outline is the independent whole-brain surface, white at fixed 20%
   opacity, initially visible. Region selection and Mask opacity do not affect it.
   Its existing display-only 50k-face cache is prepared in the background.
   For Waxholm, this outline omits the protruding trigeminal (`5n`) and optic
   (`2n`) nerves. Its display-only mask closes gaps with a two-voxel morphological
   radius (78 µm at 39 µm resolution) and fills enclosed voids, reducing internal
   surfaces visible through the unlit white envelope. Small exterior clefts can
   be filled within that radius. Contouring uses native resolution before
   display-only decimation and caching; region geometry, the original annotation
   and brain-surface DV stay intact.
   An orientation cube follows the camera.
   Click a cube face to switch to Front, Back, Right, Left, Top or Bottom.
   These views use parallel projection; Front means anterior and Top means
   dorsal. Cube edges and corners select intermediate views. Left-drag rotates
   into an oblique view.
   Region surfaces use atlas colors; shared 2D/3D mask opacity starts at 25%.
   Two sliders below the viewer move Coronal and Sagittal sections independently.
   Moving one pins that plane at its native atlas index, including during probe
   movement; the other plane can continue following the tip. **Follow tip**
   restores both planes to the selected tip. Selecting another probe/shank or
   atlas also restores automatic following. In the viewer and its section
   controls, **Left/Right** moves Sagittal left/right and **Up/Down** moves Coronal
   anterior/posterior, one native voxel per press. Click the viewer to focus it;
   arrow keys in coordinate input fields retain their usual editing behavior.
6. The right-hand tables contain only **Channel ID**, **Shank**, and **Region**
   (acronym, or Outside/Unannotated). Without a wiring map, the first column is
   **Site ID**. With a map, **Channel ID** contains zero-based acquisition IDs;
   missing mappings show **—**, with the physical site ID available on hover.
   **Save & Update** preserves all independent probes, poses and mappings. **Open
   plan** accepts version 1 and 2 projects. The right-hand **Export** saves the
   selected probe's channels. XML loading has been removed from the GUI;
   the parser and existing saved XML mappings remain supported.

The **Region mask** button opens a searchable hierarchy. Select a group such as
cerebral cortex or hippocampal formation to select all its subregions; expand
it to toggle individual regions. **Select all** and **Select none** also work
across collapsed or filtered branches. **Apply** updates the 3D surfaces and
2D colored masks together; **Cancel** keeps the previous selection. All regions
are initially selected when changing atlas except Waxholm's trigeminal and optic
nerves (`5n`, `2n`), which can be enabled here. This restores their colored surfaces, not their
outline. **Mask opacity** adjusts both slice
color intensity and 3D surface opacity. Deselecting a region
removes its 3D surface and slice color; the grayscale reference remains visible.
Selections are session display preferences, not stored in project files, and do
not change channel assignments or probe geometry.

Region geometry is prepared in the background and reused when toggling regions.
Supplied region meshes retain their original resolution and physical coordinates.
Aggregate parent envelopes are excluded to avoid covering deselected children.
If a parent has its own labeled voxels, or a region mesh is missing, its exact
label is contoured at native voxel resolution using a padded 0.5 binary
isosurface (half-voxel boundaries). The hierarchy exposes a parent's own voxels
as **Direct annotation** when they coexist with annotated children. No anatomy
is inferred, decimated or resampled for these surfaces; atlas annotation remains
the source of truth for channel assignments.

The packaged Waxholm atlas contains CA1, CA2, CA3 and DG as regions, but **no
separate hippocampal pyramidal-layer mask**. Those region masks must not be
interpreted as pyramidal cell layers. Some other layers, such as piriform cortex
layers 1–3, are available. Missing layers are never inferred from image intensity.

The [BrainGlobe catalogue](https://brainglobe.info/documentation/brainglobe-atlasapi/usage/atlas-details.html)
lists Waxholm at 39 µm, `swc_female_rat_50um` (native female Lister Hooded space)
and `whs_sd_swc_female_rat_39um` (SWC template resampled into Waxholm space, not
native 39 µm acquisition). Mouse choices include Allen CCF, Kim/Unified and
Perens stereotaxic MRI. The same mask controls operate on each atlas's annotation
labels and hierarchy; region names, layer coverage and geometry differ. Atlas
listing/selection is supported, but these alternative datasets have not all been
loaded and validated in Atlaxis. A separate
[Duke Wistar multicontrast atlas](https://www.nitrc.org/projects/rat_dmri_atlas/)
offers a 25 µm single-specimen volume. It is not integrated here: its reference
space, calibration and annotation availability need a dedicated import. Finer
voxels do not by themselves provide a hippocampal pyramidal-layer segmentation.

Known issue, deferred for a later fix: deselecting all Region mask entries can
leave visible masks. This is separate from the independently enabled Brain outline.

In the 3D tab, probe bodies and contacts remain at their true 3D coordinates,
without projected copies on the planes. Other probes are dimmed. Slice textures retain their native
pixel grid and atlas-axis placement in µm. Their background is transparent and
their opacity is 90%, allowing some visibility through intersecting planes.
By default both planes follow the selected shank's physical tip, including
insertion depth, rounded down to the displayed native slice index. Manual
slider positions are independent display settings, not changes to probe pose
or region assignment, and are not stored in plans. They remain orthogonal atlas sections at angled
probe poses, rather than becoming oblique sections aligned with the shaft.
If the selected shank tip is outside the atlas, the nearest valid section is
identified in the section tooltip. Anatomical assignment still reports the actual
out-of-bounds position; it is never clipped into the atlas.

## Manufacturer and custom probe bodies

`probes/` contains the requested manufacturer layouts, replacing the old
pilot probes. Their physical sites and shaft bodies include nonuniform shanks,
remote sites and E1 front/back faces. Some dimensions remain provisional and
are flagged in the files and library documentation. See the library README for exact
variants, sources and limitations. Neuropixels includes all 960/1280/5120 sites;
its active channels can be generated with NeuroCarto or imported from IMRO.
Cambridge includes official acquisition maps for 35 built-in Intan models,
selectable Mini-Amp-64 V1 routing for 18 ASSY-236 entries, and standard Intan RHD
profiles for 61 current ASSY-1/37/77/79/116/156 models (114 entries total).
The 57 entries without a registered profile retain physical Site IDs and show
an import notice. Other headstages/adapters are not implied by these profiles.
RHD 16ch uses native inputs 8-23, retaining the 32-input chip namespace in exports.
Cambridge's 171 ProbeInterface entries are pre-generated offline JSONs. The app
does not download them or import ProbeInterface. See the
[Cambridge library and regeneration instructions](probes/Cambridge%20NeuroTech/README.md).

## Probe plane and channel selection

The central **Probe plane** tab samples an oblique atlas section following the
selected probe's XY plane, including tilt and roll, at the reference shank's
median contact-face Z. Pixel pitch is the smallest native atlas voxel size;
annotation uses exact voxel containment, while MRI intensity is linearly
interpolated for display. Sampling runs in bounded chunks in a background worker
only when the tab is used. All shanks are projected into this view. Off-plane
distances are disclosed; region assignments always use the actual 3D site positions.
The sampled plane includes a 5 mm margin on each side of the contacts and tip.

Each right-hand probe tab contains **Geometry** and **Channel map**. Geometry shows
the physical shafts and sites: active markers are small magenta dots at 50% opacity; the
reference shank has a thin cyan outline. Scroll to zoom at the cursor, drag to
pan, and double-click to fit. Channel numbers and region acronyms appear where
they fit; zoom in or hover to read a specific site's full details. Channel map
retains the table with an **Active only** filter (on by default for Neuropixels).
Non-Neuropixels probes treat every physical contact as active, including contacts
without a hardware channel assignment. These retain their Site IDs; no channel
numbers are inferred. This activity rule also applies to the 3D view and CSV.

For catalog NP1000, NP2003 and NP2013:

1. Position the probe, then click **Select…** in its right-hand tab.
2. Drag directly on the plane to draw the first ROI. Choose CA1 (or another
   region; parents include children) and a density (Full/Half/Quarter/Low) in its
   table row. A new click/drag replaces only the selected unregistered range.
   Right-drag pans; scroll zooms at the cursor; double-click fits the plane.
3. Click **Register** to freeze that row's sites, region and density, then
   **Activate Channels** on that row. NeuroCarto 0.2.2's default stochastic
   selector assigns free hardware channels. Prior sites and channel IDs stay
   locked with `CATE_SET`; only new sites inside annotated tissue are candidates.
   Hardware conflicts can reduce the count. **Add ROI** appends another row with
   its own density. Each successfully assigned ROI activates once so repeated
   clicks cannot increase its density. Remove/recreate a row to change it.
4. **Remove** deletes that row and only the channels it added. Channels owned by
   other ROIs or imported without ROI ownership remain assigned. **Reset all**
   below the table clears the current NP probe's ROIs and map, fits the plane and
   Geometry, and restores oblique 3D and tip-following sections. Probe coordinates,
   other probes and masks remain unchanged. The central table's top-left count
   shows mapped channels out of 384. Ordinary probes have no selection controls.
5. **Export** works for partial selections too. Choose **IMRO + selection** for a
   384-channel recording map and a companion `.selection.json` containing the
   original target channel IDs, site assignments, ROI bounds, densities and
   registration/ownership. An all-channel `.active_channels.csv` and an export-specific
   `.README.txt` are also written. All four files are refreshed together from the current selection.
   Unassigned acquisition slots are completed in shank/row/column order;
   selected assignments never change. A dialog reports the extra acquisition
   channels, which may be outside the ROI or Excluded. These additional sites will
   be recorded, but are not added to the GUI target selection. Use `selected_channels`
   in the companion JSON to identify the target subset. CSV includes all 384
   acquisition channels; `is_target=1` marks ROI targets and `is_target=0` marks
   added filler sites. **Selection JSON** exports the target selection only.
   **All channels CSV** exports the same complete routing as IMRO without writing
   an IMRO file. Each export has its own updated README. Export also saves the current state of an
   already-saved plan and updates its coordinate/XML/index/README files. An
   unsaved plan can export without creating a plan bundle.
6. **Import** accepts matching-type IMRO or selection JSON. Import the companion
   JSON to restore the original partial selection and continue adding ROIs;
   importing the IMRO alone loads all 384 acquisition assignments as active.
   Channel IDs are zero-based hardware channels. Supported IMRO imports use one
   reference setting and one bank per channel; inconsistent fields are rejected.

If the atlas does not label dorsal/ventral CA1 separately, these are user-selected
spatial ranges within CA1, not newly inferred anatomical labels. Density choices
and the resulting active-site map, including ROI rows, are saved in plans.
Moving the probe updates region labels but retains the selected physical sites.
Activate Channels evaluates tissue eligibility at the current pose and never
removes old sites, even if they have moved outside the brain. Registered region
filters retain their physical sites when the probe moves. Reset all starts a new selection.
New selections can choose different equivalent sites because the selector is
stochastic. Existing NP2 tip-offset uncertainty is unchanged.

NeuroCarto's BSD-3-Clause notice is retained in
[third_party/NeuroCarto-LICENSE.txt](third_party/NeuroCarto-LICENSE.txt).

### Planning bundles

The first **Save & Update** dialog starts in `planning/`. Choosing `experiment.json`
creates `planning/experiment/plan.json` and planning reports in that folder.
After editing, **Save & Update** (Cmd+S on macOS) overwrites the same plan and
updates the reports without another filename dialog. **Save as…** creates a
separate named copy. **Open plan** also starts in `planning/`; existing
standalone plan JSONs remain readable. Installed apps use `~/Documents/Atlaxis/planning/`.

- `planned_coordinates.csv`: each shank's entry/tip coordinates (mm), AP/ML tilt
  and roll (degrees), insertion travel, and selected reference-shank flag. AP/ML
  and absolute DV are relative to Bregma; a separate tip DV column is relative
  to the brain surface at that shank's entry AP/ML, matching the GUI definition.
- `probes.xml`: one NeuroScope `anatomicalDescription/channelGroups` template,
  concatenating probe channels in plan order. IDs are zero-based. Known wiring
  supplies shank groups; unknown wiring stays in a probe-level group. Physical
  contacts are never assigned guessed hardware channels. `channel_index.csv`
  explicitly links global XML IDs to probe-local hardware IDs and known sites.
- `README.txt` reports the saved plan's current target counts and save time.
  NP inactive slots remain skipped in XML; Save does not fill their physical
  routing or create any IMRO/selection/active-channel export files.

Use the right-hand **Export** explicitly for acquisition files. Export starts
in the saved plan's folder and uses the current selection, including channels
added since the last save. Choosing `probe_1.imro` writes that IMRO together with
`probe_1.selection.json`, `probe_1.active_channels.csv` and `probe_1.README.txt`.
The CSV uses zero-based probe-local hardware IDs; `channel_index.csv` supplies
the combined XML offset. The export README reports its actual target/filler
counts and timestamp. Both IMRO and CSV include all 384 channels. CSV's `is_target`
column separates user-selected targets (1) from filler sites (0); JSON and GUI
retain only the user's target selection. Re-export to the same filename after edits to
refresh all companions. Files exported under other names remain snapshots.

The XML describes channel groups, **not complete recording metadata**. Add/merge
the recording's sampling rate, bit depth and gain before use in NeuroScope.
Offsets assume concatenated neural channels; auxiliary/sync channels are not
included. NeuroScope's [parameter workflow](https://neuroscope.sourceforge.net/UserManual/using-neuroscope.html)
requires the actual acquisition settings. `README.txt` in each bundle records
these conventions. Save leaves previous exports, including older automatically
generated IMRO files, untouched; their export-specific README describes their
snapshot, not necessarily the latest saved plan.

Generic JSON accepts a `geometry.bodies` array with `outline_um` (ordered local
xyz polygon vertices), `thickness_um` (extruded along local z), and `shank_id`.
A null shank ID denotes a common base/connector. Bodies and metadata are saved
with the project. Missing body data produces explicitly schematic 5 mm shafts,
extended if needed to cover the contact span. This is only a visualization:
contact positions and channel mappings remain untouched. The import dialog previews the local body before confirmation. Unassigned
channels do not hide the body or sites once placed in an atlas.

## Coordinates and calibration

Internal distances are µm. Stereotaxic controls use mm: AP anterior+, ML right+,
DV ventral+. Atlas axes follow BrainGlobe annotation array order. Core transforms
live in `atlas/coordinates.py`; section extraction in `atlas/sections.py`.

The stored canonical AP/ML/DV locate an entry/reference point relative to Bregma.
The GUI shows entry AP/ML relative to Bregma and the current physical tip's DV
relative to the brain surface at that entry location. DV and insertion depth
are linked: editing either updates the other while retaining the entry and tilt.
Depth advances the physical tip along the insertion direction from that entry.
Stored elevation is tilt from ventral (0° means down), azimuth 0° tilts anterior
and 90° right, and roll is right-hand rotation about the insertion direction.
The GUI instead uses direct AP/ML tilts: its world rotation is
`Ry(AP_tilt) Rx(-ML_tilt) Rz(roll)` before the zero-angle probe basis. AP tilt
is the sagittal projection angle; ML tilt is the angle out of that plane.
The direction is `(sin(AP)*cos(ML), sin(ML), cos(AP)*cos(ML))`.
Conversion to/from saved `Rz(azimuth) Ry(elevation) Rz(roll)` includes roll to
preserve the entire orientation, including the multishank array. Euler angles
are nonunique at singular orientations; displaying them never rewrites a saved
pose. At zero angles, local x is
right, y toward the base/dorsal, and z posterior. `y_to_base=-1` reverses local
y and z together. Imported local coordinates are never overwritten.

The GUI's entry belongs to the selected reference shank. Its local reference
`q` is the distal center of the supplied shank outline; for geometry-only files,
it is the median contact x/z at the explicitly declared tip-y plane (the same
convention as the schematic shaft). Electrode endpoints are never substituted
for physical tips. The canonical saved pose retains the original probe origin
`t`: `entry_reference = entry_saved + R * (q - t) / 1000`, in mm. Edits invert this
relation; angle edits hold the selected shank entry fixed. Switching reference
only changes the displayed coordinates and slice center, preserving all physical
contact positions and full-precision saved pose values. The equations below
describe that unchanged canonical transform. GUI DV is
`entry_reference.DV + depth * cos(elevation) - surface_DV(entry_AP, entry_ML)`.
The entry surface is a fixed zero while advancing along an angled trajectory;
it is not re-sampled at the moving tip's AP/ML. New probes use surface entry DV 0;
existing plans retain their physical placement and saved entry offsets.

The surface is the most dorsal nonzero annotation voxel-cell boundary in the
native DV column at AP/ML, regardless of region selection. It uses the same
floor-index voxel cells as region lookup/section textures, without smoothing or
downsampling. Its resolution is limited to the atlas voxels (39 µm for Waxholm);
centered contour meshes can differ by half a voxel. Empty/outside columns show
**No surface** for the derived DV. AP/ML can still be moved; entering a valid
column from an undefined one starts at surface DV 0. There is no nearest-tissue
substitution. This is the atlas's annotated boundary, not an animal registration.

```text
direction = (sin(elevation) cos(azimuth), sin(elevation) sin(azimuth), cos(elevation))
tip_stereo = entry + depth * direction
contact_stereo = tip_stereo + R * (contact_local - tip_local)
contact_atlas = bregma_atlas + A * contact_stereo
```

`R` includes orientation and the local shaft direction; `A` is the atlas signed
axis permutation. Voxel assignment uses floor(physical / resolution), only
within `[0, shape)`. Region -1 is outside the volume; 0 is unannotated.

Waxholm BrainGlobe v1.2 loads a Bregma origin automatically from the published
native voxel `(246, 653, 440)`, transformed through its recorded
`trasform_to_bg` metadata at packaged 39 µm resolution, yielding atlas
`(14469, 2808, 10374)` µm. Source: [WHS coordinate table](https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf).
**Bregma settings** is an advanced override for atlas registration and the saved
canonical coordinate origin; the displayed DV zero is the local brain surface. Normally
the automatic preset needs no editing. Saved custom calibration wins over defaults.
Other atlas versions/families without a verified preset require a supplied
landmark. This sets the origin in atlas-aligned axes. The published WHS 4°
flat-skull correction and animal-specific registration are not implemented.

## Input contracts and limits

- JSON: files in `probes/` demonstrate sites, body outlines and a separate
  contact-to-device-channel map. Units must be `um`; contact IDs are unique
  strings; shank IDs are nonnegative integers. Tip and shaft direction are explicit.
- MAT: requires `chanCoords.x`, `y`, and explicit one-based `channel` IDs; supports
  `z` and `shank`. Missing z means planar and missing shank means one shank.
  Physical contact IDs are generated independently. MATLAB v7.3 and MAT metadata
  round trips/export remain unsupported; use MATLAB `-v7`.
- NeuroSuite XML: uses zero-based acquisition IDs, preserves anatomical group
  and channel ordering and skipped channels, and validates mapped contacts.
  XML groups alone cannot establish contact-to-channel associations; these must
  be supplied by the geometry import's independent channel map. Duplicate
  channel assignments are unsupported. The imported XML is embedded in projects.
- No fixed vendor catalogue is embedded in widgets. The library consists of
  data files; arbitrary JSON/MAT probes remain supported.

Reference images and label volumes retain full native resolution (39 µm for the
default Waxholm atlas); smoothing improves display scaling without inventing
anatomical detail. Slice contrast is scaled for display and boundaries come
from annotation labels. The 3D silhouette keeps its display-only 50,000-triangle
approximation cached under the
atlas folder's `probe_planner_cache`; it does not participate in region lookup.

Later work includes measured manufacturer body outlines/channel routing, slice
intersection, complete shaft traversal, structure browsing, MAT/XML export,
and installers. No implantation accuracy is claimed. Known-landmark and lab-file
validation remain necessary before relying on planning coordinates.
