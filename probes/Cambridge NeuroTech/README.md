# Cambridge NeuroTech library

All **171 model entries** from the ProbeInterface library at commit
[`bb40894cdf55787fed7b7198ea854497d52ca687`](https://github.com/SpikeInterface/probeinterface_library/tree/bb40894cdf55787fed7b7198ea854497d52ca687/cambridgeneurotech)
are provided as Atlaxis JSONs: **10,765 physical sites** in total. The app reads
these files offline. There is no runtime ProbeInterface dependency or download.
Variants and upstream names, including `ASSY-350-H15_2`, remain separate entries.
This is a snapshot of the library, not every product sold by the manufacturer.

Choose **+ Probe**, then a model JSON in this folder. `ASSY-350-H20.json` and
`ASSY-325D-E-1.json` replace the older H20/E-1 filenames. Existing saved plans
embed their own geometry and remain unchanged; re-import to use updated files.

## Geometry and channel IDs

- **H20 and E-1 corrections:** retain Atlaxis's catalog-based geometry and the
  official 128-channel maps already integrated. H20's remote sites and E-1's
  30 um thickness/front-back layout are not overwritten by upstream geometry.
  Their prior dimensional uncertainty remains; see [the main library notes](../README.md).
- **Other 169 models:** preserve upstream site IDs, contact x/y, site count and
  planar outline. The leftmost physical contour tip is translated to `(0,0,0)`;
  the lowest electrode is never substituted for the tip. Shanks are numbered
  left to right from zero; differing tip heights are retained.
- **Shank recovery:** tips are the sharp local minima of the source contour.
  The common outline is partitioned at the x midpoints between tips, preserving
  its shape and any common base. This also handles missing shank IDs and H12's
  erroneous single-shank label. Original labels remain in metadata.
- **Thickness:** upstream supplies 2D layouts without shaft thickness. A nominal
  15 um single-sided / 30 um double-sided extrusion is used for display, with
  contacts at `z = -thickness/2` (front) or `+thickness/2` (back). These z offsets
  also enter atlas placement. They are assumptions with unknown physical error,
  not measured model-specific dimensions. Both faces retain upstream x/y.
- **Unverified dimensions:** upstream shaft lengths and tip offsets are retained
  without a full manufacturer audit. Three upstream ASSY-325 layouts (H3, H9,
  L3) contain 63 sites; they remain 63-site files without fabricated contacts.
- **Wiring:** none of the 171 upstream JSONs contains acquisition-channel indices.
  Atlaxis adds manufacturer maps separately: 35 built-in Intan entries have
  recording-channel assignments; 18 ASSY-236 entries have selectable Mini-Amp-64
  V1 profiles; 61 current external-headstage entries have selectable Intan RHD
  profiles. All physical sites remain active, including when wiring is unassigned.

Each JSON records its source URL, revision, Git blob hash, conversion status and
dimensional limitations. `.manifest.json` lists all models, counts and correction
status; it is hidden to keep it out of the probe chooser's normal file list.

## Headstage and wiring

In the Import preview or the probe tab, **Headstage** selects a registered
connection profile. Passive probes default to **Unassigned**, displaying Site IDs.
Select **Mini-Amp-64 V1 (J1 Bottom / J2 Top)** only for that actual connection;
the table then displays zero-based Intan recording Channel IDs. The choice and
complete mapping are embedded in saved plans; `channel_index.csv` and the bundle
manifest identify the headstage. Re-import older saved probes to obtain new profiles.
Favorite probes remember the headstage chosen when the favorite is registered.

Coverage from the [manufacturer map index](https://www.cambridgeneurotech.com/neural-probes/probe-maps):

- **ASSY-325:** all 16 library entries. M1v2/M2v2 use the current M1/M2 maps.
  H3 and L3 lack the uppermost site (channel 0); H9 lacks the uppermost right
  site (channel 18). Each maps its 63 supplied sites into a 64-channel device.
- **ASSY-325D:** all seven entries, including both faces. Shanks use the
  manufacturer's shared D-to-A / F-to-A / B-to-A projection for both face tables.
- **ASSY-350:** 12 entries, including H20. `H15_2` remains unassigned because
  the public H15 map does not identify that staggered variant.
- **ASSY-236:** 18 of 19 entries, including the separate pre-June-2022 and current
  M1/M2 revisions. Site-to-Molex-pin maps are composed with the official
  [Mini-Amp-64 V1 map](https://www.cambridgeneurotech.com/assets/files/Mini-Amp-64-V1-map.pdf).
  Probe Bottom connects to J1, Top to J2; REF/GND are excluded from recording IDs.
- **61 current external-headstage entries:** the following named configurations
  compose the individual probe maps with the official Cambridge adapter maps
  and [Intan connector pinouts](https://intantech.com/files/Intan_Recording_Controller_user_guide.pdf)
  (figures 5, 11 and 17). Only currently listed revisions are added; M1/M2 use
  the June-2022-onwards maps (`v2`).

  | Assembly | Entries | Registered connection |
  | --- | ---: | --- |
  | ASSY-1 | 4 | Cambridge A16-Om16 + Intan RHD 16ch C3334/C3335 |
  | ASSY-37 | 11 | Cambridge A32-Om32 + Intan RHD 32ch C3314/C3324 |
  | ASSY-77 | 16 | Cambridge A64-Om32x2 + Intan RHD 64ch C3315/C3325 |
  | ASSY-79 | 4 | Direct Intan RHD 16ch C3334/C3335 |
  | ASSY-116 | 10 | Direct Intan RHD 32ch C3314/C3324 |
  | ASSY-156 | 16 | Direct Intan RHD 64ch C3315/C3325 |

  RHD 16ch retains native amplifier inputs **8-23**, not compacted 0-15 IDs.
  Its channel map and XML/channel-index export use the **32-input namespace**;
  grounded inputs 0-7 and 24-31 have no physical probe site. Recording software
  may rename or compact these channels; check that order before using exports.
  For 64ch, Front Omnetics mates to the chip-side headstage connector and Back
  to the opposite connector, following the printed-side orientation in the maps.
  Adapter brands and two-separate-headstage configurations are not interchangeable
  with these named single-headstage profiles.
  **ASSY-156-M1v2:** the official current spatial table puts source Site 5 on
  connector pin 6 and Site 6 on pin 5. Routing follows that table while preserving
  the original physical Site IDs and coordinates.
- **57 entries remain without a registered profile.** This includes old/discontinued
  revisions and three unidentified variants: ASSY-37-H3 (64 source sites but no
  current ASSY-37-H3 map), ASSY-236-H1 (no current map) and ASSY-350-H15_2
  (the H15 map does not identify the staggered variant). Import explains that
  recording-channel wiring is unsupported; geometry can still be imported.
- Other assemblies/headstages/adapters remain unassigned. An Intan chip name
  alone does not identify a headstage's connector wiring. No substitute profile
  is inferred from matching contact counts or probe-style names.

Every import preview asks the user to verify **Channel ID to physical Site**
against their actual probe revision, headstage/adapter documents and acquisition
software channel order. Links to the probe, headstage and adapter maps are shown
for registered profiles. Existing saved plans keep embedded geometry and maps;
re-import from this library to obtain the new profiles.

These are per-probe channel numbers, before recording-system port offsets.
`third_party/cambridge_wiring.json` retains source URLs/PDF hashes and explicitly
transcribed spatial rows/columns against pinned source site IDs. Its `connections`
tables record connector-to-native-channel permutations and adapter pin composition;
the converter resolves these into offline profiles without a runtime dependency.
Source labels
are not simply decremented: several models use different permutations. Maps
describe wiring, not independently verified mechanical dimensions. The existing
upstream geometry limitations above still apply; no new sites or dimensions are
invented. Physical hardware validation has not been performed.

## Reproduction

From the repository checkout with the existing Python environment:

```sh
.venv/bin/python -m probe_planner.probes.convert_cambridge \
  --source-dir /tmp/atlaxis-probeinterface-bb40894c --download
```

Omit `--download` to regenerate from an existing source directory without network
access. `--destination PATH` writes to another directory. Source files are checked
against `third_party/probeinterface_cambridge.lock.json` before conversion. All
models are converted and validated before output files are written. Only the
named model files, hidden manifest and license are written; custom files are not
deleted. Keep custom edits under distinct filenames.

The development converter reads ProbeInterface's public JSON format directly,
so even generation does not require installing the ProbeInterface Python package.
H20/E-1 corrections are sourced from `src/probe_planner/probes/catalog.py`.
Official wiring overlays are read from `third_party/cambridge_wiring.json` and
applied only to their pinned source geometry. The app uses embedded profiles
offline, without reading the development source data or downloading PDFs.
Updating the upstream revision is a deliberate development change to the
converter and lock, with review of new coordinate conventions and model variants.

## Attribution

Derived from **ProbeInterface Library**, Copyright (c) 2023 SpikeInterface,
distributed under the **MIT License**. The complete notice is included in
[LICENSE-ProbeInterface.txt](LICENSE-ProbeInterface.txt) and bundled with the app.
Cambridge manufacturer maps and catalogs are linked in metadata, not redistributed.
