# Skull and drive placement: feasibility investigation

Date: 2026-09-26. Branch: `feature/skull-drive-planning`, created from `main`.
Status: skull/craniotomy and local CT caching added; craniotomy editor revised and
probe-attached drive travel added (2026-10-02). Application GUI behavior remains
unverified. Work is uncommitted; unresolved drive dimensions are omitted explicitly.

## Goal and scope

Investigate adding a skull alongside the 3D brain, choosing a probe's drive and
attachment location, and arranging multiple drives. Requested models: Cambridge
NeuroTech nano-Drive and pico-Drive, plus 3Dneuro regular and Neuropixels metal drives.
Both rat and mouse are considered; the intended species and exact NP drive variant
remain open. R2drive S/L are the provisional interpretation, with R2np/R2rail noted
separately. These are not interchangeable hardware definitions.

Investigation steps:
1. Inspect rendering, coordinates, probe representation, and project persistence.
2. Locate manufacturer specifications and actual skull/CAD file listings.
3. Separate data availability from registration, mechanical accuracy, and reuse rights.
4. Record a feasible implementation sequence and unresolved prerequisites.

## Conclusion

The existing PyVista/VTK architecture can support skull and drive visualization and
manual placement. Public rat/mouse skull STL files and Buzsaki metal-drive STEP
components exist. This does **not** establish that all four requested models are
ready for accurate placement: Cambridge CAD was not found, skull-to-atlas registration
is not supplied with the candidate STLs, and the public metal-drive revision has
not been matched to current commercial hardware. Redistribution permissions also
need clarification before assets can ship with Atlaxis.

## Drive data

| Requested model | Confirmed information | Shape availability and remaining work |
| --- | --- | --- |
| Cambridge nano-Drive | Official July 2025 catalog, p. 13: 2 x 5 x 11 mm; 7.5 mm travel; 250 um/turn; 0.26 g. | No manufacturer STEP/STL located in the inspected sources. Obtain CAD or dimensioned drawings with probe attachment datum and carriage positions. |
| Cambridge pico-Drive | Same catalog: 2 x 5 x 7 mm; 4 mm travel; 250 um/turn; 0.18 g. | Same CAD gap. Catalog marks pico-Drive as special-request; current supplied revision needs confirmation. |
| 3Dneuro regular metal drive, provisionally R2drive S | Manufacturer lists base 3.3 x 4.45 mm, regular arm 3.6 mm wide x 8.35 mm high, approximately 7 mm travel and 282 um/turn. | Buzsaki v10 body/base/regular-arm STEP files are publicly retrievable. Their exact correspondence to the current commercial S model is unverified. |
| 3Dneuro NP metal drive, provisionally R2drive L | Manufacturer lists an NP arm 5 mm wide x 10 mm high, 7 mm travel and 282 um/turn. | Buzsaki v10 includes a distinct NP1.0-arm STEP file. Confirm hardware revision and the actual probe assembly before using it as the L model. |

Sources: [Cambridge catalog](https://www.cambridgeneurotech.com/assets/files/Cambridge-NeuroTech-Product-Catalog.pdf),
[Cambridge drive page, indexed manufacturer subdomain](https://mail.cambridgeneurotech.com/nanodrives),
[R2drive S](https://3dneuro.com/products/r2drive),
[R2drive L](https://3dneuro.com/products/r2drive-l).
The catalog's indexed text was accessible; direct PDF opening exceeded the web
tool's size limit. The main Cambridge drive page returned a verification challenge.
Failure to find public CAD is not proof that the manufacturer cannot supply it.

The following actual STEP files were retrieved as text at Buzsaki repository commit
`ba4f327a46518d0353838d9f9539b0c2418effd6`. Each contains a STEP header, solid B-rep
entities, and millimeter unit declarations. CAD import, assembly, tessellation,
and dimensions were not executed or measured.

- [drive_v10.step](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/v10/step_files/drive_v10.step)
- [base_v10_aluminum.step](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/v10/step_files/base_v10_aluminum.step)
- [arm_v10_aluminum_64ch.step](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/v10/step_files/arm_v10_aluminum_64ch.step)
- [arm_v10_aluminum_NP1.0.step](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/v10/step_files/arm_v10_aluminum_NP1.0.step)

The [v10 README](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Microdrives/Metal_recoverable/README.md)
describes a 3.6 x 4.7 mm shell base, 15 mm height, and 7 mm travel, and explicitly
says v10 is not backward compatible with prior revisions. These dimensions differ
from current product specifications; do not combine them into one authoritative
model. The L product page also labels 5 x 10 mm as both an arm size and an
arm-inclusive footprint; use the explicitly stated width/height as arm dimensions,
not a verified horizontal clearance envelope. Screws and assembled offsets are
additional geometry to resolve, not supplied by those four part files alone.

If the intended NP drive is the NP2.0 dovetail version, the manufacturer's
[R2np repository](https://github.com/3Dneuro/R2np) lists `R2np.step`, `R2np.stl`, and
`R2np.pdf`. Its README points to Buzsaki files for the interfacing base and holders
and labels the repository work in progress. This is a separate candidate for the
[R2rail product](https://3dneuro.com/products), not the NP1.0 arm. No explicit license
was visible in the inspected R2np root listing/README.

A [third-party nano-Drive housing project](https://www.cadcrowd.com/3d-models/implantable-brain-probe-housing)
also advertises an assembly STEP. Its listing establishes housing CAD availability,
not manufacturer-accurate nano-Drive geometry; component contents and rights were
not verified and it is not a substitute for Cambridge CAD.

## Skull data and alignment

The Buzsaki repository tree at the commit above confirms:

| Asset | Size | Evidence and limitation |
| --- | --- | --- |
| [RatSkull.stl](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Rodent_models/RatSkull.stl) | 5,117,184 bytes | Documentation credits Mieke Roth. No WHS registration or anatomical calibration found in the accompanying documentation. |
| [MouseSkull.stl](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/Rodent_models/MouseSkull.stl) | 19,602,084 bytes | No Allen CCF registration, specimen metadata, or explicit asset license found in the accompanying documentation. |

The [source documentation](https://github.com/buzsakilab/3d_print_designs/blob/ba4f327a46518d0353838d9f9539b0c2418effd6/docs/rodent_models/rodent-models.md)
identifies these as third-party models. Binary mesh contents, watertightness, scale,
landmarks, and biological accuracy were not validated. Treat them as candidate
reference geometry, not atlas-native skulls. Units and orientation must be explicit
on import; an STL filename alone does not establish them.

A usable overlay needs Bregma, Lambda, and a third non-collinear landmark or equivalent
midline/plane constraints, plus specimen scale and a documented transform to the
selected atlas. Two landmarks alone leave rotation around their connecting line
underdetermined. Size adjustments must be recorded as an approximation. A visually
plausible fit cannot establish the skull surface's physical height or mounting accuracy.

Additional alignment leads, not validated ready-to-use assets:
- Mouse: [Gubra's multimodal atlas repository](https://github.com/Gubra-ApS/Multi-modal-mouse-brain-atlas)
  and [its publication](https://link.springer.com/article/10.1007/s12021-023-09623-9)
  describe a skull-derived stereotaxic framework. Exact reusable skull volumes,
  transformations, and data-specific permissions still require examination.
- Rat: a [WHS project forum report](https://www.nitrc.org/forum/forum.php?forum_id=9174&thread_id=11015)
  describes landmark-based registration of DigiMorph rat CT to WHS. It is a lead,
  not a verified transform for `RatSkull.stl` or Atlaxis's packaged WHS version.

## Asset reuse conditions

The [older Buzsaki design website](https://buzsakilab.github.io/3d_print_designs/microdrives/metal-microdrive/)
states GPLv3, whereas the current metal-drive directory README grants internal
noncommercial research/evaluation use and states no rights to redistribute or
modify. This is a concrete discrepancy: do not assume the downloadable v10 files
can be converted and bundled under Atlaxis's GPL license. Obtain clarification
for the exact files/revision, including derived meshes. Separately confirm the
third-party skull and Cambridge asset terms. A local-import feature does not itself
resolve an asset's usage or conversion permissions. No vendor contact was sent.

## Fit with existing code

| Existing component | Reusable behavior and required addition |
| --- | --- |
| `src/probe_planner/rendering/scene.py` | Already reads meshes, creates translucent actors, and applies per-probe `user_matrix` transforms. Add independent skull, fixed-drive, and moving-carriage actors. |
| `src/probe_planner/atlas/brainglobe_backend.py` | Loads brain annotations/reference/root mesh; exposes no separate skull asset or registration. |
| `src/probe_planner/atlas/coordinates.py` | Centralizes atlas transforms and mm/um conversion. Internal stereotaxic axes are AP anterior+, ML right+, DV ventral+. Allen's nominal 5-degree correction is not individual skull registration; WHS defaults set Bregma without skull-level rotation. Preserve these existing semantics. |
| `src/probe_planner/implant/instance.py`, `implant/pose.py` | Supports multiple probes with entry-reference position, angles, and axial depth. Add a drive association and physical attachment offset without changing existing standalone probe behavior. |
| `src/probe_planner/probes/model.py` | Probe bodies are extruded outlines; geometry-only imports may use schematic bodies. Electrode layouts do not establish a measured mechanical mounting datum. |
| `src/probe_planner/project/save_load.py`, `project/bundle.py`, `ui/main_window.py` | Save/load currently supports project versions 1/2 with probe geometry, routing, pose, and atlas calibration. A future version must persist assets/revisions, skull registration, drive placements, travel, and probe attachment transforms, while still loading old plans. |

The installed dependency requirements already include PyVista and VTK. The
[STL reader](https://docs.pyvista.org/api/readers/_autosummary/pyvista.STLReader.html)
and [collision filter](https://docs.pyvista.org/api/core/_autosummary/pyvista.PolyDataFilters.collision.html)
provide relevant primitives. Those online docs are newer than Atlaxis's allowed
PyVista versions; exact API use must be checked against the lockfile at implementation.
Prefer prepared STL/VTP meshes at runtime; STEP tessellation is a separate asset
preparation task whose conversion tool, accuracy, and permissions remain to be chosen.

## Proposed implementation sequence (not performed)

1. **Qualify assets.** Confirm species and drive variants/revisions; obtain usable
   assets and rights. Record units, axes, source revision, fixed/moving parts,
   attachment datum, and full travel. An explicitly schematic Cambridge size box
   could support an early layout preview, but its shape error is currently unknown
   and it cannot satisfy a requirement for accurate drive geometry.
2. **Add skull placement.** Independent visibility/opacity, import, landmarks, and
   saved skull-to-atlas transform. Show its registration status. Keep brain-surface
   entry, skull surface, and drive-base mounting point distinct.
3. **Add drive/probe assemblies.** Select a drive, set its base AP/ML/DV and orientation,
   and define where the probe attaches to its carriage. Base position stays fixed
   as travel moves the carriage and probe. Resolve probe tip-to-attachment offset
   and enforce the model's physical travel, rather than treating existing insertion
   depth as drive travel. Convert CAD millimeters to internal micrometers once.
4. **Support placement decisions and persistence.** Multi-drive layout and measured
   clearance/intersection feedback, save/reload, and companion export updates.
   Account for intended mounting contact, probe passage through a craniotomy, and
   the full moving envelope. Positive safety clearance, complete containment, and
   insertion/removal/tool access are not established by surface intersection alone.
   Headstages, flex cables, cement, caps, and tools need geometry or explicitly
   declared space reservations before claiming whole-implant fit.

Future acceptance evidence should include known-dimension imports, correct axis
signs and mm/um scale, measured landmark residuals independent of visual fit,
static bases at both travel limits, probe/drive attachment consistency, tilted
and adjacent assemblies, and lossless project round trips with old plans loading
unchanged. No numerical accuracy threshold is justified by the current data.

## Accepted scope and implementation plan — 2026-09-30

The user requested skull display and `Make craniotomy` with Rectangle, Circle,
and Polygon ROIs. Implement that independent part now; drive attachment dimensions
are still being collected. Do not substitute an expanded brain surface for bone.

1. Add a skull surface model imported from local STL/OBJ/VTP, explicit input units,
   axis directions, rigid registration, visibility, and opacity. Keep the original
   triangles and editable opening definitions, without modifying the source file.
2. Subtract each ROI's AP/ML prism through the skull along DV (updated user request:
   no depth-range controls).
   Split intersected triangles along the prism planes, including a small opening
   contained inside a large triangle. Support concave simple polygons by triangulation;
   reject self intersections. A circle is a regular 128-gon (maximum radial error
   approximately 0.0302% of radius). This edits a surface, does not infer bone
   thickness or manufacture watertight cut walls, and never changes brain/probe data.
3. Add skull settings and a dorsal ROI editor with draw, move, replace, delete,
   and a 3D preview. Show the complete dorsal projection and cut all skull surfaces
   along the ROI's DV projection. Cancel restores the pre-dialog state.
4. Persist the source triangles, registration, visibility, and ROIs in project
   version 3, retaining version 1/2 loading. Embed imported geometry to keep projects
   portable; do not bundle or download third-party skull assets automatically.
5. Review the scoped diff and perform at most one lightweight changed-file check,
   per repository instructions. No new tests, broad checks, or GUI launch.

Acceptance: each shape removes intersecting skull surface through its DV projection;
moving/deleting an opening restores the old surface from the original;
ROI coordinates and mm/um conversion agree with the atlas frame. Old projects
continue to load without a skull. All new state survives save/load. Model placement
is manual and must not be labeled atlas-registered by default. Runtime GUI behavior
and anatomy/registration accuracy remain unverified without an actual skull asset.

### Drive and probe decisions retained

- Use product names without a model-status suffix, and the short description
  `公開寸法を参考にした簡易モデル。` Screws and fine mechanism details are omitted.
- Separate fixed body/base from moving arm. The arm and probe travel together;
  allow the probe-base attachment height to be set independently of drive travel.
- Scope is all 205 registered models: Cambridge 171, NeuroNexus 31, Neuropixels 3.
  Electrode contours and nominal shank thickness do not establish mounting-base
  dimensions. Unknown dimensions must remain unknown or be entered by the user.
- The user owns Cambridge/3Dneuro drives. Requested mounting face width/height/
  thickness, arm lower-edge heights at both travel limits measured from the drive
  bottom, mounting-face offset from the fixed body, and exact NP-drive variant.
- Subsequent user clarification: Cambridge hardware on hand is **nano-Drive only**.
  Reported measurements: overall height including screw 11 mm, body width 4 mm,
  moving-part width 1 mm, thickness 2 mm. Do not treat overall height as arm height
  or automatically assign overall thickness to the arm. The user subsequently
  specified pico-Drive height 7 mm, with all other dimensions the same as nano
  (body width 4 mm, moving-part width 1 mm, thickness 2 mm).
  User explicitly requested public information for metal
  drives; do not make progress on those conditional on user measurements.
- Rechecked manufacturer pages on 2026-09-30: S/L base 3.3 x 4.45 mm, S arm
  3.6 x 8.35 mm, L arm 5 x 10 mm, travel approximately 7 mm, 282 um/turn.
  The linked documentation site `recover-reuse.it` could not be retrieved.
  Re-read the pinned public v10 README via the GitHub connector: base 3.6 x
  4.7 mm, height 15 mm, travel 7 mm. These are distinct revision facts, not a
  verified combined commercial assembly. Arm thickness and absolute mounting
  heights are not specified on the inspected product pages.
- Visually inspected official catalog drawings: Cambridge ASSY-79/116/156 interface
  chip length 7.6 mm and thickness 0.3 mm; ASSY-236 width 2 mm and length 7.6 mm;
  ASSY-350 width 2.6 mm, length 7.6 mm, thickness 0.3 mm. Do not extrapolate to all
  assemblies or confuse connector-PCB thickness with interface-chip thickness.
- Official Neuropixels datasheets: NP1 probe-base width 6.2 mm, length 10.7 mm;
  SMD base width 7.2 mm, length 12.2 mm (segments require the assembly drawing).
  NP2 probe/SMD width 3.5 mm, combined length 14 mm. Si-spacer versus metal-cap
  packaging changes thickness (NP1 about 1.2/1.8 mm; NP2 about 1.28/1.83 mm).
  Existing probe IDs do not encode this packaging choice. NeuroNexus mounting
  packages also need mechanical identification separately from electrical wiring.
  Sources: [Cambridge catalog](https://www.cambridgeneurotech.com/assets/files/Cambridge-NeuroTech-Product-Catalog.pdf),
  [NP1 datasheet](https://www.neuropixels.org/_files/ugd/328966_9f784121a69f4f56bd314ffdf7f86d2b.pdf),
  [NP2 datasheet](https://www.neuropixels.org/_files/ugd/328966_2b39661f072d405b8d284c3c73588bc6.pdf).

## Work and verification record (initial investigation)

- Ran `git status --short` initially: only the pre-existing modification to
  `plan_and_log/2026-09-21-desktop-installers.md` was reported; left untouched.
- Ran `git switch -c feature/skull-drive-planning` successfully.
- Inspected the relevant source with bounded `rg`, `sed`, and `cat` reads.
  No root `tests/` directory was present at the attempted inspection path.
- Checked manufacturer pages/catalog text, upstream file listings and documentation;
  retrieved the four v10 STEP texts. Skull availability is based on repository
  listings, not successful local rendering.
- Added only this investigation report. No CAD/STL assets, dependencies, runtime
  code, or generated output were added. No tests, builds, GUI launches, simulations,
  or CAD conversion were run. No commit or push was made.
- Remaining prerequisites: confirm species/NP variant, Cambridge geometry, asset
  permissions, physical attachment datums, commercial/CAD revision correspondence,
  and skull registration accuracy. Runtime and mechanical feasibility remain to
  be demonstrated after those choices.

## Implementation record — 2026-09-30

- Added `implant/skull.py`: local surface import, explicit units/axis registration,
  persistent source geometry and finite-depth opening definitions, simple-polygon
  validation, concave decomposition, and surface clipping along prism planes.
  Native geometry is stored in mm; rendering converts to um once before applying
  the existing stereotaxic-to-atlas transform. Original source files are untouched.
- Added `ui/skull_dialog.py` and main-window actions: skull placement/opacity/
  visibility, a depth-band dorsal projection, Rectangle/Circle/Polygon drawing,
  movement/redrawing/deletion, preview, and dialog cancellation rollback.
  The projection is for editing only; the 3D actor uses the imported surface.
- Project format 3 embeds the source mesh and all skull/opening state; formats
  1/2 remain accepted. Brain annotations, electrode geometry, contact mapping,
  insertion coordinates, and bundle companion exports were not changed.
- Updated the README workflow. No vendor mesh/CAD asset, dependency, test, or
  generated output was added to the repository. Preserved the pre-existing
  `plan_and_log/2026-09-21-desktop-installers.md` modification. No commit or push.
- Reviewed the task's tracked diff and both new source files. Corrected scene
  ownership, initial opening selection, stable opening order, and rejection of
  adjacent overlapping polygon edges during that inspection.
- Only execution check, completed with exit code 0:
  `PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-skull-pycache-20260930 .venv/bin/python -m py_compile src/probe_planner/implant/skull.py src/probe_planner/ui/skull_dialog.py src/probe_planner/ui/main_window.py src/probe_planner/rendering/scene.py src/probe_planner/project/save_load.py`.
  No tests, GUI, broad lint/build, runtime geometry checks, or save/load round-trip
  checks were run, following the repository's verification limits.
- Remaining: verify GUI and cutting behavior with a real registered skull;
  assess interactive performance for large meshes; no atlas-registered skull is
  bundled. Cuts remove surface within the chosen depth band, without generating
  watertight sidewalls. Circle approximation is documented above. Drive geometry,
  probe-base attachment, and travel simulation remain separate follow-up work;
  public commercial-drive specifications do not yet establish all arm offsets.

## Requested revision — 2026-09-30

The user removed the need for DV-range input and supplied Cambridge travel geometry.
Scope and steps before editing:

1. Remove the DV controls and depth-band preview; retain the three existing ROI
   shapes, movement, deletion and cancellation behavior.
2. Remove depth limits from new opening records and clipping. Cut all skull
   surfaces in each AP/ML ROI along DV. On import, discard the former uncommitted
   version-3 preview's `dv_min_mm`/`dv_max_mm` fields; version 1/2 projects are
   unchanged. No original skull, brain, or probe coordinates are edited.
3. Update the README and record the Cambridge geometry and explicit assumptions
   for the pico estimate. Review only the changed portions. No additional execution
   checks are planned: the task's single lightweight check was used above.

Cambridge datum: fixed-body bottom is height 0; positive height is upward. Nano
overall height 11 mm includes a 1 mm screw cap, giving a 10 mm fixed body. The user
reports the arm can protrude 0.5 mm above that body (upper endpoint 10.5 mm), travel
7.5 mm, lowest lower endpoint -5.5 mm, highest lower endpoint +2 mm, and arm height
8 mm. The last three quantities imply an upper endpoint of 10 mm, differing by
0.5 mm from the stated protrusion. The user explicitly resolved this by prioritizing
the upper endpoint 10.5 mm, lowest lower endpoint -5.5 mm, and travel 7.5 mm:
The initial resolution was an 8.5 mm arm. **A later direct user correction gives
the nano arm height as 7.5 mm**, superseding both the 8 mm and 8.5 mm values.
The user subsequently corrected the lower protrusion to 4.5 mm, resolving the
endpoints to a maximum upper end +10.5 mm and minimum lower end -4.5 mm.

For pico, user-specified travel 3.5 mm supersedes the earlier catalog's 4 mm for
this planning model. With a 7 mm overall height, the same 1 mm cap, and 0.5 mm
upper protrusion, its maximum upper endpoint is 6.5 mm and minimum upper endpoint
is 3 mm. Arm height additionally requires a lower-endpoint assumption; it is not
determined by overall height and travel alone. Use the corrected nano's fully
raised lower endpoint +3 mm as the shared-datum assumption. This gives a **3.5 mm
pico arm**, superseding the earlier 4.5 mm estimate. Both fixed body and arm are
then 4 mm shorter than nano; pico remains an estimate, not a measured assembly.

### Cambridge planning dimensions (nano corrected; pico inferred)

All heights are mm relative to the fixed-body bottom (0), upward positive. Travel
`q` is positive downward, with `q=0` fully raised. For both models,
`h_lower(q) = 3 - q`; nano has `h_upper(q) = 10.5 - q`, and pico has
`h_upper(q) = 6.5 - q` under the shared-datum assumption.

| Quantity | nano-Drive | pico-Drive |
| --- | --- | --- |
| Overall height, including cap | 11 | 7 |
| Fixed-body height, excluding cap | 10 | 6 |
| Cap height | 1 | 1 (same-cap assumption) |
| Fixed-body width x thickness | 4 x 2 | 4 x 2 |
| Arm width | 1 | 1 |
| Arm height | 7.5 (latest user measurement) | 3.5 (inferred) |
| Travel q | 0 to 7.5 | 0 to 3.5 (user-specified) |
| Lower end, fully raised / lowered | +3 / -4.5 | +3 / -0.5 |
| Upper end, fully raised / lowered | +10.5 / +3 | +6.5 / +3 |

Pico's arm height and lower-end positions are estimates based on the shared +3 mm
raised lower-end datum; they are not manufacturer-verified dimensions. The cap is
part of the fixed assembly, not arm travel. The previously reported 2 mm thickness
does not independently resolve moving-arm thickness or front/back attachment offset.

### Revision outcome

- Removed DV controls, depth-band projection, and depth constraints from new
  opening records and clipping. The full ROI projection now removes all intersecting
  skull surfaces along DV. Rectangle/Circle/Polygon and the original-mesh-based
  editing workflow remain in place. Previous preview depth fields are dropped on
  load to apply the requested through-opening semantics.
- Updated the README and reviewed the changed model/UI call sites and documentation.
  No additional execution checks, GUI runs, tests, commit, or push. The earlier
  compile result applies to the previous revision, not these edits.
- Recorded the nano resolution and the explicit pico estimation assumption above.
  Drive rendering and probe/arm linkage remain unimplemented.

### Metal-drive measurements — 2026-09-30

The user measured 6.5 mm travel and an 8.5 mm moving arm. At its lowest position,
the lowest edge of the moving arm's base is level with the fixed-body bottom.
Use these measured values in preference to the earlier approximate 7 mm travel
and published 8.35 mm regular-arm height for this measured unit. Keep the public
specifications above as source observations, not active measured-model defaults.

With the fixed-body bottom at height 0, upward positive (mm):

| Quantity | Measured metal drive |
| --- | --- |
| Travel | 6.5 |
| Moving-arm height | 8.5 |
| Arm-base lower edge, fully raised / lowered | +6.5 / 0 |
| Arm upper edge, fully raised / lowered | +15 / +8.5 |

For downward travel `q` from the fully raised position, `0 <= q <= 6.5`,
`h_lower(q) = 6.5 - q` and `h_upper(q) = 15 - q`. Thus the moving base never extends
below the fixed-body bottom. The derived 15 mm is the moving arm's highest upper
edge, not an independent measurement of fixed-body height.

The exact measured metal-drive variant was not stated. Do not automatically apply
the 8.5 mm arm height or the 6.5 mm travel to the separate NP model; its previously
recorded public dimensions remain separate until identified. This is a dimensional
record update only. Reviewed the added record; no runtime edits, tests, commit or
push were performed.

### Nano arm-height correction — 2026-09-30

Latest direct user measurement: nano moving-arm height **7.5 mm**. Travel remains
7.5 mm. For arm lower-end height `b` at the fully raised position, the upper end is
`b + 7.5`; at the fully lowered position, the lower end is `b - 7.5`.

The previously reported maximum upper end +10.5 and minimum lower end -5.5 span
16 mm, but the corrected arm height plus travel span 15 mm. Both endpoints cannot
remain exact under a rigid-translation model. Asked the user which endpoint to use:

- Keep maximum upper end +10.5: raised lower end +3, lowered lower end -4.5,
  lowered upper end +3.
- Keep minimum lower end -5.5: raised lower end +2, maximum upper end +9.5,
  lowered upper end +2.

The user answered **4.5 mm**, correcting the lower protrusion and selecting the
first case. Nano is now consistent: arm height 7.5 mm, travel 7.5 mm, maximum upper
end +10.5 mm, and minimum lower end -4.5 mm. The raised lower end is therefore
+3 mm. Reusing that datum gives pico arm height 3.5 mm and lower-end range
-0.5 to +3 mm; the corrected table above records the active dimensions.
Reviewed the updated dimensional record only. No runtime changes, execution
checks, commit, or push were performed for this correction.

## Skull controls and responsiveness — 2026-09-30

User reports a disabled Skull checkbox and a generally heavier GUI. Source
inspection confirms the checkbox requires an already-imported skull. Its initial
checked state also falsely suggests that a skull is present. Actual timing/context
of the slowdown has been requested; no measured performance claim is established.

Scoped fix plan before edits:
1. Start Skull unchecked; after atlas calibration, allow clicking it to open skull
   import/settings when no skull exists. Cancel keeps it unchecked. Explain the
   atlas/import prerequisites in tooltips without pretending a bundled skull exists.
2. Validate source geometry on creation/import, not on every display toggle or
   dialog-only metadata edit. Keep dialog copies isolated for Cancel rollback.
3. Reuse the cut mesh and actor when source geometry, placement, and opening
   shapes/coordinates are unchanged. Update visibility/opacity/atlas transform
   separately; skip empty-skull redraws. Keep exact geometry and clipping semantics.
4. Draw the static dorsal projection once per opening-editor session, not every
   time an ROI is added/selected/deleted. Review the scoped changes and record
   unverified performance. No extra tests/benchmarks or GUI launch are authorized.

Evidence: `dataclasses.replace(Skull)` reruns full vertex/triangle validation;
Preview, OK and dialog-finally each call `cut_mesh`; `Scene.set_skull` recreates
the actor even for unchanged geometry; ROI selection/addition rasterize all
triangles again. These paths can explain stalls after skull import, but do not
establish the cause of sluggish probe/camera operations before skull import.

### Automatic species selection and lightweight display

The user clarified that the slowdown occurs at application startup and requested
automatic skull loading with rat/mouse atlases, without a separate import step.
Revised scope and steps before further source edits:
1. Resolve usable skull assets, reuse their documented coordinate registration,
   and load species-matched geometry in the existing atlas worker. Keep saved
   custom skulls/openings authoritative. Do not invent a registered skull by
   expanding the brain surface or silently substituting an anatomical proxy.
2. Keep full source geometry in plans; cache a separate display surface, simplify
   with a 0.025 mm accumulated absolute-error limit and preserved topology/borders,
   then clip openings. Reuse it for the 3D actor and dorsal ROI editor.
3. Defer atlas-only imports until atlas selection/loading. Inspect startup I/O
   separately from skull rendering; report performance as unmeasured.
4. Review the scoped diff and document asset availability, approximation decisions,
   checks already run, and remaining runtime verification. No new tests or broad
   checks under the repository verification budget.

Pinpoint contains species-specific skull prefabs, but mesh files are excluded
from Git and its linked public asset folder currently returns HTTP 404. The
prefabs alone do not establish a distributable, calibrated surface. Asked whether
the user wants to retain real-data-only semantics or accepts a clearly identified
planning approximation if usable source assets cannot be recovered.

The user explicitly accepted an approximate planning shape with a short label.
Implement a dorsal ellipsoidal cap sized from the loaded brain outline in the
default stereotaxic frame: AP midpoint and half-span, symmetric ML half-span,
5% AP/ML margin, and half the brain's DV extent as cap height. Shift its DV origin
so the analytic cap passes through Bregma (AP=ML=DV=0). Use 96 angular segments
and 32 rings (6,048 triangles), without a basal closing face. This is a schematic
cranial vault, not a CT-derived skull: no face, sutures, basal bone or measured
bone thickness; anatomical error is unknown. The 5% margin is a visualization
choice, not a measured brain-to-bone distance. Preserve original atlas and probe
coordinates, and saved imported skulls/edits. The model is generated in the atlas
worker only for rat/mouse atlases with a known Bregma preset, requiring no network
asset download. Mark it briefly in the GUI and persist that metadata in plans.

Implementation outcome (uncommitted):
- The atlas worker now prepares the species-matched schematic cap. The GUI shows
  `Skull (approx.)` with one short placement-planning explanation. Saved skulls,
  visibility, placement and openings override automatic geometry. Legacy plans
  without a skull field receive the cap; explicit `skull: null` remains removed.
- Source arrays are retained for saving. A separate cached display mesh targets
  20,000 faces for large custom imports with VTK accumulated absolute error set
  to 0.025 mm, topology preservation, no splitting and no boundary deletion.
  This is the algorithm's configured error limit, not an independently measured
  anatomical or Hausdorff-error guarantee. Openings are clipped afterwards.
- Visibility/opacity/frame changes reuse the actor. Dialog metadata changes avoid
  revalidating all vertices. The ROI editor rasterizes the reduced surface once.
- Deferred `AtlasDialog`/BrainGlobe imports until atlas selection. Storage still
  scans bundled templates at startup; no measured evidence justifies a broader
  storage rewrite. Read-only platform inspection found an x86_64 venv Python on
  an arm64 host; its contribution to startup time is unmeasured and the environment
  was not rebuilt.
- Pinpoint v2 comparison: species-specific prefab transforms, external skull
  assets, and shader-driven circular cutouts. No Pinpoint geometry or code was
  copied. The local implementation retains editable Rectangle/Circle/Polygon
  clipping rather than adding a separate shader architecture for a 6k-face cap.

Verification: reviewed affected source and the scoped tracked diff, including
the legacy/null distinction, mm-to-µm conversion, cache ownership, face winding,
and dialog rollback. The earlier `py_compile` command recorded in this log passed
before these later changes; it does not verify this revision. No further execution
checks, GUI runs, timing benchmarks, tests, dependency installs, commit or push.
The current GUI behavior, startup improvement and anatomical fit remain unverified
at runtime under the repository's single-check budget.

Primary references inspected:
- [Pinpoint mouse prefab](https://github.com/VirtualBrainLab/Pinpoint/blob/142489d9c8213ac2aea6a76d70bbb8331a71b64f/Assets/Prefabs/Rigs/SkullRig_Mouse.prefab)
- [Pinpoint rat prefab](https://github.com/VirtualBrainLab/Pinpoint/blob/142489d9c8213ac2aea6a76d70bbb8331a71b64f/Assets/Prefabs/Rigs/SkullRig_Rat.prefab)
- [Pinpoint craniotomy shader parameters](https://github.com/VirtualBrainLab/Pinpoint/blob/142489d9c8213ac2aea6a76d70bbb8331a71b64f/Assets/Scripts/Craniotomy/CraniotomySkull.cs)
- [Pinpoint external-asset instructions](https://virtualbrainlab.org/pinpoint/development.html)
- [VTK decimation error/topology controls](https://vtk.org/doc/nightly/html/classvtkDecimatePro.html)

## Independent GPU craniotomy display — 2026-09-30

User approved adopting the rendering approach as a reference, without reusing
Pinpoint code or assets. Goal: preserve automatic rat/mouse cap loading and make
ROI preview update only opening data, without CPU mesh cutting or actor rebuilds.

Implementation steps before source edits:
1. Add an independent VTK shader adapter for the existing skull actor. Pass stereo
   AP/ML millimeters as a separate vertex attribute, unaffected by VBO coordinate
   normalization, atlas transform or camera. Discard fragments inside the union
   of ROIs before depth-peeling early returns, at all DV levels.
2. Store shape records and polygon vertices in a floating-point data texture;
   update texture/counts when ROIs change, retain the shader and mesh. Rectangle
   uses bounds, Circle uses its analytic radius, and simple concave polygons use
   even/odd containment. Preserve invalid-shape rejection. Avoid fixed uniform
   array limits or silently truncating openings; reject texture-size overflow.
3. Separate source/placement cache keys from opening keys, preserve visibility,
   opacity, saved geometry, editing, delete and Cancel rollback. Keep the CPU
   `cut_mesh` utility available but remove it from interactive display.
4. Update README and this record, review affected source/diff. The ongoing task's
   one execution-check budget has already been used; no extra GUI/test/benchmark
   runs or new test infrastructure without an explicit verification request.

Rendering now intends analytic circles; CPU `cut_mesh` retains its documented
128-segment approximation (radial difference <=0.0302% of radius). Neither path
adds bone thickness or watertight walls. Shader float precision and rasterization
apply to display; saved ROI coordinates and source meshes retain full precision.
API research uses VTK's own shader hooks and texture handling, not Pinpoint source.

Outcome (uncommitted):
- Added `rendering/skull_shader.py` with independently written analytic rectangle/
  circle tests and polygon even/odd containment, bounding-box rejection and union
  of openings. RGB float records use nearest texel fetches, not a bitmap mask;
  the active GPU's texture dimensions are checked to prevent VTK resampling data.
- `MainWindow.render_skull` now caches the uncut display surface by source and
  placement only. `Scene` retains its actor/shader and updates ROI data separately.
  The dedicated AP/ML attribute stays in mm while the actor geometry uses µm;
  atlas and camera transformations do not change the footprint coordinate system.
- Discard precedes VTK's depth-peeling early returns. Cancel restores original
  ROI data; deleting the final opening uploads count zero. Visibility, opacity,
  save/load and the short approximate-skull label remain intact. No Pinpoint
  code, mesh, shader or branding was copied and no dependency was added.
- Updated README to distinguish display cutouts from the retained CPU surface-cut
  utility and its 128-segment circle approximation.

Verification performed: source/diff inspection of the shader, scene integration,
ROI cache key, dialog apply/delete/Cancel paths and documentation. Checked VTK
shader hooks in the 9.3.0 and 9.5.2 upstream templates and installed Python API
signatures; inspected named texture binding and float-texture handling. These
are source reads, not an executed rendering check. No new tests, syntax check,
GUI launch, GLSL compilation or timing benchmark was run. GPU compilation,
transparent depth peeling and interaction speed remain runtime-unverified.

## Mapper correction and numeric craniotomy editing — 2026-09-30

The user reported an atlas-load failure: `DataSetMapper` has no
`MapDataArrayToVertexAttribute`. They requested removal of the redundant toolbar
Skull button, automatic dorsal view on Make craniotomy, numeric rectangle/circle
sizes, and AP/ML center positioning.

Implementation steps before source edits:
1. Construct the skull actor with `vtkOpenGLPolyDataMapper`, which exposes the
   vertex-attribute API used by the shader. Keep other actors and ROI semantics
   unchanged; retain one skull actor across opening updates.
2. Move optional Skull settings into the Settings menu, retain the visibility
   checkbox, and select the 3D tab and existing skull-aligned Top camera preset
   when opening the craniotomy editor.
3. Add rectangle AP/ML dimensions, circle diameter, and center AP/ML in mm.
   Synchronize drawing and numeric controls without rewriting untouched saved
   coordinates. Numeric center edits translate existing geometry; for polygons
   the center is the midpoint of its AP/ML bounds. Preserve drawing, validation,
   Apply, Cancel and saved opening format.
4. Update README and this record and inspect the scoped source/diff. The ongoing
   task's execution-check budget is already used; no additional runtime checks
   or new tests are planned. Record unverified GUI/GLSL behavior explicitly.

Outcome (uncommitted):
- Replaced the skull's default DataSetMapper with an explicit OpenGL polygon
  mapper. Its installed API exposes the vertex-attribute method in the reported
  exception. The new shader/texture is prepared before replacing the old actor;
  scalar coloring is disabled so AP/ML attributes do not color the surface.
- Removed Skull from the toolbar, preserving optional import/placement/opacity
  under Settings and the existing visibility checkbox. Make craniotomy now
  selects the 3D tab and the existing stereotaxic Top camera preset.
- Added rectangle AP/ML sizes, circle diameter and center AP/ML inputs in mm.
  Drawing/dragging synchronizes the inputs. Numeric entry creates new openings
  without drawing, including when the user enters the displayed defaults.
  Changing one field preserves other coordinates at their original precision.
  Polygon centers translate all vertices, preserving concavity and completion;
  their bounds are read-only and center input waits until drawing is finished.
- Kept saved shapes, unlimited DV openings, Apply/Cancel and visibility semantics.
  Updated README. No change to atlas/probe coordinates or approximation geometry.

Verification: inspected the scoped diff and edited dialog source, the installed
VTK OpenGL mapper signature, and PyVista actor construction/addition APIs.
Reviewed reversed rectangle corners, arbitrary circle edge directions, negative
AP/ML, blank numeric drafts, partial polygons, signal blocking and Cancel paths.
No execution checks or new tests were run for this revision; the previous syntax
check predates these edits. GUI startup, GLSL compilation and interaction remain
runtime-unverified. No commit/push; unrelated installer notes left untouched.

## Anatomical skull surfaces — 2026-09-30

The user rejected the smooth schematic cap as visually inadequate and requested
a more realistic skull. Goal: replace the generated ellipsoid with species-specific
anatomical surfaces while retaining automatic atlas loading and responsive editing.

Implementation steps before source edits:
1. Obtain explicitly reusable micro-CT-derived rat/mouse meshes, record source,
   attribution, units and any inferred registration. Prepare compact display assets
   offline; never download or decimate large originals during GUI startup.
2. Replace the default cap with bundled anatomical surfaces. Express them in the
   existing Bregma-relative mm frame; disclose approximate alignment separately
   from measured shape. Preserve individual custom meshes and opening coordinates.
3. Use smooth surface normals and a bone material, retaining the existing GPU
   cutouts and size/center controls. Include assets and attribution in source,
   wheel and desktop packaging; keep GUI explanations short.
4. Inspect the asset views and scoped source/diff and record preparation commands
   and limits. Asset conversion/landmark inspection is production work; no new
   tests, broad checks or GUI verification are authorized for this ongoing task.

Confirmed source candidates: rat, Pohl et al., Figshare 777745 v1, CC BY 4.0
(RatSkull_Mesh1.stl, 507,865,903 bytes); mouse, Mark Ungrin/MarkU,
Thingiverse 20200, with original micro-CT credited to Mark Henkelman/MICe, CC BY
4.0 in the author's page metadata. Neither source establishes registration to
Atlaxis's atlas versions. Landmark placement must be recorded as approximate;
do not claim individual-animal accuracy or infer a rat mesh by scaling a mouse.

### Pinpoint model provenance follow-up

The user clarified that the question concerns how Pinpoint obtained/created its
skull models, not its rendering technique. Public evidence now includes:
- [Issue #24](https://github.com/VirtualBrainLab/Pinpoint/issues/24), opened by
  Daniel Birman on 2022-02-10, supplies `mouseSkull.zip`. The attachment remains
  downloadable, despite the separate asset-folder link being unavailable.
  Archive inspection found only `mouseSkull.STL` (33,286,284 bytes), with no
  provenance, license or acquisition-method document. The binary header names
  `mouseSkullPart` but does not identify a creator or imaging source.
- Birman's 2022-02-15 comment states: "Done, but unclear how to align properly".
  [Issue #59](https://github.com/VirtualBrainLab/Pinpoint/issues/59) subsequently
  records a Bregma-aligned skull, added in v0.6.1. These are historical records,
  not measurements of current registration error.
- The v2 `Skull.asset` manifest registers `skull.obj` and `skull.prefab`; the
  referenced mesh directory is excluded from Git. Mouse and rat rigs reference
  different prefab GUIDs. The original scan/provider, reconstruction software,
  and rat-model provenance remain unconfirmed. The paper's full text and
  acknowledgements did not identify a skull source.

Do not attribute the separately located Pohl or Ungrin CT datasets to Pinpoint,
or redistribute its issue attachment based only on its public availability.
No anatomical replacement has been integrated yet. Rat source preparation is
in progress; a PyVista offscreen preview failed because no OpenGL context was
available. Mouse STL retrieval from the author's download button timed out.
No application tests were run in this follow-up.

## Flat-skull landmark proposal — 2026-10-01

The user requests Bregma–Lambda and bilateral leveling to be performed here,
with visual results for an accept/reject decision. Prepare a reviewable skull
registration proposal before adopting anatomical defaults in the application.

1. Inspect the actual rat and mouse surfaces at sufficient detail to distinguish
   visible sutures from inferred landmarks; retain original geometry/provenance.
2. Place candidate Bregma/Lambda points and a paired left/right dorsal surface
   reference halfway between them, at equal transverse offsets.
   Compute a rigid frame with Bregma at zero, Lambda on the posterior horizontal
   axis, and the transverse axis level. Record every estimated landmark and scale.
3. Render top, side, and front views with the candidate landmarks and reference
   lines. A zero residual from the fitted transform establishes geometric leveling,
   not anatomical correctness. Do not present it as registration accuracy.
4. Record results and unresolved source/landmark issues. Keep uncertain models
   and calibration out of runtime defaults until the user's visual review.

WHS source discrepancy: the authors' 2023 coordinate-system note states 4 degrees,
but its metric Bregma/Lambda coordinates differ by AP 8.2421875 mm and superior
0.9375 mm, implying approximately 6.49 degrees. Its high-resolution Lambda z=434
also conflicts with the WHS-relative z=216 and low-resolution z=232 entries
(both imply z=464, consistent with the older coordinate release note). Do not
silently treat the nominal 4 degrees as an exact landmark-derived leveling.
Source: https://www.nitrc.org/docman/view.php/1081/194197/

Source selection update: the user explicitly prefers scientific CT-derived skull
meshes. Pohl's original paper confirms the rat mesh comes from micro-CT of a
250 g male Wistar rat (0.0883 mm slice thickness). The STL's coordinate-unit
conversion remains unverified; the paper's physical print dimensions cannot be
substituted for the mesh calibration. The mouse preview uses UT Austin DigiMorph
specimen TMM M-3196, an adult female house mouse, scanned by Ketcham/Colbert on
1999-03-16 (481 coronal slices at 0.0435 mm). Its STL is directly downloadable
from https://digimorph.org/specimens/Mus_musculus/mus.stl. This is not an Allen
C57BL/6J template specimen. DigiMorph permits rendering the download but its
site-wide redistribution terms are restrictive; no mouse asset is being bundled
in the app. MarkU's CC BY micro-CT mesh download remains unavailable through the
site UI. The Pinpoint attachment was inspected only as a reference, not used for
the proposed scientific-source skulls.

Preview method: visually select suture-junction candidates on the original
meshes and intersect dorsal rays with the original surface. Define AP from
Lambda toward Bregma. Sample paired surfaces at the B–L midpoint with transverse
offsets of ±0.30 times the candidate B–L length, remove the AP component of their
difference to define ML, and set DV = AP × ML. Apply a rigid transform only.
This levels the selected four points by construction; it does not establish
global skull symmetry or anatomical landmark accuracy. Figures use normalized
B–L units for composition; the exported coordinates retain source units. No
physical scale, brain-overlay registration, or application default is approved.

### Lambda definition correction

The user's review correctly identified that the original Lambda candidates were
too rostral for the stereotaxic convention: they marked the visible central
suture junction. The WHS original paper (Papp et al., 2014, Figure 3) uses the
midpoint of a best-fit lambdoid curve; the mouse CT/MRI atlas (Chuang et al.,
2009) likewise specifies fitted sagittal/lambdoid lines. The central rostral
spur must not be treated as the default stereotaxic Lambda.

- https://pmc.ncbi.nlm.nih.gov/articles/PMC4160085/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2723180/

Revise the private proposal by manually tracing bilateral lambdoid limbs and
the sagittal midline on the original meshes. Use a quadratic curve for the
curved rat limbs and a line for the nearly transverse mouse limbs; intersect
with a fitted sagittal line, then project onto the original dorsal surface.
Show original and revised points together with the selected samples and fitted
lines. These are approximate candidate landmarks, not author-provided labels;
fit residuals measure tracing consistency, not anatomical error. Recompute the
rigid review transform from the revised candidate, without changing runtime.

Bresee et al. (2023; https://pmc.ncbi.nlm.nih.gov/articles/PMC10617617/)
traced Bregma/Lambda from the same mouse CT specimen TMM M-3196. Its public
Zenodo archive (https://doi.org/10.5281/zenodo.7992354) includes
`mouse_facial.mat`, but the accompanying MATLAB script identifies its frame as
the average whisker-row plane. Those Bregma/Lambda points are 1.929536 mm apart;
the required map to the original STL was not found. Do not paste these
registered facial coordinates into the raw skull or claim they validate our
landmark candidates.

Proposal output: `lambda-correction-review.png`, revised rat/mouse
`*-alignment-candidate.png`, and their `*-landmarks.json` plus
`lambda-fit-candidates.json` were saved under
`/Users/yoshi/.codex/visualizations/2026/09/26/01a0dee7-418f-76d2-996b-bf97cd774682/skull-alignment-review/`.
The revised projected Lambda is (242.553, 515.622) in rat native X/Z and
(5.641, 17.526) in mouse native X/Z. These replace the previous central-junction
candidates; numbers are recorded for reproducibility, not precision claims.
Side/front preview cameras were also corrected to use proper rotation bases.

Artifact production completed with:
- `MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl .venv/bin/python /private/tmp/atlaxis-skull-review/lambda_review.py`
- `MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl .venv/bin/python /private/tmp/atlaxis-skull-review/build_review.py`

The correction overlay and updated views were visually inspected. A data-read
attempt initially failed because optional `lxml` was unavailable; it was repeated
using the standard-library XML parser without installing dependencies. No
application code was changed, and no application tests or GUI checks were run.
Anatomical accuracy, rat physical scale, source licensing for mouse distribution,
and registration to the brain atlases remain unresolved. Work is uncommitted.

### Bilateral appearance review

The user flagged apparent left/right distortion in the candidate views. Source
inspection confirms that the preview applies translation, rotation and a uniform
plot-only scale, with equal-aspect orthographic cameras; it does not warp or
anisotropically scale either skull. A narrowly scoped NumPy check of both saved
3x3 transform blocks returned singular values [1, 1, 1], determinant approximately
1 and orthogonality error below 5e-16. The check only establishes rigidity.

The AP axes differ from native scan -Z by 2.335 degrees (mouse) and 6.435 degrees
(rat) in dorsal projection; these are not anatomical alignment-error estimates.
The preview's directional lighting also differs left/right. Leveling one pair of
surface points does not validate the whole skull's midsagittal plane. Original
mesh views and candidate views were inspected, but the contributions of specimen
shape, reconstruction, landmark selection and viewing orientation were not
quantitatively separated. Do not claim a validated bilateral anatomical alignment
or apply the candidate defaults based solely on these views. No app changes.

### User-directed landmark adjustment

The user requests a small rightward mouse Lambda shift, and rightward rat
Bregma / leftward rat Lambda shifts in the displayed top view. Prepare a new
review proposal, retaining the previous coordinates and distinguishing user
adjustments from the earlier suture-fit estimates. Interpret the small shifts
as +0.02 B–L lengths for mouse Lambda, +0.03 for rat Bregma, and -0.03 for rat
Lambda along the previous view's rightward ML axis. These magnitudes are an
initial visual interpretation, not measurements or validated anatomical labels.

1. Move the requested points in the previous frame; intersect dorsal rays with
   the unchanged original CT surfaces so each candidate remains on the skull.
2. Recompute the B–L / paired-surface rigid leveling using the same procedure.
3. Render a comparison in the previous camera frame plus updated leveled views;
   keep the app unchanged pending visual confirmation.

Completed with `MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl .venv/bin/python
/private/tmp/atlaxis-skull-review/adjust_review.py` (one shell command).
The fixed-camera `landmark-adjustment-review.png` and both
`*-alignment-candidate-adjusted.png` views were visually inspected: shifts match
the requested screen directions. `*-landmarks-adjusted.json` records the prior
points/frame, interpreted shift magnitudes and updated source coordinates;
the earlier proposal files remain intact. All outputs are in the same persistent
review folder. No app source edits or app tests; visual approval remains pending.

The user requests one further very small rightward rat Bregma adjustment.
Move only Bregma by +0.01 of the current B–L length along the current top-view
ML axis (approximately one third of the prior shift), keeping Lambda's source
coordinate unchanged. Retain the previous proposal and save this revision as
`rat-*-adjusted-v2`. Relevel using the existing procedure and visually inspect
the resulting figure; do not modify the app before the requested review.

This additional revision completed with
`MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl .venv/bin/python /private/tmp/atlaxis-skull-review/adjust_rat_v2.py`.
The `rat-alignment-candidate-adjusted-v2.png` figure was visually inspected;
its coordinates and prior frame are saved in `rat-landmarks-adjusted-v2.json`
in the persistent review folder. Mouse and previous proposals remain unchanged.
No application source changes or tests in this revision.

### Skull-wide orientation review

The user still observes tilt. The earlier construction levels a single pair of
surface points, which cannot establish the skull-wide midsagittal orientation.
Replace that orientation estimate for the next private rat proposal only:

1. Keep the latest Bregma/Lambda source coordinates fixed and preserve all mesh
   vertices/faces. Estimate a bilateral plane from a broad cranial-vault region,
   excluding the mandible, rostrum and attached vertebrae.
2. Fit the plane by minimizing distances between that region and its reflection,
   using deterministic spatial sampling and a robust loss for local asymmetry.
   Record sampling, region, constraints and residuals; residuals measure shape
   symmetry, not anatomical registration accuracy.
3. Use its normal as ML; choose DV perpendicular to both ML and the fixed B–L
   vector. This makes the fitted plane vertical and B/L equal in height. Do not
   force Lambda onto ML=0, which would overconstrain this correction.
4. Render before/after front/top views with neutral left/right lighting and the
   fitted plane. Keep the prior proposals and application defaults unchanged.

This is a reviewable rigid-orientation estimate, not shape symmetrization or a
claim that an individual CT skull is perfectly symmetric. If the fit fails or
does not resolve the observed tilt, report that outcome without moving landmarks
again merely to improve appearance.

Completed asset analysis/rendering with
`MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl .venv/bin/python /private/tmp/atlaxis-skull-review/rat_symmetry_review.py`.
The fit used AP [-1.25, 0.65], DV [-0.4, 0.65] in previous B–L units,
0.025-unit voxel-centroid sampling, soft-L1 loss with scale 0.02, bounded
local plane slopes (15 degrees) and offset (0.15). It converged in 26 function
evaluations without touching bounds. The proposed rotation differs by only
0.1597 degrees; reflection RMS decreased from 0.01618 to 0.01263 B–L units.
These are within-fit shape residuals, not independent validation or uncertainty
bounds. B/L source coordinates stayed fixed and their resulting DV difference
is zero; Lambda is at ML 0.0661 source units rather than forced to zero.

`rat-symmetry-orientation-review.png` was visually inspected with identical,
bilaterally balanced lighting in both columns. The orientation difference is
barely visible and residual bilateral shape differences remain. This does not
establish that the user's perceived tilt has been resolved, nor distinguish
anatomical asymmetry from CT/reconstruction effects. Parameters, transforms and
residuals are in `rat-landmarks-symmetry-proposal.json` in the persistent review
folder. No further landmark movement, shape warping or application changes.

## Approved CT reference integration — 2026-10-01

The user approved the current anatomical references for Atlaxis and asks what
still needs confirmation. Use the adjusted mouse landmarks and the rat
symmetry-plane proposal. Integrate as approximate reference anatomy, preserving
the approved shape/asymmetry; do not imply individual-animal registration.

1. Prepare compact meshes offline (target 20,000 triangles) from the original
   CT surfaces, preserving the reviewed rigid transforms. Record provenance,
   landmark coordinates, scaling and sampled simplification error. Use uniform
   reference sizing: mouse B–L 4.25 mm (AtlasGuide adult CT/MRI reference), rat
   B–L 8.30 mm (rounded WHS landmark separation), not a claim about source STL
   calibration. Do not scale brain, probes or drive geometry.
2. Bundle the CC BY 4.0 rat asset and attribution. Install the reviewed DigiMorph
   mouse asset only in this user's selected data folder (`skulls/mouse.npz`),
   outside repository/build inputs. Its redistribution permission is unverified.
   Load local reference assets automatically, then bundled assets; retain the
   existing schematic cap when no CT reference is installed.
3. Add skull-only size adjustment via B–L distance, preserve metadata/landmarks
   in saved plans, use smooth shading and show the reference landmarks. Reuse
   existing GPU craniotomy/cached rendering and atlas-loading worker.
4. Update packaging, concise UI wording, provenance documentation and this log.
   Preserve saved custom/removed skulls and prior plans. Inspect the scoped diff;
   no new tests or broad verification. Earlier task execution-check budget is
   consumed, so report source inspection and asset preparation separately from
   unrun application/GUI tests.

Open scientific issue: this integration uses the existing atlas coordinate frame
(Allen nominal +5-degree pitch; WHS atlas-aligned, zero pitch). It does not resolve
the WHS nominal 4-degree vs landmark-derived 6.49-degree discrepancy or apply
unvalidated brain scaling. Reference skull size/orientation and correspondence
to the selected brain atlas remain approximate and must be disclosed.

Distribution update requested by the user: neither mesh will be bundled. Both
CT originals are fetched directly from their author/provider on first atlas
load, prepared in the worker and cached in the selected data folder. Ship only
source links, terms, and reviewed landmark/transform metadata. Existing cached
references load without network or runtime decimation. Download failure must
leave the atlas usable with an explicitly identified schematic fallback. This
supersedes step 2's rat bundling / manually installed mouse split.

### Integration outcome

Implemented provider downloads with original-file SHA-256 checks, reviewed rigid
placement, uniform reference sizing, one-time simplification and definition-keyed
local NPZ caches. Download/preparation runs in the existing atlas worker; startup
does not fetch a skull. Both source and installer contain metadata only. Failed
downloads retain the schematic cap and expose the reason in its source description.

The skull settings now expose Bregma–Lambda size and restoration of the atlas
reference. Red Bregma / blue Lambda markers share the skull's placement and atlas
transform, including after origin changes. Cached CT surfaces use smooth normals.
Source metadata, landmarks and skull-only scale persist in plans; existing custom
or removed skulls remain intact. README and notices describe provider terms,
including the implications of sharing a plan with an embedded mesh.

Production asset preparation used `.venv/bin/python` with
`MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl` to call
`reference_definition`, `reference_cache_path` and `prepare_reference` for the
existing provider originals `/private/tmp/atlaxis-rat-skull-pohl.stl` and
`/private/tmp/atlaxis-skull-review/mouse-digimorph.stl`. It completed successfully:

| Species | Triangles | Cache bytes | Sample median / p95 / max distance (mm) |
| --- | ---: | ---: | --- |
| Rat | 19,999 | 208,814 | 0.0222 / 0.0905 / 1.6779 |
| Mouse | 19,999 | 203,895 | 0.0096 / 0.0369 / 0.2448 |

The deterministic 5,000-vertex samples quantify reduction of these source meshes,
not atlas registration. The rat maximum shows substantial local loss of detail;
there is no whole-surface error bound or clearance-accuracy claim. Shape asymmetry
was not corrected by nonrigid warping. These lightweight references require visual
review in the app; no application test or GUI verification was run in this update.

Installed the produced `rat-74d83b512aa1.npz` and `mouse-fbf06bfa3152.npz` in the
user's selected `/Users/yoshi/Documents/Atlaxis/skulls/`, preserving any existing
same-named cache. This user can load them without repeating the original downloads.
The new downloader itself has not been exercised end-to-end; production preparation
used originals already obtained during the investigation. Source/diff inspection
covered the changed loading, placement, rendering, persistence and packaging paths.
No tests, lint, build, or GUI launch were run; unrelated installer notes remain
untouched. Remaining scientific confirmation is specimen size and skull-to-brain
registration, particularly the rat brain's skull-level rotation.

## Craniotomy editor and microdrives — 2026-10-02

Implement the user's requested centered dorsal editor, per-craniotomy table,
Apply-only persistence, corrected laterality, hidden-by-default skull, and the
previously specified four drive types. Preserve unrelated pending changes.

1. Replace the flat silhouette with a shaded, translucent dorsal projection and
   landmark overlays. Align its screen axes and displayed ML sign with the main
   Top view. Keep physical AP/ML coordinates unchanged. Sutures may only be
   identified as approximate guides unless actual registered traces are available.
2. Replace the side list and form with editable table rows, + and row deletion,
   sequential Craniotomy names, left-drag drawing, right-drag movement, double-click
   fit and slower zoom. Polygon completion uses first-vertex closure or Enter.
   Apply commits all valid rows to the main scene; window close discards only
   unapplied edits. Remove OK/Cancel and explanatory paragraphs.
3. Default newly loaded skull references to hidden while retaining saved choices;
   applying craniotomies shows the skull. Preserve exact ROI geometry on selection.
4. Add four dimension-recorded microdrives, probe-base attachment controls and
   bounded carriage travel. Travel translates the probe and carriage rigidly along
   the insertion axis while the drive body stays fixed. Persist drive state with
   plans. Unknown mechanical dimensions require explicit values, not fabricated
   manufacturer specifications; keep the short model description requested earlier.
5. Review the task's changed source/diff and run at most one lightweight changed-file
   check. No new tests, broad suite, build, benchmark or environment changes.

### Outcome and decisions

- The user rejected inferred suture guides. Added an original-CT dorsal shading
  image before mesh reduction, stored locally with preparation-version-2 caches.
  No suture traces are fabricated; relief is visible only where the source
  segmentation resolves it. The editor applies 72% image opacity and overlays
  Bregma/Lambda and A/P/L/R. Pixel-grid extents include image-axis rounding.
  Custom/rotated placements shade the placed display mesh instead.
- Removed the side list, explanatory paragraphs, mode selector and OK/Cancel.
  Added table rows, + / ×, Craniotomy N names and Apply-only commits. Left draws,
  right moves the current ROI, middle pans, double-click fits (restoring geometry
  before the preceding click). Polygon completion uses first-vertex closure or
  Enter. Zoom is 1.06 per wheel notch. Applied edits survive window close;
  unapplied rows do not change the parent skull. Empty table + Apply removes all
  craniotomies. Partial/invalid polygons cannot be applied.
- Screen ML direction is obtained from the actual Top camera basis. Table ML is
  left-positive, like probe controls; internal/saved ML remains right-positive.
  This fixes the reported mirrored editing without moving existing saved holes.
  New skulls start hidden; saved visibility is preserved; Apply shows the skull.
- Added probe-owned DriveMount state and a Microdrive dialog with four choices,
  probe-local attachment, carriage mounting height and bounded downward travel.
  Travel changes probe translation by `delta_q * insertion_direction`; fixed
  drive points receive `+delta_q` toward the probe base, cancelling that world
  translation. Carriage points stay relative to the probe. Tilts and y_to_base
  signs reuse the existing probe transform; no new axis convention is introduced.
  Slider travel applies on release to avoid contact remapping on every mouse move.
  The attachment seed is the proximal face of displayed geometry, not a claim
  that every library probe has a measured mounting package. Users can adjust it.
- Nano/pico use the corrected dimension table above. Regular metal uses measured
  arm/travel; NP is provisionally the published R2drive L / NP1.0 arm. Rechecked
  [S](https://3dneuro.com/products/r2drive) and
  [L](https://3dneuro.com/products/r2drive-l) manufacturer specifications: neither
  inspected page specifies fixed-body height or the NP raised lower-edge datum.
  The user's clarification was to attach the drive to the probe, not a new
  measurement. Consequently, regular Metal initially shows its mounting face and
  fixed footprint; NP shows its mounting face and fixed zero-travel reference.
  Body height/datum can be entered under Dimensions. Unknown arm thickness is a
  face, not an invented solid. Body offset 0 means adjacent planning planes.
  These limitations remain relevant to layout/clearance accuracy.
- Project format 4 persists each probe's drive. Formats 1–3 remain readable,
  including saved skulls/ROIs and first/additional probes. No drive CAD assets,
  dependencies, commits or pushes were added; unrelated installer notes stayed
  untouched. README and skull preparation documentation were updated.

### Checks and produced assets

Source/diff inspection covered the changed editor, physical-coordinate mappings,
drive transforms, serialization and rendering call sites. One changed-file syntax
check completed with exit 0 (temporary bytecode directory removed):

```sh
PYTHONPYCACHEPREFIX="$task_check_cache" .venv/bin/python -m py_compile src/probe_planner/ui/skull_dialog.py src/probe_planner/ui/drive_dialog.py src/probe_planner/ui/main_window.py src/probe_planner/implant/drive.py src/probe_planner/implant/instance.py src/probe_planner/implant/skull.py src/probe_planner/implant/skull_reference.py src/probe_planner/rendering/skull_projection.py src/probe_planner/rendering/scene.py src/probe_planner/project/save_load.py
```

The final one-line slider tracking setting was inspected after that check. No
tests, GUI run, build, broad checks or mechanical simulation were executed.

Ran the production `prepare_reference` pipeline on the previously downloaded
rat/mouse originals using `.venv/bin/python` with
`MPLCONFIGDIR=/private/tmp/atlaxis-skull-mpl`. Regenerated after correcting the
pixel-grid extent. It produced `rat-c59dc0b7e808.npz` (1,150,884 bytes) and
`mouse-10aeae1810b8.npz` (673,384 bytes), installed under the selected
`/Users/yoshi/Documents/Atlaxis/skulls/` without overwriting existing caches.
Visually inspected the two produced `*-dorsal-detail.png` images: actual source
surface detail is visible, without synthetic suture lines. These image checks do
not verify Qt interaction, GPU opening placement, drive rendering or round-trip
runtime behavior. Existing saved plans without the source-detail image continue
to use their stored display surface; their geometry is not silently replaced.

### 3D opacity and laterality explanation — 2026-10-02

The user requested an opaque skull in the main GUI. Changed the skull model,
scene and settings defaults from 65% to 100%; existing saved opacity values remain
editable and are preserved. The separately requested translucent craniotomy image
remains at 72%. Inspected the changed defaults and callers; no execution check or
GUI launch for this small adjustment.

Inspected the Top camera and editor projection to answer the laterality question:
for the current ASR atlas axes, the camera's screen-right vector points toward
anatomical left. The editor now follows that camera, so its left edge is R and
right edge L. This is a display handedness issue, not a change to stored AP/ML
positions. This explanatory follow-up did not change laterality or camera behavior.

### Relative drive controls, edge alignment and appearance — 2026-10-02

The user requests opaque silver drives, gold screws, no editor R/L labels,
English UI and relative parameters based on the probe base's lower-right corner.
Moving a drive must move its attached probe. This supersedes screw omission and
the former tip-relative absolute attachment controls.

1. Derive the represented base shoulder from the most proximal nonterminal
   horizontal ledge; use the base's right bound and mounting face. Where no base
   is represented, use the modeled shank's proximal end and disclose the missing
   geometry. Do not invent a probe package.
2. Default new mounts to the carriage's lower-right corner. Persist a lateral
   mounting offset (legacy default center) and assembly translation offsets in
   probe-oriented mm (legacy zero). UI displacement starts at zero at attachment;
   translating it moves probe and entire drive together. Mount-height changes
   reposition the probe on the stationary carriage; travel moves carriage/probe
   together with fixed-body cancellation preserved. Keep absolute probe-local
   attachment data internal for backward compatibility; provide Align base to
   explicitly reset an existing mount to the new datum.
3. Add lightweight illustrative screws on the fixed assembly, with shaft,
   thread and slotted head; silver drive/gold screw, opacity 1. Cambridge retains
   the supplied 1 mm cap height. Unmeasured screw dimensions are visual assumptions;
   for unknown body height, the screw spans the carriage travel envelope and is
   not a measured body-height substitute. Remove only editor R/L labels.
4. Inspect scoped changes and run at most one lightweight changed-file check.
   Update documentation and this record. No new tests, broad verification or GUI
   launch; preserve unrelated pending changes and existing saved placements.

#### Outcome

- Drive dialog is English. Right/Up/Face offsets start at zero at attachment and
  translate the entire assembly in the probe-oriented basis. Absolute probe-local
  XYZ remains internal. Mount height starts at zero; the lateral mount point
  starts at the carriage right edge. Align base explicitly updates old mounts.
  Changing mount height/lateral attachment repositions the probe on a stationary
  drive. Travel still translates carriage/probe along insertion, not the fixed
  body or screw. Existing values are retained without display-rounding drift.
- Added backward-compatible lateral/assembly-offset fields to DriveMount; saved
  format-4 mounts without these fields use their former center/zero conventions.
  Rendering reuses meshes for pure assembly translations and updates transforms.
- Base datum uses represented polygon shoulders, not contact locations. Inspected
  ASSY-236-H1's explicit common-base shoulder and ASSY-350-H20's shaft-only outlines.
  The latter lacks base geometry: its shank-root right bound is an explicitly
  limited reference, not a manufacturer-verified base edge. No library geometry
  or electrode positions were modified.
- Drives are silver and opaque; gold fixed screws have shaft, helical thread and
  shallow slotted head. Screw shaft radius 0.35 mm, head radius 0.75 mm and thread
  tube radius 0.055 mm are visual assumptions. Cambridge cap height is the user's
  1 mm; the other cap height is illustrative 0.8 mm. Nominal thread pitches use the
  previously recorded 0.25 / 0.282 mm per turn. Unknown body-height screw lengths
  span the moving-arm envelope and do not resolve the missing body dimensions.
- Removed craniotomy R/L labels; A/P and Bregma/Lambda remain. No camera, saved
  opening coordinates or ML sign changes. README updated; unrelated changes kept.

Reviewed the changed source and relevant diff. Algebraically, fixed drive points
have local axial offset `q - mount_height`; the probe's `+delta_q` insertion
translation cancels the fixed points' proximal `+delta_q` offset. Assembly offsets
instead enter the probe pose once, so every attached actor and electrode translates
equally. This is source inspection, not an executed numerical/GUI test.

One lightweight check passed with exit 0; temporary bytecode storage was removed:

```sh
PYTHONPYCACHEPREFIX="$task_check_cache" .venv/bin/python -m py_compile src/probe_planner/implant/drive.py src/probe_planner/ui/drive_dialog.py src/probe_planner/ui/main_window.py src/probe_planner/rendering/scene.py src/probe_planner/ui/skull_dialog.py
```

No tests, GUI launch, rendering run, build, new dependencies, commit or push.
GUI appearance/interaction and screw geometry rendering remain unverified at runtime.

## Rat skull overlap and craniotomy cut faces — 2026-10-02

The user reports posterior brain/skull overlap on a fresh rat atlas, and cannot
see bone thickness at a craniotomy. The screenshots show both the misplaced
posterior surface and a rectangular cut without sidewalls.

1. Correct the recognized WHS default frame using the published 2014 v1.01
   landmark table (Bregma native voxels 246/653/440; Lambda 244/442/464).
   In this application's convention the pitch is atan2(-24, 211), about -6.49°.
   Keep Bregma fixed and apply the existing shared frame to skull/probes/ROIs;
   preserve saved calibrations. Do not resize or deform brain or skull to hide
   residual differences between the Wistar CT and Sprague Dawley atlas.
2. Add cut-face geometry from planar sections of the existing CT bone surfaces,
   preserving inner cavities. Use only closed section contours; do not invent
   thickness for open surfaces. Clip walls to the union boundary of the ROIs,
   including overlapping or touching openings. Circles use the existing 128-edge
   approximation for walls (maximum radial deviation 0.0302% of radius).
3. Cache cut faces by placed surface and ROI geometry; share skull placement,
   visibility and opacity. Rebuild only when openings or skull geometry change,
   keeping the existing shader and lightweight scene for routine probe motion.
4. Update concise documentation and this record; inspect the scoped changes.
   No broad tests or new test infrastructure. Report limitations explicitly.

Diagnostic evidence: a read-only local mesh inspection compared six dorsal rays
through the cached brain/skull and original rat STL. At AP=-8, ML=2 mm, native
brain starts at DV=0.010 mm, cached skull outer/inner faces are 0.122/0.988 mm:
brain lies above the skull. The original STL has the same outer/inner pair at
0.052/1.018 mm, so the discrepancy is not solely mesh reduction. The CT already
contains bone thickness; the current fragment-discard shader never draws its
cross-section. At AP=0, ML=2 mm the original outer/inner pair is 0.216/0.802 mm.
These local samples are diagnostic evidence, not whole-skull registration or
thickness accuracy validation.

Coordinate source: https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf
The 2023 nominal 4° statement remains inconsistent with the landmark table.
This change deliberately uses landmark-based leveling, not an asserted resolution
of that publication discrepancy. Registration to a different individual remains
approximate. No runtime, GUI or post-change numerical verification has yet run.

Cut-face implementation refinement: the first focused reproduction found that
requiring a whole-skull planar contour to be closed rejects all four rectangle
walls because of unrelated holes elsewhere in the mesh. Restrict each section
to its actual ROI edge first, then connect consecutive outer/inner surface
crossings on its two vertical endpoints (even/odd solid occupancy from air).
Do not bridge any gap inside that interval or accept odd endpoint counts. This
uses measured model intersections, not a nominal constant thickness. The first
check's failure is retained; the same rectangle and assertions are used on rerun.

### Outcome and remaining limitation

Implemented the WHS landmark-derived default pitch (−6.4891663959275565°), with
unchanged Bregma, native atlas data, skull scale and saved-plan coordinates.
The existing shared frame also controls probes, ROI projection and anatomical
camera directions. Both recognized WHS packagings use the landmark-based pitch;
the local execution below covers the standard whs_sd_rat_39um v1.2 packaging.

Added cached cut-face actors generated from CT cross-sections, including union
edge splitting for overlapping/touching openings. Wall actors share skull frame,
visibility and opacity and use a slightly lighter bone color. No thickness is
specified or synthesized. Source gaps and odd surface-crossing counts leave an
uncapped edge; Apply status and the Skull tooltip disclose incomplete faces.
Native/saved surfaces and existing opening footprints remain unchanged.

Focused command (one case, rerun once after fixing its initial failure):

```sh
.venv/bin/python -B /private/tmp/atlaxis-rat-craniotomy-check.py
```

The script loads the existing rat cache and native brain display shell, levels
published atlas landmarks, and requests a rectangle AP −6..−3 / ML +1..+3 mm.
The first run failed: 0 cut triangles / 4 incomplete edges. After limiting each
section to the opening interval, the rerun produced 100 cut-face triangles but
2 incomplete edges. **The full-face assertion still fails.** Do not describe
cut-face generation as fully verified or complete; source/contour deficiencies
remain for this actual reference mesh. The unchanged assertion and script are
retained under `/private/tmp` for diagnosis. No third run or broader checks were
performed under the repository verification limit.

Both runs placed atlas Bregma at zero and Lambda at
(−8.2820611565, −0.078, 9.09e−16) mm: leveling and rotation sign are confirmed.
At AP −8 / ML +2 mm the brain surface after correction is DV 0.9281 mm,
compared with skull outer/inner surfaces 0.122/0.988 mm from the initial sample.
This greatly reduces the dorsal mismatch but leaves about 0.060 mm overlap at
that sample; it is not full skull/brain registration or a clearance guarantee.
The reference skull and atlas are different specimens/strains. No deformation,
manual scale tuning or extra offset was applied to conceal that residual.

Scoped source/diff review completed. No application launch, GUI/rendering check,
circle/overlap execution checks, full tests, lint, build or dependency changes.
Unrelated installer notes remain untouched; changes are uncommitted. Remaining
work is reliable cut faces at locally incomplete contours and visual review of
whole-skull correspondence, without inventing anatomical thickness.

## Probe bases and Cambridge side mounting — 2026-10-02

The user reports a drive apparently mounted midway along the shafts, missing 3D
probe bases, and the wrong attachment face. The user explicitly confirms the
Cambridge mounting face is the narrow carriage side, 90° to the previously shown
4 mm fixed-body face. The H20 source contains only four 6.5 mm shafts: treating
its proximal endpoint as a real base was insufficient for this workflow.

1. Represent an optional mounting base separately from shanks, preserving contact
   coordinates and shaft geometry. Persist it in probe geometry. Add sourced
   dimensional envelopes for Cambridge ASSY-236/350 and Neuropixels 1/2. All other
   models can supply width/height/thickness in the same dialog; unknown package
   dimensions must not be invented or replaced by a shaft-root attachment.
2. Build each envelope from the modeled shank/root datum, with a centered lateral
   placement and front surface aligned to the shaft front. These are disclosed
   planning assumptions, not verified package-to-site registration. Use published
   NP Si-spacer thickness by default and allow explicit dimension changes.
3. Anchor on the actual base lower-right/back face. Add editable base dimensions
   and make Align base reposition the drive to that datum without moving electrode
   coordinates. Ordinary offsets/travel keep their assembly-motion contracts.
4. Turn Cambridge fixed-body/screw cross-sections 90° relative to the mounting
   face (2 mm along probe width, 4 mm normal to probe); retain the measured 1 mm
   carriage face and all vertical dimensions/travel. Leave metal-drive orientation
   unchanged. Draw bases opaque and visually distinct from the silver carriage.
5. Perform one focused H20 geometry/assembly check and scoped source/diff review;
   update this record and concise README. No broad tests, generated-library sweep,
   unrelated skull work, commit, push, or dependency installation.

Sources re-inspected: Cambridge catalog PDF pages 10 (side-mount photo), 26–27
(interface chips); NP1/NP2 datasheet page 4 (package dimensions). The manufacturer's
chronic protocol redirects to login and was not accessed. Cambridge ASSY-350 chip
is 2.6 x 7.6 x 0.3 mm. ASSY-236 is 2 x 7.6 mm; thickness is not explicitly called
out in its column, so do not borrow 0.3 mm from a different assembly. NP1 base is
6.2 x 10.7 mm, nominal Si-spacer thickness 1.2 mm; NP2 base/SMD envelope is
3.5 x 14 mm, nominal Si-spacer thickness 1.28 mm. Exact taper, flex, connector and
headstage geometry remain out of scope. Do not imply that all registered models
have manufacturer-verified mounting packages.

Scope refinement: the user requests chronic bases only, with assembly-specific
sizes. Do not add acute package geometry. Known Cambridge acute assemblies are
excluded from new attachments; old attachments remain accessible for detaching.
Unidentified/legacy packages receive no automatic dimensions; manually supplied
dimensions are for a chronic mounting package. NP remains available for chronic
implant planning, with its package-variant assumption disclosed.

Further user refinements: use a common provisional 0.3 mm thickness for Cambridge
chronic bases where thickness is unspecified (including ASSY-236), preserving
assembly-specific width/height and the sourced NP thicknesses. Add dark visible
carriage edges so the moving part is distinct from the silver fixed body. These
edges belong to the carriage mesh and follow its transform/travel.

Implemented: optional persisted `mounting_base`, assembly-specific Cambridge and
NP dimensional envelopes, editable base dimensions, and a lower-right/back-face
attachment datum. ASSY-236 now uses the user-approved 0.3 mm common thickness;
ASSY-79/116/156 still need width, and unidentified packages need width/height.
Known acute Cambridge packages receive no new base or attachment. No published
package dimensions were inferred from electrical channel maps. Base envelopes
are opaque graphite; Cambridge fixed bodies use the side-mount cross-section;
carriages have dark outer edges. Align base reanchors an existing drive without
moving electrodes. Existing custom mounts are not silently reanchored.

Scoped source/diff review completed. One focused check was run:
`.venv/bin/python -B /private/tmp/atlaxis-h20-mount-check-20261002.py`.
Its H20 numerical assertions completed before rendering: 2.6 x 7.6 x 0.3 mm base
at the 6.5 mm shaft root, lower/right/back coincidence with carriage, 2 x 4 mm
fixed-body cross-section, base serialization, unchanged pose on Align base, and
3.75 mm travel of contacts/carriage with stationary body/screw at a tilted pose.
The subsequent application Scene render failed with exit 139 because VTK could
not create a Cocoa OpenGL context. Therefore the overall check did not pass;
carriage edge visibility and the interactive dialog remain visually unverified.
No environment repair, rerun, broad suite, new repository tests, dependency
installation, commit, or push. The temporary reproduction is retained for
diagnosis. Package-to-site registration/taper remain planning approximations;
existing skull cut-face limitations are unchanged by this work.

## Cambridge carriage volume and lower-left alignment — 2026-10-02

The user reports that the carriage is still modeled incorrectly and requests a
separate cuboid with 1 mm thickness, its own length, and lower-left alignment of
the probe base to the carriage. The supplied nano/pico photo and confirmed side
mount mean the mounting face spans the 2 mm body depth; the 1 mm carriage
dimension is its thickness normal to that face, not its face width.

1. Give Cambridge carriages independent dimensions: width 2 mm, thickness 1 mm,
   nano length 7.5 mm and pico length 3.5 mm. Preserve the agreed body heights,
   travel distances and raised lower-edge datums. Metal thickness is unspecified
   and is not inferred from the Cambridge photo.
2. Extrude each Cambridge carriage behind its probe mounting face, then position
   the fixed body and screw behind the carriage's back face plus the saved gap.
   Keep the body/screw fixed during travel and the carriage/probe moving together.
3. Change new attachments and Align base to the base/carriage lower-left corners.
   Preserve electrode poses during explicit re-alignment and retain saved custom
   attachment values until the user applies Align base. Keep carriage edge lines.
4. Update concise documentation, review the scoped edits and run one numerical
   carriage-geometry check without an OpenGL render (previous render failed to
   obtain a context). No broad tests, environment repairs or unrelated edits.

The focused numerical check passed nano but found a pico fixed-screw displacement
of 0.000445 um from regenerating VTK float32 cylinder vertices at each travel
position. Preserve the fixed geometry by generating it at zero travel and applying
the travel compensation afterward in float64. This is a small correction to the
fixed-body invariant, not a tolerance change; rerun the same check once.

User clarification supersedes the lower-left interpretation: the intended corner
is the viewer's left when facing the mount, corresponding to the drive's physical
right. Restore the probe-local lower-right/back datum and +half-width carriage
anchor, with that coordinate convention stated in the UI. The Cambridge cuboid
and motion check passed on the single permitted rerun before this clarification.

The user also requests correcting the 3Dneuro/NP model, whose missing body height
and NP carriage datum caused a face/screw-only display. Re-read the public S/L
specifications and downloaded the pinned v10 body, regular-arm and NP-arm STEP
files linked earlier in this record. Native millimeter VERTEX_POINT coordinates
show a fixed-body envelope of 4.3 x 14.1 x 4.35 mm (local x/y/z), including tabs;
both arm plates span z=4.10..4.75, giving a 0.65 mm main plate thickness. The
raised 0.4 mm-wide side lip and guide/standoff are omitted from the independent
simple plate, not flattened into an arbitrary full-plate thickness. This is a
v10 reference envelope, not a confirmed dimensional match to current R2drive S/L.
Retain the user's regular-arm length/travel/datum and published NP arm size/travel.
Use the public v10 body envelope and plate thickness for visualization, disclose
their source and revision limitation, and preserve explicit saved body heights.
The NP fully-lowered carriage datum was requested from the user; do not equate
it with the regular drive's measured datum without clarification.

Check command: `.venv/bin/python -B /private/tmp/atlaxis-carriage-volume-check-20261002.py`.
The initial run failed only on the pico fixed-screw roundoff described above; the
single permitted rerun passed both Cambridge models, including six-faced 1 mm
carriage volumes, separate body heights, touching rather than overlapping faces,
unchanged probe pose during alignment, and mid/end travel with fixed bodies and
screws. The later coordinate-label clarification and Metal defaults are reviewed
in source only; no additional execution check or GUI rendering was run. STEP
vertex extraction was source-data inspection, not application verification.

Current outcome: Cambridge and regular Metal have independent carriage and body
volumes; all attachment controls use the clarified drive-right/view-left corner.
The Metal body source is disclosed briefly in Dimensions. Opening an older mount
with no body height now pre-populates the source reference height; applying Align
base/Attach saves it. Existing explicit body heights are retained. NP carriage
thickness is corrected, but its body placement remains pending the user's answer
about the fully-lowered carriage edge. Do not report the NP body display as fixed
while its vertical datum remains unspecified. Changes remain uncommitted and
unrelated installer/skull work was not edited.

## Main-panel drive travel and apply/close workflow — 2026-10-02

The user requests closing the craniotomy/drive dialog after a successful Apply or
Attach, moving mechanical drive travel into the left Probe panel, and retaining
only signed vertical mounting adjustment from the drive-right lower corner in
the drive dialog.

1. Close each dialog only after its explicit Apply/Attach succeeds; keep errors
   open and keep existing live mounting previews open while editing fields.
2. Move the bounded travel spinbox/slider to the Probe panel. Use the existing
   assembly-motion function, then refresh the surface-derived insertion depth,
   DV, coordinates and rendered contacts. Hide travel when no drive is attached.
3. Remove the dialog's assembly XYZ offsets and lateral mounting control. Keep
   their saved values internally for old plans; new/Align base mounts use the
   right corner. Replace Mount height with signed Mount offset (+up / -down),
   preserving the saved `mount_height_mm` field and its positive direction.
   Travel stays mechanically bounded; mounting offset is finite but signed.
4. Review these coordinated changes and run one lightweight changed-file syntax
   check. No new tests, OpenGL render, broad suite, extra dependency or commit.

Ordinary probe pose controls keep their existing whole-assembly behavior. The
requested coupling is drive travel -> physical pose -> displayed surface-relative
insertion depth/DV, without redefining saved depth conventions or inventing a
surface when no atlas intersection exists. Prior NP datum uncertainty is separate.

Implemented the four steps. Drive travel has a synchronized 0..model-travel
spinbox/slider in the Probe panel and refreshes the same surface-derived depth/DV
controls used by ordinary pose edits. It is hidden without an attached drive.
The drive dialog preserves existing travel, removes its XYZ/lateral controls,
and permits signed Mount offset. Live edits do not close the dialog; explicit
successful Attach and Apply craniotomy do. Errors leave the dialogs open.
Saved fields/formats and positive mounting direction are unchanged.

Scoped source/diff review completed. The one check run was
`PYTHONPYCACHEPREFIX=/private/tmp/atlaxis-drive-ui-pycache-20261002 .venv/bin/python -m py_compile src/probe_planner/ui/main_window.py src/probe_planner/ui/drive_dialog.py src/probe_planner/ui/skull_dialog.py src/probe_planner/implant/drive.py`.
It exited 0. Interactive Qt/3D behavior and numerical travel/depth coupling were
not executed in this change; no new tests, broad suite or OpenGL attempt. README
updated; unrelated changes retained; work remains uncommitted.

### Screenshot corner clarification pending — 2026-10-02

The latest screenshot identifies a visible lower-left corner, but the silver
extension below the black probe base is the fixed body in the current model;
the carriage lower edge already coincides with the base at zero Mount offset.
Asked whether the intended datum is the lower silver-body corner (approximately
image x=680, y=480) or the current base/carriage lower-edge height (x=665, y=420).
No source changes or execution checks were made for this clarification; do not
flip the lateral coordinate again or change the mounting height before resolving
which physical part/corner the user intends.

### Confirmed fixed-body corner datum — 2026-10-02

The user confirmed the lower silver fixed-body corner, not the carriage lower
edge. Keep the clarified lateral direction; change the vertical reference and,
where body/carriage widths differ, align to the fixed-body lateral edge.

1. Retain stored carriage-relative `mount_height_mm` and existing travel mechanics.
   Display Mount offset relative to the fixed-body bottom at the current travel:
   `offset = mount_height + raised_lower - travel` (mm, upward positive).
   Its inverse is `mount_height = offset + travel - raised_lower`.
2. Make new/Align base mounts use offset zero and the fixed-body half-width,
   allowing that lateral datum when wider than the carriage. Preserve the probe
   mounting face (no interpenetration), existing saved placement until explicit
   re-alignment, and planned electrode pose during Align base.
3. Update dialog precision preservation, labels and documentation. Existing NP
   mounts with unknown body datum retain their stored height; new body alignment
   requires that missing datum rather than silently treating it as zero.
4. Review scoped edits and run one focused non-rendering check of this geometric
   relation, pose preservation and travel. No broader tests or unrelated edits.

Implemented this datum in the drive dialog and documented it in the README.
Stored carriage offsets and travel remain unchanged; the displayed offset now
reports the current base height above the body bottom. Lateral validation accepts
the body edge where wider than the carriage. Unknown NP lower-edge calibration
is not inferred. Existing mounts retain their physical position until Align base.

Focused non-rendering check:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-body-corner-check-20261002.py`
exited 0. H20 geometry with nano, pico and regular Metal passed corner alignment
at zero/mid/full travel and signed offsets -1/0/+1 mm, face contact, unchanged
electrode pose on Align base, and fixed-body/screw invariance during travel.
Unknown NP datum was rejected for new body alignment. Box comparisons allow
0.005 um for VTK float32 coordinates over the checked <32 mm extents; travel
invariance uses 1e-8 um. Scoped source/diff review completed. Interactive GUI
rendering was not run. No additional tests or broad validation; uncommitted.

### Mouse/rat atlas and outline transformation audit — 2026-10-02

The user requested a second check of transformations on the atlas and brain
outline. Read-only inspection followed atlas loading, default/saved frames,
outline and region preparation, scene actors, camera presets, section sampling,
contact mapping, surface intersection, and skull placement. No runtime source
changes were needed for the rigid-coordinate path; no additional execution
checks or GUI validation were run for this audit.

- Recognized Allen v1.2 volumes use Bregma (5400, 0, 5700) um and +5 degrees
  skull-to-native pitch. Recognized WHS standard v1.2 and SWC female v1.0 use
  atan2(-24, 211), approximately -6.489 degrees. Other versions/shapes are not
  silently assigned those presets. Saved frames take precedence; old zero-pitch
  plans are not automatically migrated.
- Annotation/reference volumes, region meshes and brain outlines all remain in
  native atlas physical coordinates. The shared transform maps skull/probes into
  that space; camera axes use the same rotation. Thus the outline does not miss
  a rotation that is applied only to region meshes. No extra mesh rotation is
  required by this rendering convention. Probe-plane sampling, contact lookup
  and surface-depth calculations use that same coordinate frame.
- Orthogonal Coronal/Sagittal textures remain native atlas sections. They are
  correctly positioned in the scene, but coronal sections are not resampled as
  constant skull-level AP planes; the UI labels them "AP at center" under pitch.
- Mouse in-vivo size scaling and nonlinear warping are not implemented. Neither
  atlas brain is rescaled by the pitch correction. CT skull-only uniform sizing
  is separate and does not establish individual skull-to-brain registration.
  This audit confirms the implemented coordinate paths, not anatomical fit or
  equivalence to the full Pinpoint in-vivo transformation.

### Reusable affine alignment and skull-level sections — 2026-10-02

Goal: apply the documented mouse in-vivo scale coherently to atlas/outline,
sample coronal sections at constant skull-level AP (sagittal at constant ML),
and persist the correction and sampled slices for reuse. The prior implication
that nonlinear warping is required was incorrect for the documented Pinpoint
Qiu transform. See [source discussion](../paperflow/atlas-invivo-alignment/discussion.md).

1. Extend AtlasCoordinates with positive AP/ML/DV scale, defaulting to unity for
   legacy plans. New recognized Allen defaults use (1.031, .952, .885). For
   native-axis map O, scale S, pitch R and Bregma b, use
   `atlas = b + O S^-1 R stereo`; preserve the existing rat pitch/unit scale.
   Render brain/outline through `D = M_display inverse(M_atlas)`, where
   `M_display = [O R, b]` is rigid. Render probes/skull using M_display so their
   physical dimensions do not change. Contact/surface queries use M_atlas.
2. Resample sections directly from the original volume on a skull-level grid.
   Use containing voxels for labels and trilinear voxel-center intensity
   interpolation, as in probe-plane sampling. Grid pitch is minimum native
   spacing times minimum scale; no invented nonlinear warp. Keep native sections
   only for an uncalibrated atlas. Update mesh corners, slider ranges, captions,
   camera basis and cache invalidation with the same frame.
3. Persist sampled planes in the atlas cache with source/transform/version keys,
   reuse a bounded in-memory cache during probe motion, and save scale in plan
   version 5 (read versions 1–4 with unit scale). Provide an explicit default
   alignment action for existing plans; preserve probe poses and custom origins.
4. Update UI descriptions/README and inspect scoped diffs. Run one lightweight
   numerical check of affine/render equivalence, resampled constant-AP labels,
   persistence/cache reuse and old-plan compatibility; no broad suites or GUI
   rendering. Label sampling must agree with inverse atlas lookup and display
   points must agree with physical probe coordinates, including boundary cases.

Implemented all four steps for recognized Allen mouse and WHS rat frames. Atlas
surfaces and outline share the corrected display matrix; skull/probes/drives and
camera axes use the rigid physical display frame. Skull-level slice meshes and
their labels/intensity are resampled from native voxels. Probe-plane sampling
uses the same physical resolution rule. Bregma subtraction precedes inverse
rotation to keep the zero-plane index exact. No native dataset was overwritten,
and no nonlinear field or rat size correction was invented.

Plan version 5 persists scale/origin/pitch; legacy plans load with unit scale.
`Settings → Use atlas alignment preset` explicitly adopts the current defaults
while preserving origin and physical poses. `Save & Update` retains them. Bundle
CSV/README also record scale. Disk sections carry atlas source revision and
complete transform keys; a bounded eight-section memory cache avoids repeated
disk reads during probe motion. Changing the frame invalidates active textures,
sampled-section memory and manual indices. The first required section is generated
on demand, rather than building a complete transformed volume at startup.

Verification command (one focused workflow, rerun once):
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-affine-sections-check-20261002.py`

The first run passed mouse and rat Coronal, but its check incorrectly excluded
all rat Sagittal pixels because that entire plane lies on a native voxel face.
Removed this exclusion to strengthen the check: every in-volume pixel, including
exact faces, is compared with its containing native voxel. No source parameters,
data, assertions on IDs, or tolerances were weakened. The same workflow's rerun
exited 0 on the installed `allen_mouse_50um_v1.2` and `whs_sd_rat_39um_v1.2`.

- Exact section label comparisons: mouse Coronal 39,606 pixels / Sagittal 49,209;
  rat Coronal 263,680 / Sagittal 524,290, including voxel faces and outside zeros.
- Constant AP/ML plane geometry, slider boundary planes, independent trilinear
  intensity samples, analytical scale-then-rotation equations, inverse coordinate
  roundtrip, rigid camera bases, and physical probe/display equivalence passed.
- Rat published Bregma/Lambda DV leveling passed. Plan save/reload retained the
  exact transform and poses; version 4 without scale retained unit scale.
  Repeated section loads with the reloaded frame matched arrays exactly and did
  not rewrite cached NPZ files. Temporary caches/plans were cleaned automatically.
- Coordinate tolerance: 1e-8 um for double arithmetic at native extents below
  40,000 um; labels exact; intensity tolerance 4 × float32 epsilon with 1e-5
  absolute allowance. No full-volume resampling or dataset-wide validation.

Scoped source/diff inspection completed. No GUI/OpenGL rendering, full suite,
lint/build, export execution, or independent agent review was run. The helper's
Matplotlib/Arrow imports reported sandbox cache/CPU-query warnings but completed.
10/25/100 um Allen variants and SWC female rat use the same inspected path but
were not executed in this check. Population-average scaling and separate CT
specimens cannot guarantee individual anatomical fit. Work remains uncommitted;
unrelated installer documentation and earlier feature changes are preserved.

## 2026-10-02 — NeuroNexus mounting bases

Goal: show the missing NeuroNexus base as a shared 3D part and use it for the
existing drive attachment, without changing shaft/contact geometry or wiring.
Chronic planning remains the scope; known acute package selections must not gain
an implant base. NeuroNexus array names alone do not identify their package.

1. Inspect manufacturer array drawings and package documentation. Where base
   dimensions are not annotated, derive explicitly approximate width/height from
   the same drawing's labeled shaft length; retain per-model provenance and use
   the previously accepted common planning thickness of 0.3 mm. Do not substitute
   connector dimensions or infer unlisted models from channel count.
2. Add these per-model base envelopes through the existing mounting-base path.
   Preserve saved/custom bases and electrode poses; continue to allow dimensional
   overrides in Microdrive → Dimensions. No cable, connector or headstage model.
3. Carry the selected NeuroNexus package into the mounting eligibility check on
   import, plan/favorite loading and package changes. Hide bases and disallow
   new drive attachments for the registered A64 acute profile; prevent switching
   an attached drive to that profile until detached.
4. Document the estimates and inspect the scoped diff. Run at most one focused
   changed-file check for the newly added base/attachment/package behavior; no
   test infrastructure, full suite, GUI, or broad validation.

Implemented the per-model diagram estimates for all 31 registered arrays under
the existing simplified-model policy, with their approximate status recorded in
the dimension tooltip and [library documentation](../probes/NeuroNexus/README.md#mounting-base-display).
The original numerical shaft lengths, contacts, wiring and insertion poses are
preserved. The base factory, 3D body rendering and drive datum are reused.
Import preview and plan/favorite instances synchronize the selected package;
acute selection hides the base without deleting saved or user-entered dimensions.
Changing to an acute profile while a drive is attached leaves the current
geometry/map intact and reports that the drive must first be detached.

Source: NeuroNexus Penetrating Probe Catalog V2.1, downloaded 2026-10-02; SHA-256
`27881fa444792f145353d81ca0359a272afe4d8f72a88c35bebbc0465d33a5ba` (the library's
existing catalog revision). Each width/height is calculated from the full-array
vector outline and shaft-length extension lines, then rounded to 0.01 mm.
The catalog does not annotate these base dimensions or certify drawing scale.
Unknown physical error, omitted epoxy overhang and approximate registration
prevent mechanical clearance claims. Unlisted models still require dimensions.
No manufacturer drawing/PDF was added to the repository.

Scoped diff review completed. The single permitted changed-file check exited 0:

```sh
python_cache_dir=$(mktemp -d /private/tmp/atlaxis-neuronexus-syntax.XXXXXX)
PYTHONPYCACHEPREFIX="$python_cache_dir" .venv/bin/python -m py_compile src/probe_planner/probes/mounting.py src/probe_planner/probes/model.py src/probe_planner/probes/importers.py src/probe_planner/implant/instance.py src/probe_planner/implant/drive.py src/probe_planner/ui/dialogs.py src/probe_planner/ui/main_window.py
check_exit=$?
rm -rf "$python_cache_dir"
exit "$check_exit"
```

No GUI/OpenGL, drive-motion execution, tests, broad checks or packaging build were
run. Runtime behavior remains unverified. Work is uncommitted; prior feature work
and unrelated installer documentation are preserved.

## 2026-10-02 — Align with the moving carriage corner

The new Buzsaki-5x12 screenshot clarifies that the requested datum is the moving
carriage's lower-left corner as viewed facing its mounting surface, not the fixed
body's bottom. The existing UI converted zero into a negative carriage-relative
height, placing the base below the moving part. This supersedes the earlier
fixed-body interpretation; no hardware dimensions change.

1. Use the persisted carriage-relative `mount_height_mm` directly for Mount
   offset (mm, positive upward); default/Align base = 0. Use arm half-width
   rather than fixed-body half-width for lateral alignment. Keep the base's
   maximum-X, minimum signed-Y, back-face datum (viewer's lower-left).
2. Keep attachment/pose math and saved placement unchanged. Align base explicitly
   repositions an existing drive while preserving electrode pose. Travel moves
   probe and carriage together without changing their relative Mount offset.
   Alignment no longer requires a known fixed-body lower-edge datum.
3. Update the dialog descriptions and README; inspect the scoped diff and run
   one lightweight changed-file syntax check. No new tests or broad validation.

Implemented in DriveDialog and README. New attachments and Align base now use
`mount_height_mm = 0` and `lateral_offset_mm = arm_width_mm / 2`. Source inspection
confirms that the carriage mounting-face corner `(arm_width/2, -height, 0)` maps
exactly to the base attachment datum at zero height. Signed height edits continue
to use the existing pose update, and persisted height/lateral values retain their
original meaning and placement until the user selects Align base. The public
body-offset conversion helpers remain unchanged for compatibility.

Scoped diffs reviewed. The one changed-file check exited 0:
`PYTHONPYCACHEPREFIX="$python_cache_dir" .venv/bin/python -m py_compile src/probe_planner/ui/drive_dialog.py`
where `python_cache_dir` was created using
`mktemp -d /private/tmp/atlaxis-carriage-corner-syntax.XXXXXX` and removed afterward.
No GUI/render or motion execution, tests, or broad checks were run. Runtime visual
alignment remains unverified. Work is uncommitted; unrelated changes preserved.

Follow-up clarification: left/right must also be reversed for the view from the
probe side. Align the minimum-X corner of the probe base with the minimum-X
corner of the moving carriage; use `lateral_offset_mm = -arm_width_mm / 2`.
The zero-height carriage datum remains unchanged. Apply this to new attachments
and explicit Align base, preserving saved placements otherwise. Update descriptions
consistently to say probe-side view. Review these small additional diffs without
running another check, within the task's verification budget.

Follow-up implemented: base reference now selects minimum X, and new/realigned
mounts use the negative arm half-width. Reviewed the changed reference, candidate
construction and documentation. At zero Mount offset the minimum-X carriage
corner has local X `-arm_width/2 - (-arm_width/2) = 0`, placing it at the base's
minimum-X/back/lower attachment point. No additional execution check was run after
this left/right correction; the earlier syntax result predates it. GUI alignment
and motion remain unverified.

## 2026-10-02 — Mouse posterior skull intersection

Goal: diagnose and correct the reported mouse cerebellum/skull intersection,
without concealing it by clipping brain geometry or deforming the CT to fit.
Original and reduced DigiMorph CT cross-sections reproduce the intersection;
the reduced surface's recorded sampled p95 error is 0.037 mm. The Allen preset
uses the opposite pitch direction from the published reference once native
posterior-positive and application anterior-positive axes are reconciled.

1. Establish the sign from published transform and coordinate-space definitions,
   independently of skull fit. Pinpoint's native axes are posterior/right/ventral;
   convert its output to anterior/right/ventral before comparing. Its -5 degree
   native rotation corresponds to +5 degree forward rotation around application
   ML, hence `pitch_correction_deg=-5` in Atlaxis's inverse-lookup convention.
2. Correct the Allen preset for all recognized resolutions. Retain native-axis
   Qiu scale factors, Bregma, transformation order, rat calibration, and physical
   skull/probe/drive dimensions. No estimated warp, size tuning or new atlas data.
3. Retain explicit saved calibrations for compatibility; existing Use atlas
   alignment preset adopts the corrected value and invalidates section keys.
   Document the correction and the existing-plan update path.
4. Run one focused changed-behavior check on installed mouse data, including the
   physical sign oracle, a before/after cerebellum/skull comparison and rendering.
   Report measured remaining mismatch rather than claiming separate specimens
   are anatomically identical. Do not add tests or run broad suites.

The focused check exposed a second problem: the corrected brain still intersects
the independent CT in the inferior posterior region. On 0.1 mm dorsal rays,
external cerebellum exposure changes from 1,506/2,174 rays (+167 rays without CT)
to 0/2,410 (none without CT); however, reduced-CT/cerebellum triangle contacts
increase from 2,237 to 3,688. Contact counts are tessellation-dependent, not an
error metric; they reject a claim of complete anatomical fit. Original full-CT
sections and actual Scene renders agree. Do not hide this residual failure.

The first post-edit check stopped because the offscreen OpenGL context had not
been initialized before Scene's texture setup. After initializing it, the single
rerun completed (exit 0), retaining all comparisons and reported intersections:
`MPLCONFIGDIR=/private/tmp/atlaxis-mpl PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/verify_pitch_fix.py`

The user explicitly authorized additional numerical/3D verification to complete
this specific CT/MRI alignment fix after the normal verification budget was used.
Continue with paired MRI/CT reference investigation; no arbitrary skull warp,
brain clipping, or size fitting solely to eliminate intersections. The published
Henderson/Chan C57BL/6J MRI and whole-skull MINC files were downloaded locally
from https://db.phm.utoronto.ca/surgical.htm for inspection. Gubra/Perens provides
CCF-to-MRI fields, but its archive currently responds HTTP 403 to direct access.

Additional verification outcome (user-authorized scope):

- Allen 10/25/50/100 um metadata cases produce identical physical transforms;
  inverse round trips and rigid probe/skull/drive display frames pass. This is
  a transform check, not a render of four downloaded atlas datasets.
- Full-source CT/cerebellum collision verification finds 6,300 triangle contacts,
  with intersecting cerebellar-cell centers at DV 3.001–6.375 mm. This confirms
  a residual inferior/lateral mismatch even without decimation; triangle counts
  do not measure anatomical error magnitude.
- Paired Henderson MRI/CT and label volumes were read in their MINC physical
  coordinates. A standard affine ICP candidate fitted the MRI-label surface to
  the corrected Allen outline, never using CT overlap as its objective. It was
  rejected for application use: external surface fitting does not establish
  internal anatomy or Bregma/Lambda constraints. No CT replacement or further
  brain/skull scaling was applied. Research details are in
  `paperflow/atlas-invivo-alignment/discussion.md`.
- Published Gubra fields could not be retrieved via direct access (403) or browser
  download (timeouts); Duke's corresponding data portal requires a login. No
  account was created and no message/access request was sent.

Commands actually run, all using `.venv/bin/python` and temporary diagnostics:

```sh
MPLCONFIGDIR=/private/tmp/atlaxis-mpl PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/inspect_paired.py
MPLCONFIGDIR=/private/tmp/atlaxis-mpl PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/paired_affine_candidate.py
MPLCONFIGDIR=/private/tmp/atlaxis-mpl PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/paired_roof.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/verify_resolution_and_contacts.py
```

The first three completed. The final check initially accessed VTK ContactCells
as cell data instead of field data; after correcting the diagnostic, its rerun
completed with the results above. No new repository tests, dependency installs,
full suites or broad checks were performed. Actual Scene before/after renders
and numeric outputs are preserved in the task's visualization directory under
`mouse-skull-alignment/`. Existing saved calibrations still require explicit
Use atlas alignment preset; rat and unrelated work remain unchanged.

Status: the software pitch-sign fix is verified and uncommitted. Full anatomical
alignment is **not complete**. Do not equate dorsal coverage or the rejected
surface-fit candidate with validated CT-to-CCF registration.

User scope update: retaining the model is acceptable if the residual discrepancy
is not substantial. Keep the verified pitch correction and current CT reference;
do not continue replacing datasets or fitting a new deformation for this task.
One final scoped diagnostic sampled 5,000 cerebellum surface vertices against
the original CT from two fixed intracranial ray origins. For points classified
past a first bone pair, nearest-CT distances were median 0.077/0.082 mm, p95
0.301/0.319 mm, and maximum 0.499/0.521 mm. These are sampled surface proximity,
not a maximum registration error or proof of anatomical enclosure. Radial
overrun reached 1.96/2.09 mm; its sensitivity to direction, intervening bone and
natural openings prevents interpreting it as anatomical displacement. The CT
has 288 open edges, and 447/371 sampled rays lacked a bone pair, so those rays
cannot establish enclosure either. Retain the model only as a placement-planning
reference, with the inferior mismatch explicitly unresolved.

Command completed successfully:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python /private/tmp/atlaxis-mouse-fit/measure_remaining_mismatch.py`
Its full output is preserved as `mouse-skull-alignment/remaining-mismatch.json`
in the visualization directory. No further runtime or atlas-parameter changes
were made after this scope update. Scoped source/documentation diffs reviewed.

## 2026-10-02 — Integration and desktop builds

The user approved committing, pushing, merging and building this feature after
shortening the README. Retain the accepted approximate CT reference and the
verified pitch correction; no further registration or geometry changes.

1. Commit the feature, its documentation and a 0.2.0 version bump. Preserve the
   separate uncommitted NP stored-IMRO export work and prior installation note.
2. Push `feature/skull-drive-planning` and merge it into `main` through a PR.
3. Run the existing desktop workflow against the merged commit: macOS arm64 DMG
   and Windows x64 installer, each with matching source. Record build outcomes.

Verification scope is the previously recorded checks, the integration diff and
the explicitly requested installer builds. No new tests or broad audits. Existing
installed apps require replacement/reinstallation; their external data folder
and saved settings must be retained.

Integration outcome: feature commit `caba636` was pushed and merged via
[PR #1](https://github.com/yoshihito-saito/Atlaxis/pull/1). The installer source is
merge commit `50cd7de630dcd3a5d1d4c272a773a07420f6a17b`, version 0.2.0. Local `main`
was fast-forwarded to that commit; the five unrelated dirty files/hunks remain
uncommitted. The staged feature diff was reviewed; `git diff --cached --check`
passed. No additional tests or scientific checks were run for integration.

[Desktop workflow run 37075131147](https://github.com/yoshihito-saito/Atlaxis/actions/runs/37075131147)
completed successfully for both native runners. Both ran `uv sync --locked`,
`uv pip install "pyinstaller==6.22.3"`, and
`uv run --no-sync python -m PyInstaller --noconfirm packaging/Atlaxis.spec`.
macOS ran `bash packaging/build_macos_dmg.sh` (including `hdiutil verify`);
Windows ran Inno Setup with `AppVersion=0.2.0`. Both archived matching source
with `git archive` and uploaded the installer/source artifacts:

- macOS arm64: artifact `11255284193`, 253,122,382 bytes.
- Windows x64: artifact `11256461199`, 160,810,409 bytes.

These are Actions artifacts; no new Release was published. Installed apps were
not replaced, and the newly frozen GUIs were not launched on a physical machine.
Update by quitting Atlaxis, replacing the Mac app from the DMG or running the
Windows installer, and retaining the existing data folder. To opt an older plan
into the current atlas correction, use Settings → Use atlas alignment preset,
then Save & Update. Residual CT/brain mismatch remains as documented above.

### Release publication follow-up — 2026-10-02

The user reported that Releases still showed 0.1.0. Published
[Atlaxis v0.2.0](https://github.com/yoshihito-saito/Atlaxis/releases/tag/v0.2.0)
as Latest, tagged at the exact built merge commit `50cd7de630dcd3a5d1d4c272a773a07420f6a17b`.
The existing 0.1.0 release was retained. Assets are the macOS arm64 DMG, Windows
x64 Setup.exe and matching source ZIP from workflow run 37075131147.

Publication checks: downloaded Actions ZIP sizes and SHA-256 hashes match their
API metadata; both source archives identify the built commit and version 0.2.0.
Their whole-archive hashes differed: inspection confirmed 789 text files differed
only by Windows CRLF versus LF, with all other bytes identical. The macOS LF
archive supplies the release source. All three uploaded release assets match the
prepared sizes and SHA-256 hashes, and `/releases/latest` confirms v0.2.0 with the
complete asset set. Preparation/publication used scoped temporary Python scripts
with the GitHub REST API; no rebuild, source change or new GUI test was performed.
