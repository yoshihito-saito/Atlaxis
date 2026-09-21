# NeuroNexus 64/128-channel library

The library contains 31 models: the five original entries, 24 manufacturer-map
additions and two ProbeMaps additions. 29 models offer source-based connection
profiles; A6x21 has user-requested provisional IDs. Other mapped imports start with
**Unassigned**: select the actual **Package / headstage**, then Import. The same
selector is available in the probe's coordinate tab. Saved plans embed their old
geometry and wiring; re-import a library entry to obtain corrections. Sibling
model folders contain connection-specific XML and CellExplorer chanCoords pairs.

Supported connections, where a matching spatial map is available:

- Activus AV64 / AVH64 / AVI64 / AVIH64, and their 128-channel counterparts:
  the manufacturer's zero-based recording channels are retained directly.
- H64LP / MRH64LP with SmartLink64 Chronic or Intan RHD64 C3315 / C3325:
  package pins are traced through the selected headstage's connector diagram.
- A64 / MRA64 / original OA64LP with SmartLink64 Acute. **Not OA64LP V2**.

All resulting Channel IDs are zero-based, local to that probe. Connector pin
numbers remain separately recorded in profile metadata and are never exported as
recording channels. Other packages, adapter chains and headstage models are not
interchangeable. Before every use, verify Channel ID against physical Site using
the exact probe revision and recording-system documentation; the import preview
retains this reminder and links to the source maps.

## Added models

| Family | Added variants | Channels |
| --- | --- | ---: |
| A1x64 Edge | 6mm-20-177 | 64 |
| A2x32 linear | 5mm-25-200-177; 5mm-100-200-177; 6mm-70-200-177; 8mm-35-200-177 | 64 |
| A4x4 tet | 5mm-150-200-121 | 64 |
| A4x16 linear | 3mm-50-200-177 | 64 |
| A4x16 poly3 | 5mm-20s-200-160 | 64 |
| A8x8 linear | 5mm / 10mm, 200-200, 177 / 703 square-micrometer site area | 64 |
| A8x8 Edge | 5mm-50-150-177; 5mm-100-200-177 | 64 |
| Buzsaki | Buzsaki64; Buzsaki64sp; Buzsaki64spL | 64 |
| A2x64 Poly4 | 10mm-20-800-100 | 128 |
| A4x32 Poly2 | 5mm-23s-200-177; lin-5mm-20s-150-160 | 128 |
| A8x16 Edge | 5mm-30-500-121; 5mm-50-150-177; 5mm-100-200-177 | 128 |
| A16x8 berg | 5mm-200-160 | 128 |

Existing A4x16-poly2-5mm-23s-200-177 now offers Activus wiring. Existing
Buzsaki64L now offers H64LP and A64 connections listed above.

## A6x21 and deferred connections

The A6x21 full-probe drawing on catalog page 119 places the two extra proximal
sites on **Shank 2**, third from the left in the electrode-facing view. The
enlarged tip illustration is not the physical shank order. Counts are
**21 / 21 / 23 / 21 / 21 / 21**, total 128. Only these two sites moved; the
previous provisional 35.5 um tip offset and all other geometry remain unchanged.
No matching manufacturer channel map was found. At the user's request it now
uses provisional Channel IDs 0-127: left-to-right shanks and tip-to-base contacts
within each shank. Shank ranges are 0-20, 21-41, 42-64, 65-85, 86-106, 107-127.
These are placeholders for review, not confirmed recording wiring.

The existing Buzsaki-5x12 remains unassigned: HZ64 site-to-pin maps are available,
but its full recording connection is not registered. It receives no generated
XML/chanCoords. A5x12-16 Buz-Lin 5mm now offers the explicitly named ProbeMaps
normal XML configuration below; no Activus route is inferred from the 3-4 mm variant.

## ProbeMaps normal XMLs

Pinned [ayalab1/ProbeMaps](https://github.com/ayalab1/ProbeMaps/tree/c50ba8f23a634e9513507b6843703413af175f16).
Its generator documents left-to-right shanks and base-to-tip site order. This
is reversed when associating the XML with Atlaxis tip-to-base contacts. The A5
coordinate table independently corroborates the group/site order; physical
coordinates here retain the manufacturer catalog's origin and dimensions.

- Added **A1x32-Edge-5mm-20-177** from catalog page 41 (15 um thickness variant).
- Added **A4x16-Poly2-lin-5mm-20s-150-160** from catalog page 92. The XML alias
  `A4x16-Poly2-5mm-20s-lin-160` matches official OA64LP V2 spatial map page 4;
  it is distinct from the staggered-tip 190 um model.
- Existing **A4x16-poly2-5mm-23s-200-177** and **A5x12-16-Buz-Lin-5mm-100-200-160-177**
  also gain a `ProbeMaps normal XML` choice. Select it only for that configuration.

Seven original XMLs are copied under model/reference folders in `ProbeMaps/`,
with unchanged bytes and pinned blob hashes. Version1 is retained; version2,
reversed, opposite and flipped alternatives are excluded.
`64_HPC_curvature` and `A4x16-Lin-5mm-50s-300` remain XML references because exact
manufacturer geometry could not be established. The combined Poly3 + Buz-Lin
XML remains a two-probe reference, not a fabricated single-probe model.
No coordinates or new GUI probe were invented for these three source-only entries.

Other package maps are not automatically applicable to a similarly named
geometry. X-series/AC128 pin maps need the downstream headstage route; a package
pin map alone does not establish a recording Channel ID. Models with unresolved
dimension/revision differences (including the Poly5 drawings) are deferred.

## Geometry and provenance

Site coordinates use micrometers, electrode-facing left-to-right shanks and
tip-to-base site order, then left-to-right within a row. Nonrecording reference
pads are not counted as recording contacts. Shaft silhouettes are schematic,
with interpolated taper dimensions; they are not certified CAD. Edge variants
use provisional lateral pad-center registration because the catalog does not
fully dimension it; their exact lateral error is unknown. Axial pitch, nominal
tip offset and shank pitch follow the catalog. These limitations are embedded in
each affected JSON. No other new digitized coordinate approximation is used.

Sources accessed 2026-09-20:

- [64-channel package maps](https://www.neuronexus.com/product_documentation/64-channel-package/)
- [128-channel package maps](https://www.neuronexus.com/product_documentation/128-channel-package/)
- [SmartLink headstage maps](https://www.neuronexus.com/product_documentation/headstage-mapping/)
- [Intan Recording Controller guide, page 11 / Figure 17](https://intantech.com/files/Intan_Recording_Controller_user_guide.pdf)
- [NeuroNexus catalog](https://solutions.neuronexus.com/hubfs/Penetrating_Probe_Catalog_V2.1.pdf)

Exact PDF URLs, hashes, page numbers, spatial number lists, connector row
orientation and pin-to-amplifier permutations are retained in
`third_party/neuronexus_wiring.json`. Generated profiles retain the relevant
source identifiers and site-to-channel maps. No manufacturer PDFs are bundled.
The application needs neither internet access nor a third-party geometry package.
