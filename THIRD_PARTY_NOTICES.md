# Third-party notices

Atlaxis is licensed under [GNU GPL v3.0](LICENSE.md). Third-party software and
data retain their own copyright notices and licenses. Inclusion here does not
relicense those components or imply endorsement by their authors.

## Software

The [dependency index](third_party/licenses/environment/INDEX.md) lists exact
versions, license metadata and links to the original notices. Its
[manifest](third_party/licenses/environment/manifest.json) records source-archive
locations and notice checksums. Standalone builds regenerate this collection
from their own Python environment, including platform-specific dependencies.
The repository snapshot is from macOS x86_64; it is not the inventory of a
released macOS arm64 or Windows application.

| Components | Notices |
| --- | --- |
| BrainGlobe Atlas API / BrainGlobe Space | BSD notices in the dependency index |
| NeuroCarto | BSD-3-Clause; Copyright (c) 2023 AntonioST; original notice in the dependency index |
| NumPy, SciPy, Matplotlib, VTK and their bundled components | Original package notices, including available native-library and font notices; supplementary [VTK notices](third_party/licenses/upstream/vtk/) |
| PyVista, PyVistaQt and QtPy | MIT notices in the dependency index |
| PySide6, Shiboken6 and Qt | [PySide notices](third_party/licenses/upstream/pyside-setup/), [Qt Base](third_party/licenses/upstream/qtbase/), [Qt SVG](third_party/licenses/upstream/qtsvg/) and [Qt Image Formats](third_party/licenses/upstream/qtimageformats/) |
| Python interpreter | [License and historical notices](third_party/licenses/environment/python/LICENSE.txt) |
| PyInstaller bootloader and runtime | [Original licenses and bootloader exception](third_party/licenses/upstream/pyinstaller/) |
| Other direct and indirect Python dependencies | Original LICENSE, COPYING, NOTICE, AUTHORS and other license files in the dependency index |

Qt and Qt for Python are Copyright The Qt Company Ltd. and other contributors.
For this GPL-3.0-only application, use their GPLv3 option where offered; their
third-party code retains its individual terms. The collected Qt attribution
JSON files retain component names, copyright holders, versions and license
references. Optional components and other operating systems are included in
the upstream collection; their presence does not imply they are in the app.
See the [pinned upstream source manifest](third_party/licenses/upstream/manifest.json).

## Probe data

Cambridge NeuroTech layouts derived from the ProbeInterface Library are
Copyright (c) 2023 SpikeInterface and provided under the
[MIT license](third_party/licenses/probe-data/ProbeInterface-LICENSE.txt).
The source revision is `bb40894cdf55787fed7b7198ea854497d52ca687` in
[SpikeInterface/probeinterface_library](https://github.com/SpikeInterface/probeinterface_library).
Manufacturer maps and catalogs linked in probe metadata are not redistributed.

Seven original XML files from [ayalab1/ProbeMaps](https://github.com/ayalab1/ProbeMaps)
are included under the NeuroNexus probe library. The pinned revision is
`c50ba8f23a634e9513507b6843703413af175f16`; file provenance is recorded in
`third_party/probemaps.lock.json`. No redistribution license was located in the
checked upstream repository. **Permission to redistribute these XMLs remains
unverified.** Attribution alone does not grant permission; resolve this before
publishing a distribution containing them. Atlaxis's GPL does not grant rights
to third-party probe data.

## Atlas data and README images

Atlas volumes are downloaded separately through BrainGlobe and are not bundled
with Atlaxis. Each atlas has its own terms and citation requirements, independent
of the BrainGlobe software license.

`docs/images/ca1-overview.jpg` and `docs/images/ca1-rois.jpg` show the Waxholm Space
atlas of the Sprague Dawley rat brain, BrainGlobe package
`whs_sd_rat_39um_v1.2`. Atlaxis rendered the atlas with probe and CA1 ROI overlays;
the images do not represent experimental recordings. Atlas reference:

Kleven, H., Bjerke, I. E., Clascá, F., et al. (2023). *Waxholm Space atlas of the
rat brain: a 3D atlas supporting data analysis and integration.* Nature Methods
20, 1822–1829. [DOI: 10.1038/s41592-023-02034-3](https://doi.org/10.1038/s41592-023-02034-3).
RRID: SCR_017124.

The [atlas project page](https://www.nitrc.org/projects/whs-sd-atlas/) states
CC BY 4.0. Its [citation page](https://www.nitrc.org/citation/?group_id=1081)
also says CC BY 4.0, but links to CC BY-SA 4.0. Both original legal texts are
included for reference under [atlas licenses](third_party/licenses/atlas/);
this does not select or grant a license on the authors' behalf. Confirm the
terms for the exact atlas package and derived images before redistribution.

## Downloaded CT skull references

Atlaxis distributes source links and approximate registration metadata only;
skull meshes download directly to the user's data folder on first use.

- Rat: Bernd M. Pohl, Fernando Gasca, Olaf Christ and Ulrich G. Hofmann (2013),
  [3D .stl file of rat skull](https://doi.org/10.6084/m9.figshare.777745.v1),
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Local preparation
  crops attached posterior structures, applies rigid registration and uniform
  reference scaling, and simplifies the surface.
- Mouse: UT Austin / DigiMorph, specimen TMM M-3196,
  [CT-derived STL](https://digimorph.org/specimens/Mus_musculus/stl.html).
  [Provider terms](https://digimorph.org/aboutdigimorph.phtml) apply;
  redistribution permission is not established. Local preparation applies
  rigid registration, uniform reference scaling and surface simplification.

Downloading from a provider does not waive its terms. Saved plans embed the
prepared mesh, so sharing such plans may also constitute redistribution.
See [reference metadata and limitations](src/probe_planner/data/skulls/README.md).

## Distribution status

These notices preserve available upstream texts; they are not certification of
a completed binary license audit. See [source distribution and outstanding
release requirements](docs/licensing.md), including the ProbeMaps permission,
atlas terms and native-library source checks.
