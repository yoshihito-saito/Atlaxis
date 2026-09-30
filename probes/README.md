# Probe library

Choose **+ Probe** (always starts in this library), open a manufacturer folder, select JSON, inspect the preview,
then **Import**. All coordinates are micrometers; shanks are zero-based.
The preview's lower-left scale bar follows zoom and displays micrometers or
millimeters. It measures physical geometry, not the fixed-size site markers.
The tip of shank 0 is the origin. Positive y points toward the shaft base;
front sites lie at negative z and back sites at positive z. Cambridge includes
all **171 models** in the pinned ProbeInterface snapshot, with two curated
corrections. See [the Cambridge manifest and instructions](Cambridge%20NeuroTech/README.md).
NeuroNexus includes 24 additional 64/128-channel models with source-backed
connection profiles; see [NeuroNexus coverage](NeuroNexus/README.md).
Two more models and normal XML configurations were added from
[ProbeMaps](https://github.com/ayalab1/ProbeMaps), with manufacturer geometry.
The table below lists the original curated models, not the full expanded library.

## XML and CellExplorer companions

Each existing `<manufacturer>/<model>.json` has a sibling `<model>/` folder.
The original JSON paths remain unchanged, including for favorites. Each confirmed
connection has a matching `.xml` and `.chanCoords.channelInfo.mat` pair in that
folder. Select the actual package/headstage variant; the files are not interchangeable.
XML is zero-based. MAT rows are indexed by recording channel + 1, with XYZ in
probe-local micrometers and zero-based shanks. Unassigned amplifier inputs retain
NaN coordinates (`connected=false`) so native channels are never silently shifted.
The existing Atlaxis MAT importer accepts finite coordinate rows only; use the
JSON plus connection selector in Atlaxis for profiles with unassigned inputs.

For CellExplorer, rename the chosen MAT file to
`<session>.chanCoords.channelInfo.mat`. Generated XMLs contain channel groups;
merge actual acquisition settings before use. Source XML copies under `ProbeMaps/`
retain their original settings and bytes. A6x21 alone uses user-requested provisional
Channel IDs (left-to-right shanks, tip-to-base, 0-127), clearly marked in its files
and import preview. Other unassigned models receive no invented XML/chanCoords.

Neuropixels has no static all-site recording map. After selecting channels, use
**Save & update**: the plan folder receives `probe_N.channels.xml` and
`probe_N.chanCoords.channelInfo.mat`, alongside combined `probes.xml`.
These describe the current selection; missing channels have no inferred position.
MAT channels are local to that probe; `combined_xml_channel` records the offset
into the combined XML. Saving after Reset/removal removes obsolete managed NP
companions. IMRO/CSV exports remain manual and are not changed by Save.
Generated, fully mapped groups in `probes.xml` list the original hardware channel
IDs in physical base-to-tip order, matching the per-probe XML companions.
Explicit imported XML order and groups without known site correspondence remain
unchanged. Channel-index CSV and MAT rows remain indexed by hardware channel.

Regenerate companions after updating the geometry library:
`python -m probe_planner.probes.companions`.
Use `--probemaps-source-dir <pinned-checkout>` to also copy the seven original
normal NeuroNexus XMLs. The pinned revision/blob hashes are in
`third_party/probemaps.lock.json`; version2, reversed, opposite and flipped files
are excluded. Models without identifiable geometry remain source-reference folders.

| Manufacturer / model | Physical shanks | Physical sites | Length / thickness | Geometry status |
| --- | ---: | ---: | --- | --- |
| NeuroNexus A6x21-poly2-10mm-50-200-160 | 6 | 128 | 10 mm / 50 µm | Provisional tip offset |
| NeuroNexus Buzsaki-5x12 | 5 | 64 | 5 mm / 15 µm | Dimensioned site layout |
| NeuroNexus A5x12-16-Buz-Lin-5mm-100-200-160-177 | 5 | 64 | 5 mm outer, 6.2 mm center / 15 µm | Dimensioned sites; schematic shaft width |
| NeuroNexus A4x16-poly2-5mm-23s-200-177 | 4 | 64 | 5 mm / 15 µm | Dimensioned site layout |
| NeuroNexus Buzsaki64L | 8 | 64 | 10 mm / 50 µm | Dimensioned site layout; 50 µm variant |
| Cambridge NeuroTech H20 (ASSY-350) | 4 | 128 | 6.5 mm / 15 µm | Provisional tip offset and middle remote-site distances |
| Cambridge NeuroTech E-1 ASSY-325D | 4, double-sided | 128 | 6 mm / 30 µm | Provisional taper-site positions and exact face registration |
| Neuropixels 1.0 single shank | 1 | 960 | 10 mm / 24 µm | Dimensioned site layout |
| Neuropixels 2.0 single shank (NP2003) | 1 | 1280 | 10 mm / 24 µm | Provisional tip-to-first-site offset |
| Neuropixels 2.0 four shank (NP2013) | 4 | 5120 | 10 mm / 24 µm | Provisional tip-to-first-site offset |

The original curated shaft silhouettes interpolate catalog dimensions. The
expanded Cambridge entries retain upstream planar outlines, including any common
base, with nominal display thickness. Neither is certified manufacturer CAD;
connectors, cable and headstage packaging are omitted. These files do not support
mechanical collision certification.
Site centers are modeled in 3D; the viewer uses display markers, not scaled
electrode-pad outlines. Source and uncertainty notes are embedded in every JSON
and retained in saved plans. No original catalogs are bundled; the requested
normal ProbeMaps XMLs are preserved with source provenance.

## Sources and decisions

Sources accessed 2026-09-20. Page numbers below are PDF page positions, not the
printed catalog index. These independently constructed layouts use the public
dimension facts; manufacturer documents remain at the linked sources.

- [NeuroNexus catalog V2.1](https://solutions.neuronexus.com/hubfs/Penetrating_Probe_Catalog_V2.1.pdf):
  A4x16 page 89, A5x12-16 page 95, Buzsaki 5x12 page 102, Buzsaki64L page 104,
  A6x21 page 119. Buzsaki 5x12 includes four additional center-shank sites;
  A6x21 includes two proximal sites on the third shank from the left (Shank 2,
  electrode-facing view): counts are 21/21/23/21/21/21. Neither is simply
  the product of the two numbers in its name. A5x12-16's central tip extends
  1.2 mm beyond the other tips. Its shaft is modeled at 58 µm width without
  guessing the undimensioned proximal widening. Buzsaki64L uses the 50 µm
  thickness variant; the 15 µm variant is not a separate file.
- [Cambridge catalog](https://www.cambridgeneurotech.com/assets/files/Cambridge-NeuroTech-Product-Catalog.pdf):
  E1 page 40; H20 page 50. H20 includes 31 clustered sites and one remote site
  per shank. E-1 ASSY-325D is modeled with 16 sites per face on four shanks.
  Default lengths/thicknesses are the catalog standards above.
- [H20 ASSY-350 map](https://www.cambridgeneurotech.com/assets/files/ASSY-350-H20-map.pdf)
  and [E-1 ASSY-325D map](https://www.cambridgeneurotech.com/assets/files/ASSY-325D-E-1_E-2-map.pdf),
  both updated 2024-07-01: complete **zero-based Intan/Open Ephys channels 0–127**
  for these digital SPI assemblies are included. No separate map import is
  needed for these assemblies. H20 shanks 0–3 follow A–D in the electrode-facing
  schematic (opposite the headstage front-view photo). E-1 shanks 0–3 follow
  D–A in both face tables; we interpret this as a common front projection and
  no longer mirror the back sites again. The JSON `shank_labels` records this
  orientation. Connector/headstage variants need their own verified wiring map.
- [Neuropixels official support](https://www.neuropixels.org/support),
  [1.0 datasheet](https://www.neuropixels.org/_files/ugd/328966_9f784121a69f4f56bd314ffdf7f86d2b.pdf),
  [2.0 datasheet](https://www.neuropixels.org/_files/ugd/328966_2b39661f072d405b8d284c3c73588bc6.pdf)
  and 2.0 User Manual V1.0.6 pages 14–16: shaft and site dimensions, total sites,
  shank pitch and 384 simultaneous readout channels. All physical sites are
  included; NeuroCarto selection and IMRO routing are available in the GUI.
- [SpikeGLX ProbeTable](https://github.com/billkarsh/ProbeTable/blob/main/Tables/probe_features.json)
  supplies NP2 column centers 27 and 59 µm from the left edge of its 70 µm shaft.
  These are asymmetric about the shaft center. The
  [cortex-lab layout documentation](https://github.com/cortex-lab/neuropixels/wiki/Selecting-recording-electrodes)
  gives NP1's staggered columns and 200 µm first-row offset. Site numbering here
  is our spatial index, not a device channel. The Neuropixels adapter validates
  these coordinates before mapping (shank, column, row) to NeuroCarto electrodes.

Local pyNeuroscope references checked: `A4x16-Poly2-5mm-23s-200-177.xml`,
`Buzsaki64L.xml`, both `A5x12_16-Buz_lin-5mm-100-200-160_177_version*.xml`, and
`E-1_ASSY-350_128ch_double-sided.xml`. They corroborate channel/group counts
but lack physical XYZ and independent contact-to-channel associations. Eight
E1 groups correspond to faces, not evidence for eight physical shanks. They
were not used as wiring in the initial pilot. The newer ProbeMaps import uses
the pinned repository's documented base-to-tip order, with explicit selectable
profiles; its reversed/version2 variants are excluded.

## Provisional dimensions

- A6x21 tip-to-first-site: approximately 35.5 µm, digitized from the catalog.
- H20 tip-to-first-site: approximately 22.5 µm. Remote gaps from the cluster's
  uppermost row: 1200/1000/800/600 µm; middle two are inferred from drawing scale.
- E1 tip-to-first-site: approximately 22.5 µm. Taper x coordinates are digitized;
  both faces use the map's common front projection. The layout preserves nominal
  20 µm stagger/40 µm same-column spacing and 300 µm cluster span.
- Neuropixels 2.0 tip-to-first-site: provisionally 200 µm. The manufacturer
  specifies a 175 µm taper, which is not a first-site center distance.
  ProbeTable's 206/209 µm `tip_length` differs from that taper dimension and
  is not substituted as an undocumented site-center offset.

Catalog digitizing has about 2–5 µm reading repeatability, not a manufacturing
tolerance or known accuracy. NP2's offset and E1's exact backside registration have
no established error bound. These entries are usable for preliminary layout;
precise tip-based targeting needs dimensioned drawings or measured probes.
The import preview shows both faces without a selector; detailed provenance and
dimension limitations are retained here and in JSON metadata.

## Editing and regeneration

The standard JSON format accepts arbitrary contacts, bodies and metadata.
35 Cambridge built-in Intan models include `channel_map.contact_to_channel`
from official maps. The 18 ASSY-236 models offer Mini-Amp-64 V1 as a selectable
headstage; see [Cambridge wiring coverage](Cambridge%20NeuroTech/README.md).
Other ordinary probes leave routing empty until verified wiring
is supplied; their summary displays **Site ID**. With a map it displays
**Channel ID** instead.
No site is removed from Geometry when it lacks routing. Ordinary probes always
use all contacts and have no channel-selection controls. Neuropixels has an
Active only display filter and per-ROI activation, or IMRO import to assign
hardware channels; see the main README for the workflow.

The corrected E-1 entry is now `ASSY-325D-E-1.json`; H20 is `ASSY-350-H20.json`.
Their old filenames were removed to avoid duplicate entries.
Saved plans embed their own geometry and routing and are not silently migrated.
Re-import a corrected library probe to use the updated geometry/channel map;
restore its planned placement as needed.

The original curated layouts live in `src/probe_planner/probes/catalog.py`.
The NeuroNexus expansion is in `neuronexus_catalog.py`, with source tables in
`third_party/neuronexus_wiring.json`. Regenerate only NeuroNexus with
`python -m probe_planner.probes.catalog --manufacturer NeuroNexus`.
From the repository root, `python -m probe_planner.probes.catalog` rewrites the
curated and expanded NeuroNexus JSONs, so custom variants should use separate filenames. To regenerate
the complete Cambridge snapshot and its provenance, use
`python -m probe_planner.probes.convert_cambridge --source-dir PATH --download`.
The source lock is `third_party/probeinterface_cambridge.lock.json`; no
ProbeInterface package is required. Installed wheels include this directory,
including Cambridge's MIT attribution, under `probe_planner/data/probes`.
