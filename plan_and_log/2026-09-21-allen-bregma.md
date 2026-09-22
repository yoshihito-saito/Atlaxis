# Allen mouse coordinate initialization

## Goal and scope

Restore probe placement and surface-relative insertion controls for standard
BrainGlobe Allen mouse 10, 25, 50 and 100 um atlases. Currently the default frame
exists only for WHS rat, so Allen returns no frame, displays "No surface" and
omits probes from the scene. Preserve saved/custom frames, WHS coordinates,
probe poses, ML signs and native-voxel surface intersection semantics.

## Steps

1. Add an Allen v1.2 preset restricted to the standard asr orientation, resolution
   and full CCF dimensions. Use the cortex-lab allenCCF estimated Bregma:
   `(5400, 0, 5700)` um in AP/DV/LR array order, independent of voxel resolution.
   Source: https://github.com/cortex-lab/allenCCF/blob/master/Browsing%20Functions/allenCCFbregma.m
2. Identify this preset as estimated in calibration controls. Distinguish absent
   atlas/Bregma from an insertion line that actually misses annotated tissue.
3. Document supported presets and their limits. Inspect the scoped diff and run
   one lightweight check against the installed Allen 100 um volume; record what
   was and was not verified.

## Constraints

The published Bregma estimate is a coordinate convention, not individual-animal
registration; its anatomical error is not quantified by its source. No skull
rotation/scaling correction is introduced. DV and insertion depth still reference
the native annotated surface, not the preset's vertical zero. Do not apply the
adult preset to developmental or other mouse atlases. No atlas downloads, new
tests, broad suites or standalone build in this change.

## Catalogue follow-up scope

The user subsequently requested a rat/mouse-only atlas chooser, removal of
Allen 100 um, and confirmed that only atlases with automatic Bregma should appear.

1. Restrict the common catalogue population path to WHS rat 39 um and Allen mouse
   10/25/50 um with supported v1.2 origins, including downloaded/cache/online names.
   Use the locally loaded version when present; otherwise use the catalogue version.
2. Explain the automatic WHS origin and estimated Allen origin in the chooser.
   Preserve downloaded data, existing-plan loading and Allen 100 um backend support.
   Do not assign adult Allen origins to developmental or other atlases.
3. Update both READMEs, review the scoped diff and run at most one lightweight
   changed-file check. No new tests, atlas downloads or standalone build.

## Outcome

Implemented the guarded Allen preset for all four resolutions, the estimated
origin label/dialog hint, and separate `Load atlas`, `Set Bregma` and `No surface`
states. Updated repository and bundled data-folder READMEs. Saved/custom frames
still take precedence; no rendering/surface algorithm or pose format changed.

Reviewed the scoped source diff. Ran one inline changed-file runtime check with
`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 BRAINGLOBE_CONFIG_DIR=/Users/yoshi/Documents/Atlaxis/.atlaxis/brainglobe .venv/bin/python -B -`.
It loaded the actual installed Allen 100 um v1.2 volume and bundled NP 2.0
four-shank probe. At AP=ML=0, the new frame is `(5400, 0, 5700)` um and the selected
shank's surface entry is stereo `(0, 0, 1.2)` mm. Initial surface-relative depth
and DV are both zero; advancing 1 mm yields depth=DV=1 mm and tip atlas coordinates
`(5400, 2200, 5700)` um. Exit code 0. PyArrow emitted sandbox CPU-cache query
warnings but the atlas/coordinate execution completed.

The installed catalog lists all four resolutions at v1.2. Only 100 um was checked
with a real volume; 10/25/50 um and GUI behavior were inspected, not executed.
No new tests or dependencies, broad suite, rebuild, commit or push. The installed
app and published v0.1.0 remain unchanged; a new build is needed to distribute this
fix. Existing installer-check log edits were preserved. Work is uncommitted.

### Catalogue follow-up outcome

The chooser now admits only WHS rat 39 um and Allen mouse 10/25/50 um at v1.2.
The same filter covers cached, downloaded and online entries; a downloaded
unsupported version takes precedence over a supported online listing and is
omitted. Removed atlases are not deleted, and saved-plan loading is unchanged.
The chooser distinguishes the WHS landmark from the estimated Allen origin.
Both READMEs describe the new selection policy.

Reviewed the dialog/documentation diff and ran the single lightweight check:
`.venv/bin/python -B -c 'import ast; from pathlib import Path; path = Path("src/probe_planner/ui/atlas_dialog.py"); ast.parse(path.read_text()); print(f"Syntax OK: {path}")'`.
It passed. No GUI execution, downloads, new tests, broad suites or rebuild for
this follow-up. Installed/released binaries remain unchanged; work is uncommitted.

Reference comparison: Pinpoint sets atlas-specific reference coordinates and
offers separate atlas transforms (including optional MRI scaling/rotation).
BrainGlobe Atlas API supplies native atlas geometry; its axis convention is not
a universal Bregma landmark. These sources do not justify copying adult Allen
origins to developmental or other atlases:

- https://virtualbrainlab.org/pinpoint/development.html
- https://virtualbrainlab.org/pinpoint/in_vivo_alignment.html
- https://brainglobe.info/documentation/brainrender/usage/using-your-data/registering-data.html

## Waxholm-aligned female rat follow-up

Requested: add `whs_sd_swc_female_rat_39um`; investigate developmental origins and
reported atlas-angle differences. Preserve existing coordinates and axis signs;
do not add an in-vivo rotation/scale correction or unsupported developmental preset.

1. Establish the female atlas grid from the official packaging script, source
   NIfTI headers and released metadata before defining its origin.
2. Add a guarded v1.0 preset and chooser entry, with accurate Waxholm guidance.
   The source grid differs from the original WHS grid, so do not reuse its raw
   voxel vector or metadata transform.
3. Update both READMEs and record the coordinate derivation and research limits.
4. Review the scoped diff and use at most one lightweight changed-file check;
   no new tests or broad verification, rebuild, commit or push.

Evidence: official GIN reference and annotation NIfTI headers both have dimensions
`(1024, 512, 512)`, spacing `0.0390625` mm, and world-coordinate mapping
`(X,Y,Z) = (k*s-9.53125, i*s-24.3359375, j*s-9.6875)` mm. The NITRC landmark is
`(0.078125, 1.171875, 7.5)` mm, hence source indices `(653, 440, 246)`.
The v1.0 packager declares PIR and maps to ASR (AP and DV flip, third axis stays),
with BrainGlobe's 39 um spacing and full-extent point-transform convention.
The resulting packaged origin is `(14469, 2808, 9594)` um. Do not change the
existing male WHS origin `(14469, 2808, 10374)` um. No new numerical approximation
is introduced; the 39 vs 39.0625 um atlas packaging convention is preserved.

Released metadata was streamed from the official archive: v1.0, ASR,
`(1024, 512, 512)`, `(39, 39, 39)` um, no `trasform_to_bg` field. No atlas files
were installed. Upstream PR #716 itself notes uncertainty about the PIR choice;
this preset follows the published packaging, without silently correcting or
claiming to validate the atlas's anatomical left/right convention.

Sources:
- https://github.com/brainglobe/brainglobe-atlasapi/blob/3cc01d389d2f37852b3b4c3675f9945cd5889706/atlas_scripts/whs_sd_swc_female_rat.py
- https://github.com/brainglobe/brainglobe-atlasapi/pull/716
- https://gin.g-node.org/BrainGlobe/swc_rat_atlas_materials/src/master/packaging/Waxholm_space_39um
- https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf

### Female rat outcome and remaining limits

Added the v1.0 preset, whitelist entry and chooser explanation; both READMEs
describe the female template and distinguish origin setting from skull leveling.
Existing saved frames and all other presets are unchanged. Scoped diff reviewed.
The single lightweight changed-file check passed:

```sh
.venv/bin/python -B - <<'PY'
import ast
from pathlib import Path
for name in ('src/probe_planner/atlas/coordinates.py', 'src/probe_planner/ui/atlas_dialog.py'):
    ast.parse(Path(name).read_text())
    print(f'Syntax OK: {name}')
PY
```

No runtime/GUI or anatomical left-right validation was performed. No new tests,
full atlas installation, build, commit or push. Source changes remain uncommitted;
unrelated installer-check log edits remain untouched.

Developmental research: DeMBA maps brain anatomy across P4–P56, but the reviewed
paper provides no Bregma/Lambda skull calibration. ADMBA reconstruction metadata
likewise does not establish a verified skull origin for the reviewed P28 use case.
No adult-origin substitution is justified. Allen-derived Kim and BlueBrain barrel
atlases are future candidates, subject to separate packaged-grid checks.

Angle report: Pinpoint documents about 5 degrees of pitch between Allen CCF and
a Bregma/Lambda-leveled skull, with separate Qiu/Dorr scale/rotation presets.
The previously supplied Pinpoint issue #856 concerns Waxholm 78 um lateral
misalignment, not a confirmed pitch error; its maintainer attributes it to the
atlas, which does not prove any particular 39 um atlas is unaffected.

- https://www.nature.com/articles/s41467-025-63177-9
- https://brainglobe.info/documentation/brainglobe-atlasapi/usage/atlas-details.html
- https://virtualbrainlab.org/pinpoint/in_vivo_alignment.html
- https://github.com/VirtualBrainLab/Pinpoint/issues/856

## Allen skull-level pitch correction

The user now requests correction of Allen CCF's approximately 5-degree pitch and
explicitly states that no existing-plan compatibility or migration is needed.
Apply the rotation to coordinates, not only the camera. Keep the existing Allen
Bregma estimate and native resolution; do not add Qiu/Dorr anisotropic scaling.

1. Store a finite `pitch_correction_deg` in `AtlasCoordinates`; Allen presets use
   5 degrees, other presets use zero. With `s=(AP anterior, ML right, DV ventral)`,
   atlas position is `b + S @ Ry(+5 degrees) @ s`, where S is the existing signed
   axis permutation. The inverse maps native atlas coordinates to the level-skull
   frame. This is the inverse of Pinpoint's pitch-only native-to-skull rotation.
   One millimeter ventral maps to ASR displacement `(-sin(5), cos(5), 0)` mm.
   Distances, Bregma and ML are invariant. Five degrees is a published nominal
   correction, not individual-animal registration; its uncertainty is not estimated.
2. Use the transformed vertical ray for brain-surface placement. Probe transforms,
   contact lookup and probe-plane sampling already consume the common matrix.
   Align camera presets/cube with the skull frame; native coronal/sagittal slices
   stay native (no resampling) and identify coronal AP at the slice center.
3. Preserve the rotation when editing the Bregma origin. Show correction status,
   save it in the existing dataclass-based plan JSON, and describe the frame in
   planning CSV/README output. Keep application READMEs focused on usage, as
   requested; retain calibration provenance here. No legacy migration.
4. Review the scoped diff and run one lightweight coordinate check using the
   installed Allen volume, checking sign, inverse, distances and native surface
   intersection. No new tests, broad suites or rebuild.

Oracle: https://virtualbrainlab.org/pinpoint/in_vivo_alignment.html and
https://github.com/VirtualBrainLab/BrainAtlas/blob/main/Packages/vbl.brainatlas/Scripts/Runtime/CoordinateSystems/AffineTransform.cs
(Pinpoint Qiu2018 uses rotation `(0,-5,0)` in native-to-transformed space; its
scaling is deliberately outside this request.)

Developmental follow-up is limited to BrainGlobe atlases. The reviewed P28
DeMBA/ADMBA sources do not establish a packaged-grid skull landmark, so no
developmental preset is added. The separate Johns Hopkins MRI/CT atlas is outside
this scope. Remove the detailed atlas/calibration paragraph from both user READMEs.

### Pitch correction outcome

Implemented the shared rigid 5-degree Allen correction, with no scale change or
legacy-plan migration. Surface initialization now follows the corrected vertical
ray through native voxels. Probe/contact/probe-plane transforms use the same
matrix. Camera presets and cube faces/picking follow corrected axes; native
sections remain native and the coronal caption specifies AP at its center.
Editing Bregma retains pitch. Plan JSON persists the dataclass field; coordinate
CSV and bundle metadata record its value. Both user READMEs now give only a short
atlas-selection instruction. No developmental preset was added.

Scoped diff reviewed. Ran one inline coordinate check using:
`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 BRAINGLOBE_CONFIG_DIR=/Users/yoshi/Documents/Atlaxis/.atlaxis/brainglobe .venv/bin/python -B -`.
It loaded the installed Allen 100 um v1.2 volume (still excluded from the chooser)
and passed pitch-sign, orthonormality, fixed-Bregma, inverse/distance, JSON
round-trip, edited-origin pitch retention and camera-axis assertions. Matrix
tolerance was 1e-14; transform-coordinate tolerance was 1e-10 um and surface-ray
tolerance was 1e-10 mm, allowing ordinary floating-point roundoff. Three actual tissue crossings were checked using points
1e-6 mm on either side of the computed surface, confirming outside then inside:

- AP/ML `(0, 0)` mm: surface skull DV `1.20458381` mm.
- AP/ML `(-3, 1)` mm: surface skull DV `-0.06170202` mm.
- AP/ML `(2, -1)` mm: surface skull DV `1.68070708` mm.

The entry stays unchanged when advancing the ray origin 1 mm along its axis;
an ML=50 mm ray correctly misses tissue. Exit code 0. Matplotlib used a temporary
font cache and PyArrow printed sandbox CPU-query warnings; neither blocked the
check. No new test files, broad suite, GUI execution or app rebuild. Allen 10/25/50
um were not loaded; the correction is shared across resolutions. Anatomical
accuracy of the nominal 5-degree correction was not measured against individual
animals. Source changes remain uncommitted and installed binaries are unchanged.

## Rebuild and release update

The user authorizes commit/push, rebuilding both desktop installers and updating
the existing release while keeping version 0.1.0.

1. Commit the atlas fixes, concise READMEs and this record; preserve the unrelated
   local installer-check note. Push the source revision to main.
2. Dispatch the existing native macOS/Windows workflow for that revision and
   require both builds to succeed before replacing release downloads.
3. Replace v0.1.0 installers and matching source archive, align the release tag
   with the build revision, and update release notes with the exact build identity.
   Record final artifact verification and remaining installation limits here.

### Release update outcome

Committed the atlas changes as `10b02abba71707e468b2d3058b308bb041e84cb3` and pushed
main. Dispatched `build-desktop.yml`; [run 35674414926](https://github.com/yoshihito-saito/Atlaxis/actions/runs/35674414926)
succeeded on macos-14 and windows-2022. Artifact IDs are 10671579642 (Mac) and
10672791991 (Windows). Verified downloaded archive SHA-256 hashes and both source
ZIP commit comments against the build SHA, then verified all uploaded asset
sizes/digests against their local files before replacing the old downloads.

Updated [v0.1.0](https://github.com/yoshihito-saito/Atlaxis/releases/tag/v0.1.0)
with `Atlaxis-macOS-arm64.dmg`, `Atlaxis-Windows-x64-Setup.exe` and the matching
macOS-produced `Atlaxis-source.zip`. Moved only the v0.1.0 tag using an explicit
force-with-lease against its previous `dfc1bb5` revision; branch history was not
rewritten. Release notes identify the rebuild and exact source revision. A final
API read confirmed the published state, expected three filenames and their
hashes/sizes. Application version remains 0.1.0. Installed apps were not replaced
and these rebuilt installers were not interactively installed or GUI-tested.
The unrelated local installer-check note was left untouched and uncommitted.
