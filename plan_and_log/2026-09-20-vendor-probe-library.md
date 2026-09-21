# Manufacturer probe library

## Per-probe XML / CellExplorer companions — 2026-09-20 (uncommitted)

Goal: assign the requested provisional A6x21 Channel IDs and provide XML and
CellExplorer coordinate companions for every manufacturer, including the normal
NeuroNexus XML files in ayalab1/ProbeMaps.

1. Confirm CellExplorer indexing/units and inspect the pinned ProbeMaps XMLs;
   exclude version2, reversed, opposite and flipped variants.
2. Assign A6x21 provisional IDs from zero, left-to-right shanks and tip-to-base
   sites within each shank. Keep geometry and confirmed wiring unchanged.
3. Generate per-model companion folders with per-connection XML and chanCoords
   MAT files for confirmed wiring, with A6x21 the only provisional-ID exception.
   Keep existing JSON locations/favorites compatible. NP coordinates belong in
   the planning bundle after channel selection, not a static all-site map.
4. Preserve source XML bytes and provenance without inferring missing coordinates
   or reinterpreting group order as a verified spatial map. Document limitations,
   inspect scoped diffs and run one focused export round-trip check.

Scope clarified: all NeuroNexus, Cambridge and Neuropixels library models.
Latest clarification: do not add unconfirmed NeuroNexus models. Use normal
ProbeMaps XMLs plus manufacturer coordinates where their spatial correspondence
can be established; unresolved source models remain reference-only. Do not infer
NP routing before selection. Existing poses and NP selection semantics are unchanged.

Completion:
- A6x21 now defaults to explicitly provisional IDs 0-127, with shank ranges
  0-20 / 21-41 / 42-64 / 65-85 / 86-106 / 107-127. Its import preview and
  companions identify these as user-requested placeholders. Geometry is unchanged.
- Pinned ProbeMaps revision `c50ba8f23a634e9513507b6843703413af175f16` in
  `third_party/probemaps.lock.json`. Its generator documents base-to-tip spatial
  XML order; the A5 CSV independently supports this order. Preserved seven source
  XMLs byte-for-byte after git-blob validation, excluding version2, reversed,
  opposite and flipped variants. No default acquisition settings were inferred.
- Added A1x32-Edge-5mm-20-177 (catalog p41) and A4x16-Poly2-lin-5mm-20s-150-160
  (p92, XML alias cross-referenced to OA64LP V2 map p4). Added explicit
  `ProbeMaps normal XML` profiles to these and existing A4x16-poly2-23s / A5 Buz-Lin.
  Kept confirmed manufacturer/headstage profiles separate. The new Edge model's
  lateral tip registration is undimensioned and marked provisional (unknown error).
- Generated 205 sibling model folders and 172 connection-specific XML/MAT pairs.
  58 previously unassigned models (57 Cambridge, one NeuroNexus) have explanatory
  README files without fabricated channel maps. Existing JSON paths/favorites are
  unchanged. No all-site NP map is generated. The two unresolved source model names
  (`64_HPC_curvature`, `A4x16-Lin-5mm-50s-300`) and combined Poly3+Buz-Lin XML remain
  source-only references; neither geometry nor an acquisition coordinate map was guessed.
- Added shared channel-companion serialization. MAT rows retain device-channel
  positions with one-based `channel`, local XYZ in um, zero-based shanks and NaN
  for unassigned inputs. XML orders sites base-to-tip within shanks. Partial maps
  are never compacted or filled. The existing finite-only MAT importer is unchanged;
  use the geometry JSON in Atlaxis for profiles with NaN/unassigned inputs.
- Save & update writes selected NP XML/chanCoords into the existing planning
  bundle; reset/removal clears only obsolete managed companions on the next save.
  Per-probe MAT retains local IDs plus combined XML offsets. Manual IMRO/CSV exports
  remain untouched. Added binary staging alongside existing text outputs.
- Regenerated using `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
  probe_planner.probes.catalog --manufacturer NeuroNexus` and
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m probe_planner.probes.companions
  --probemaps-source-dir /tmp/atlaxis-probemaps`. The first companion generation
  stopped on Cambridge's `.manifest.json`; excluded hidden metadata files and
  regenerated successfully. Re-ran generation after preserving spatial XML order.
- One focused read-back check ran with `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -`
  (inline): serialized the existing `planning/260920_NP1_test/implant_plan/plan.json`
  selection, then parsed the XML/MAT. Passed 324/384 native indices, all XYZ/site/shank
  associations, 60 unassigned inputs, XML skip flags, a combined-XML offset, and
  preservation of the input map. This check read but did not modify the saved plan.
  Scoped source/data/document diffs reviewed. No full suites, new tests/dependencies,
  hardware/CellExplorer GUI validation or end-to-end Save/reset GUI run; no commits.

## NeuroNexus 64/128-channel wiring and A6x21 correction — 2026-09-20 (uncommitted)

Goal: add source-verifiable 64/128-channel NeuroNexus connection profiles and
correct which A6x21 shanks carry the additional sites.

1. Inspect the official 64/128-channel package maps and catalog diagrams;
   identify physical sites, connector/revision conventions and actual channel IDs.
2. Correct A6x21 geometry from the drawing and register supported package/recording
   profiles using the existing selection mechanism. Do not substitute connector
   pins for acquisition channels or infer undocumented layouts.
3. Regenerate only affected NeuroNexus files and expose unavailable connections
   and source links in the existing import preview. Keep saved plans unchanged.
4. Inspect scoped diffs, perform one focused changed-file check, and document
   confirmed coverage and remaining source limitations.

Scope (confirmed by user): also add other 64/128-channel models whose physical
geometry and channel maps can be established from official documentation;
defer models without channel maps. A6x21 geometry must still be checked.
No new channel counts,
unrelated vendor edits, broad tests or dependency changes.

Completion:
- Added 24 models (17 with 64 channels, seven with 128 channels), each with a
  source-backed recording connection. The library now has 29 models, including
  26 with selectable wiring. Existing unmapped models remain available; no new
  unmapped model was added. A6x21 remains the requested geometry-only exception.
- Corrected A6x21's two extra proximal sites to Shank 2, third from the left in
  the electrode-facing catalog drawing (page 119). Counts are now
  21 / 21 / 23 / 21 / 21 / 21; all other coordinates are unchanged.
- Registered Activus 64/128 recording maps, H64LP with SmartLink64 Chronic or
  Intan RHD64, and A64 with SmartLink64 Acute where matching spatial maps exist.
  Import and coordinates use the existing selector, labeled Package / headstage.
  Source pins remain metadata; exported Channel IDs are zero-based amplifier
  channels. Unassigned is retained until the actual connection is selected.
- Stored source PDF URLs, hashes, pages, spatial numbers and connector orientation
  in `third_party/neuronexus_wiring.json`; added an offline generator extension.
  Regenerated only NeuroNexus with `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
  -m probe_planner.probes.catalog --manufacturer NeuroNexus`. Generation completed
  with strict shank/site-count and complete channel-permutation validation.
- Reviewed scoped source/data/document diffs. One focused check ran with
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  MPLCONFIGDIR=/tmp/atlaxis-current-wiring/mpl .venv/bin/python -` (inline).
  Passed Buzsaki64L import connection switching: first two site channels were
  53/50 for Intan, 52/51 for SmartLink Chronic, and 57/56 for SmartLink Acute;
  each map covered 0-63 exactly. Source links, selection clearing and preservation
  of the original input map also passed. Qt emitted a font-alias warning.
  No new tests, broad suites, dependencies, commits or pushes.
- Limits: no hardware verification; other package/headstage chains and unresolved
  Poly5 revisions remain deferred. Existing Buzsaki-5x12 and A5 Buz-Lin 5mm
  recording routes remain unassigned with import explanations. Edge lateral
  pad-center registration remains explicitly provisional with unknown error;
  shaft silhouettes remain schematic. Old saved plans are not migrated; re-import
  to obtain corrected geometry/profiles. Coverage is documented in
  `probes/NeuroNexus/README.md`.

## Current Cambridge external-headstage coverage — 2026-09-20 (uncommitted)

Goal: register all source-verifiable current Cambridge wiring configurations in
the existing library; identify unsupported wiring at import and always remind
users to check Channel ID against physical Site using their actual documentation.

1. Trace current ASSY-1/37/77/79/116/156 physical site layouts through official
   probe, adapter and Intan RHD pinout documents. Preserve explicit revisions,
   connector orientation, source IDs and zero-based amplifier channel numbering.
2. Add source-backed selectable headstage profiles without guessing unsupported
   configurations or changing geometry. Preserve existing fixed/Mini-Amp profiles.
3. Show unsupported/unassigned wiring and a persistent source-check reminder in
   the import preview, updating status when the headstage selection changes.
4. Regenerate affected library metadata, document coverage and limitations, inspect
   scoped diffs, and run at most one focused changed-file/import check.

Scope: current entries in the existing library. Discontinued/old entries and
unidentified variants remain explicit holdouts. No hardware validation or new
geometry; no broad tests or dependency installation.

Completion:
- Added all 61 current, identifiable ASSY-1/37/77/79/116/156 library entries
  using 45 official probe maps, three Cambridge adapter maps and Intan User
  Guide figures 5/11/17. Stored PDF hashes, physical spatial tables and six
  named connection permutations; converter composes pins into offline profiles.
  Existing 53 profiles remain unchanged (114 supported entries, 57 holdouts).
- Passive models require the actual headstage selection. RHD 16ch C3334/C3335
  retains native inputs 8-23 in a 32-input namespace, including in exports.
  ASSY-156-M1v2 source Sites 5/6 correspond to official connector pins 6/5;
  preserved source geometry/IDs and corrected only their routing correspondence.
- Added unsupported-wiring reasons, an always-visible Channel ID / Site check
  reminder and manufacturer document links in the import dialog. Selection
  changes update the connection note and existing contact tooltips. NP imports
  refer to active maps/IMRO rather than being labeled unsupported.
- Regenerated with `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
  probe_planner.probes.convert_cambridge --source-dir
  /tmp/atlaxis-probeinterface-bb40894c` (171 files / 10,765 sites; twice, the
  second run normalizing the new source URLs). Generation's existing pinned-blob,
  site-coverage, channel uniqueness/range checks passed before writing.
- One focused check: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  MPLCONFIGDIR=/tmp/atlaxis-current-wiring/mpl .venv/bin/python -` (inline).
  Passed the ASSY-1-E-1 import/select/unassign/cancel flow: official adapter
  endpoint routing (pins 1/16 -> native inputs 22/15), input range 8-23,
  namespace size 32, persistent reminder, source link and immutable input map.
  Inspected its captured preview and scoped source/data/document diffs.
  Qt emitted standard offscreen/font messages; no new tests or dependencies.
- Updated coverage documentation. No geometry edits, old-plan migration,
  broad tests, hardware validation, commits or pushes. Existing plans need
  re-import to obtain new profiles. Unidentified/legacy variants and other
  headstage brands, adapter brands or dual-headstage configurations remain
  unassigned rather than receiving an inferred map.

Goal: provide the ten requested NeuroNexus, Cambridge NeuroTech and Neuropixels
designs as importable files with full shanks and source-backed physical sites.

1. Read manufacturer dimension drawings and the local pyNeuroscope XML references.
   Resolve model aliases, site counts, tip offsets, pitch, shaft length/thickness
   and front/back faces. XML channel groups alone do not establish XYZ or wiring.
2. Create `Probe file/NeuroNexus`, `Probe file/Cambridge NeuroTech` and
   `Probe file/Neuropixels`. Generate the existing JSON geometry format, recording
   sources, physical site IDs and explicit body/packaging approximations. Never
   invent unknown coordinates or equate site IDs with acquisition channels.
3. Make the import chooser start in that library; retain staged import and the
   existing coordinate/plan contracts. Show material geometry/routing notes in
   preview. Include all Neuropixels sites; bank selection remains deferred.
4. Replace the pilot-only probe examples after usable manufacturer replacements
   exist; update affected references/documentation without changing saved plans.
5. Review the scoped diff and run one focused library-load check. Record source
   discrepancies, unsupported variants, verification and any remaining work.

No acquisition routing will be guessed from XML group order. Unspecified
mechanical packages are not implant collision models. No broad tests or commits.

Source decisions: official catalog drawings establish nonuniform layouts:
A5x12-16 has a 6.2 mm central shaft among 5 mm shafts; Buzsaki 5x12 has four
additional central sites. The initial A6x21 interpretation placed two additional
proximal sites on the leftmost shaft; the correction above places them on the
third shaft (128 physical sites total). H20 has 31 clustered sites plus one
remote site per shaft. E-1 ASSY-350 is the four-shank, double-sided 128-site
assembly (6 mm, 30 um). Standard H20 is 6.5 mm, single-sided, 128 sites.

Missing drawing dimensions cannot be presented as manufacturer measurements.
For A6x21's tip offset (~35.5 um), H20's tip offset (~22.5 um) and E-1's taper
coordinates/tip offset (~22.5 um), use explicitly provisional catalog digitizing.
Nominal spacings remain dimensional constraints; x/y drawing scale is calibrated
separately where necessary. Reading repeatability is approximately 2–5 um, not
a manufacturing tolerance; actual uncertainty is unknown. E-1 back-face mirrored
registration is provisional. Flag these in files and import preview. Shaft
silhouettes interpolate dimensioned widths and are schematic, not certified CAD.
Do not use the public probeinterface H20/E-1 JSON unchanged: H20's 165 um span
and E-1's 9 mm contour contradict the current manufacturer drawing.

Neuropixels 2.0 uses commercial NP2003/NP2013 dimensions, including the
asymmetric column centers 27/59 um from the left shaft edge (ProbeTable).
The official manual specifies a 175 um taper but does not dimension the first
site center. Use a provisional 200 um tip offset, explicitly flagged; this
is confirmed for NP1 by the cortex-lab electrode-layout documentation, not NP2.
ProbeTable's 206/209 um `tip_length` differs from the manufacturer's 175 um
taper specification and is not silently substituted for a site-center offset.
All entries remain physical-site libraries without inferred hardware routing.
When routing is absent, the summary will label its first column Site ID.

## Completion — 2026-09-20 (uncommitted)

- Added ten JSON layouts under the three requested manufacturer directories,
  generated by `src/probe_planner/probes/catalog.py`. Provenance and provisional
  dimensions are embedded and documented in `Probe file/README.md`.
- Import starts at the library; preview shows thickness, dimension limitations
  and E1 face selection. Unmapped tables use physical Site ID. Existing mapped
  plans keep Channel ID and saved geometry/poses are unchanged.
- Removed the two pilot geometry files and their obsolete example channel XML;
  replaced the unused default-probe loader with library path discovery. Added
  wheel inclusion of the library. No manufacturer PDFs/XML were redistributed.
- Executed `.venv/bin/python -m probe_planner.probes.catalog` to produce files.
- One permitted focused verification: `.venv/bin/python -` with an inline
  library-load assertion check. Passed all ten files / 8,000 unique physical
  sites, expected shank/site counts, face z coordinates, sites within shaft
  length, A4 row/column spacing, A5 central tip/length/site pattern, Buzsaki
  extra sites, A6 proximal sites, H20 cluster/remote distances, E1 front/back
  counts, NP column/row/shank pitches and 384-channel unassigned routing.
  This verifies implementation of the stated layouts, not accuracy of digitized
  manufacturer drawings. No permanent tests or broad suites were added/run.
- Reviewed source and the task-only diff against pre-edit snapshots. GUI
  interaction and wheel building were not run; face controls and packaging
  were inspected in source. No commits or unrelated code edits.

Remaining: manufacturer confirmation of flagged tip offsets, H20 remote gaps,
E1 taper coordinates/back-face registration; certified mechanical outlines;
hardware wiring and NP bank selection. Standard Cambridge variants were used
as stated because no alternative dimensions were supplied. Preserved arbitrary
JSON/MAT import and saved-plan support.

## Cambridge maps and import simplification — 2026-09-20

Goal: import from `probes/`, simplify the preview, and assign Cambridge channels
from the manufacturer's digital 128-channel maps. The user approved correcting
E-1's assembly name to ASSY-325D. Existing saved plans remain unchanged.

1. Read and visually inspect the official ASSY-350 H20 and ASSY-325D E-1/E-2
   maps (both dated 2024-07-01), including shank order and both E-1 faces.
2. Use a fresh chooser rooted at the library. Remove mapped count, face selector
   and explanatory paragraphs from preview; retain provenance in files/docs.
3. Encode the documented zero-based Intan/Open Ephys channel assignments and
   face registration; regenerate only Cambridge JSONs and replace the misnamed
   E-1 file. Keep dimension uncertainty explicit where maps lack measurements.
4. Review the scoped changes, perform one lightweight Cambridge library check,
   and document results and remaining dimensional/GUI limitations here.

The channel maps are wiring oracles, not dimensioned mechanical drawings. H20
uses A-to-D electrode-facing schematic order; E-1 uses D-to-A common front
projection shown for both faces. Tip offsets and remote gaps retain their
previous provisional status. No new tests, dependencies, or broad validation.

Follow-up scope: the user requested a scale bar after viewing H20. Add a small
viewport overlay to the import preview, using the actual scene-to-screen scale
and adaptive 1/2/5 lengths in um or mm. It must not affect fitting or geometry.

Completion (uncommitted):
- Replaced the native import chooser with an explicitly rooted Qt chooser;
  simplified the preview as requested and added its adaptive scale overlay.
- Replaced the misnamed E-1 library entry with ASSY-325D. Added complete official
  0–127 channel routing to E-1 and H20. Interpreted E-1's identical D-to-A table
  order on both faces as a shared projection, removing the extra back-face
  mirror. Exact lateral registration remains provisional, not measured CAD.
- Regenerated only the two Cambridge JSONs using `.venv/bin/python -` with
  `build_catalog()` filtered by manufacturer; other vendors/plans untouched.
- One focused check ran with `.venv/bin/python -`: loaded both JSONs through
  the public importer, validated maps, and compared every shank/face's spatial
  row order against separately transcribed top-to-bottom official PDF tables.
  Both passed: 128 unique channels each, complete 0–127 coverage; E-1 lateral
  alternation and front/back registration also matched the stated convention.
- Reviewed source and generated-file diffs against pre-edit copies. Scale bar
  received source/diff inspection only; no GUI execution or broad suites run.
  No new tests, dependency installation, commits, or original PDF distribution.
- Remaining: dimensional estimates noted in JSON/README, physical hardware
  validation and interactive GUI confirmation. Saved plans need re-import to
  use corrected library geometry/routing; no automatic migration was performed.

## Complete Cambridge snapshot — 2026-09-20

Goal: prepare every Cambridge model in ProbeInterface as offline Atlaxis JSONs,
using upstream data only during generation. No new runtime dependency or GUI
feature. Preserve the existing H20/E-1 geometry and wiring corrections.

1. Pin library commit `bb40894cdf55787fed7b7198ea854497d52ca687`; inspect
   upstream coordinate, outline, shank/face and routing conventions.
2. Add a development conversion command using the library JSON snapshot,
   retaining IDs/provenance and separating physical geometry from acquisition
   wiring. Normalize the physical tip using supplied contours. Document missing
   dimensions and any necessary display approximation explicitly.
3. Generate all Cambridge entries under their upstream model names, preserve
   the two curated corrections, remove their obsolete duplicate filenames,
   and include the source revision, manifest and MIT attribution.
4. Inspect the scoped diff and perform one lightweight conversion check;
   document results and unverified manufacturer/GUI behavior. No new tests,
   broad suites, environment changes or commits.

Inspection decisions: all 171 inputs are 2D micrometer layouts with contours
and unique site IDs; none has acquisition-channel indices or shaft thickness.
Seven mark front/back faces. Some omit shank IDs, and H12 incorrectly labels
two outlined shafts as one. Recover physical shanks from the contour's sharp
tips in x order; partition the supplied contour at inter-tip midpoints, retaining
the original outline and contact x/y after one tip-origin translation. Preserve
unequal tip heights. Use explicitly nominal 15 um / 30 um extrusion for single /
double-sided displays (site z = +/- half thickness); exact thickness error is
unknown. Do not reinterpret contact IDs as channels. Preserve upstream 63-site
variants as supplied. Record these limits in each file and the library README.
Read the upstream JSON directly during generation; the ProbeInterface Python
package itself is unnecessary. Keep a pinned file/hash lock for reproduction.

Completion (uncommitted):
- Generated all 171 locked models / 10,765 sites in `probes/Cambridge NeuroTech`.
  Added `convert_cambridge.py`, a source-file/hash lock, hidden model manifest,
  MIT license and regeneration/limitation documentation. No runtime dependency
  or application import path changed. Upstream JSONs remain in a temporary cache.
- H20/E-1 now use canonical `ASSY-350-H20` / `ASSY-325D-E-1` filenames; their
  old duplicate filenames were removed. Both retain their corrected contacts,
  bodies and channel maps. Other vendors and saved plans were not modified.
- Generation command (passed): `.venv/bin/python -m
  probe_planner.probes.convert_cambridge --source-dir
  /tmp/atlaxis-probeinterface-bb40894c`. Generation checks pinned source blob
  hashes and validates constructed geometry/maps before writing any models.
- One lightweight changed-file check ran with `.venv/bin/python -` (inline).
  Passed: manifest/output filenames cover all 171 locked names; six representative
  models retain source x/y, IDs and outline area; H12 has two shanks, P-1 retains
  both faces, H15_2 retains 15 um tip stagger, F8-0 has eight shanks, and H3 keeps
  63 sites. The two curated models' geometry fields and channel maps compare
  exactly with their pre-task files. Numerical tolerances derive from float64
  precision and coordinate/area calculation scales, not tuned fixtures.
- Reviewed the converter, scoped existing-file diffs, generated metadata and
  source lock/manifest. No permanent tests, broad suite, GUI execution, full
  manufacturer dimensional audit, wheel build, or commit was performed.
- Remaining limitations: 169 entries have no acquisition wiring; source lengths
  and tip locations remain unverified, and thickness/face-z are nominal. These
  are documented in JSON metadata and the Cambridge README. The development
  downloader path was inspected, while generation used the already downloaded
  fixed-revision cache. Existing plans continue to use their embedded geometry.

## Favorite probes and official wiring — 2026-09-20

Goal: persist frequently used probe definitions behind a yellow tab star and a
Favorite probes import menu; register Cambridge wiring from official maps.

1. Inspect tab/import/store integration and manufacturer maps. Clarify external
   headstage routing while proceeding with unambiguous built-in Intan assemblies.
2. Add a persistent favorite store and tab stars/menu. Favorites hold model
   templates, never implant coordinates or Neuropixels ROI selections. Library
   favorites reopen current library files; custom definitions retain snapshots.
3. Transcribe and document official acquisition mappings only where a source
   identifies the site correspondence. Preserve connector-pin versus device
   channel distinctions; record unsupported revisions instead of guessing.
4. Integrate maps into reproducible Cambridge generation, update documentation,
   inspect the scoped diff and run one focused permitted check. No new test
   files, broad suites, independent agents or commits.

Follow-up: add a Headstage selector for passive Cambridge probes. Store selectable
verified routing profiles with the geometry and the selected profile with the
channel map, so saved plans and favorites retain the connection choice. Built-in
Intan routing is fixed. Register Mini-Amp-64 V1 for supported ASSY-236 layouts
from its official Molex pin map; unsupported connections remain explicitly
unassigned. Do not equate a connector label with a recording channel.

Completion (uncommitted):
- Added yellow/empty stars on imported probe tabs and a persistent Favorite
  probes menu. QSettings stores library references or independent custom
  snapshots; favorites exclude poses and NP ROI selections. Library re-imports
  use current files and restore the headstage selected at registration.
- Added Headstage selectors to import preview and probe settings. Registered
  35 built-in Intan models (all ASSY-325/325D, 12 ASSY-350) and selectable
  Mini-Amp-64 V1 profiles for all 18 ASSY-236 entries. Passive probes default to
  Unassigned; changing the selection updates routing without moving the probe.
- Inspected official diagrams visually, including spatial columns, shank order,
  face registration and legacy M1/M2 revisions. Stored factual transcriptions,
  PDF hashes/URLs and pinned geometry hashes in `third_party/cambridge_wiring.json`.
  ASSY-236 pin maps compose with Mini-Amp J1 Bottom / J2 Top. Source contact IDs
  are not assumed to be acquisition IDs. H3/L3 retain missing channel 0, and
  H9 retains missing channel 18; all three still contain 63 physical sites.
- Added optional `ChannelMap.headstage_id` (old plans load with None); saved
  plans already serialize the complete map and profiles. Bundle channel_index
  CSV and manifest now identify the headstage. Existing plans are not migrated;
  re-import to obtain new library profiles. Updated workflow/library docs.
- Generated files with `.venv/bin/python -m
  probe_planner.probes.convert_cambridge --source-dir
  /tmp/atlaxis-probeinterface-bb40894c` (passed, 171 files / 10,765 sites).
  Generation validates pinned blobs, site coverage and each profile's channel
  uniqueness/range before writing. Physical geometry was not edited.
- One permitted lightweight workflow check ran with
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -`
  (inline): selected Mini-Amp in an ASSY-236-H2 import preview, compared the
  four endpoint channels to official probe/pin tables, persisted/reopened a
  favorite using temporary QSettings, verified independent re-import and
  unassign/remove without mutating the original mapping. Passed. Temporary
  settings cleaned automatically. Qt rendering imports initially built a
  temporary Matplotlib font cache; no dependency installation was needed.
- Reviewed the scoped source/UI/data diffs against pre-edit copies. No new
  test files, broad test suite, interactive atlas GUI run, commit or push.

Remaining: 118 models have no registered acquisition profile, including the
unidentified ASSY-350-H15_2 revision and other external-headstage assemblies.
Their geometry remains usable with physical IDs. Other external Intan headstages
and adapters require their exact connector-to-channel maps before being offered
as choices. Profiles are extensible per geometry; unsupported names are not
shown as functional mappings. Existing provisional dimensions remain unchanged.
Full atlas interaction, custom favorite/NP UI flows, and physical hardware
validation were not executed in this task.
