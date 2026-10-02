# CT skull reference definitions

Only JSON source/registration definitions are distributed here. The application
downloads the originals from the providers during first atlas load and caches
prepared surfaces and shaded source-surface images in the user's selected data
folder, under `skulls/`. Cached
files are keyed by the complete definition; changed registration metadata uses
a new cache. Startup performs no skull download or preparation.

| Species | Source | Terms | Reference Bregma–Lambda |
| --- | --- | --- | --- |
| Rat | Pohl, Gasca, Christ and Hofmann (2013), [Figshare 777745 v1](https://doi.org/10.6084/m9.figshare.777745.v1); micro-CT of a 250 g male Wistar rat | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | 8.30 mm |
| Mouse | UT Austin / DigiMorph, [TMM M-3196](https://digimorph.org/specimens/Mus_musculus/stl.html); adult female house mouse CT | [Provider-specific terms](https://digimorph.org/aboutdigimorph.phtml); redistribution permission is not established | 4.25 mm |

Downloading directly avoids redistributing the models with Atlaxis; it does not
grant additional rights. DigiMorph's STL page permits download for 3D rendering
and printing. Its site-wide terms restrict redistribution and other uses. Check
those terms before sharing derived meshes or plans containing the embedded mesh.

## Registration and size

The JSON definitions retain original source-space Bregma/Lambda candidates and
the reviewed rigid transforms. Mouse uses the visually adjusted landmarks. Rat
uses the latest fixed landmarks and an approximate cranial-vault symmetry plane;
the remaining specimen/reconstruction asymmetry is preserved. Bregma/Lambda are
at equal DV. Rat Lambda has a small nonzero ML; it was not moved to enforce both
the fitted symmetry plane and an exactly midline B–L vector simultaneously.

Absolute source calibration was not established. Uniform reference scaling uses
4.25 mm from the adult CT/MRI reference described in
[AtlasGuide](https://pmc.ncbi.nlm.nih.gov/articles/PMC3863333/) and 8.30 mm,
rounded from the Euclidean separation of the WHS metric landmarks in its
[coordinate note](https://www.nitrc.org/docman/view.php/1081/194197/).
These are practical reference sizes, not measurements of the downloaded skulls,
an Allen CCF landmark separation, or individual-animal calibration. The GUI's
Bregma–Lambda field changes skull scale only, about its Bregma origin.

No brain scaling is applied. Allen retains its +5° default. New recognized WHS
rat sessions use a landmark-derived pitch of atan2(-24, 211), approximately
−6.49°, about Bregma. The [2014 v1.01 table](https://www.nitrc.org/docman/view.php/1081/2095/Coordinates_v1-v1.01.pdf)
gives native Bregma (246, 653, 440) and Lambda (244, 442, 464); their AP/DV
displacement in anterior+/ventral+ axes is (-211, -24) voxels. The shared frame
levels those landmarks without modifying the native atlas data or skull shape.
This explicitly selects landmark leveling over the inconsistent nominal 4°
description; the publication discrepancy remains unresolved. Saved project
coordinates remain unchanged. Skull/brain correspondence is approximate.

## Surface preparation

STL hashes identify the exact originals. Rat's native Z<580 crop excludes
attached posterior structures as in the reviewed figure. Apply rigid placement
and uniform reference sizing, then VTK quadric decimation toward 20,000 triangles
with volume preservation. Before simplification, a 1200-pixel software-shaded
dorsal projection records the actual source surface relief, with depth-ordered
triangles. This avoids introducing a second OpenGL context in the loader thread.
It is not a suture segmentation: unresolved sutures are never invented. Pixel
extents retain their AP/ML mapping. This is a simplified 3D display reference. A deterministic
sample of up to 5,000 original vertices is measured against the reduced surface;
median, 95th percentile and maximum sampled distances are stored in the cached
metadata. They are not a Hausdorff bound, registration error or anatomical
accuracy estimate. Smooth normals are computed once when creating the actor.

Initial preparation produced 19,999 triangles per species. At the reference sizes,
sample median / p95 / maximum distances were 0.0222 / 0.0905 / 1.6779 mm for rat
and 0.0096 / 0.0369 / 0.2448 mm for mouse. Local fine detail can be lost, especially
in rat; these meshes do not establish precise hardware clearance.

Cached metadata, landmarks, skull-only scale and source geometry are embedded in
saved plans. Existing custom skulls and explicitly removed skulls stay intact;
use Settings → Skull → Use atlas reference to opt into the current reference.

Cache preparation version 2 includes the original-surface image for craniotomy
editing. New references start hidden; applying craniotomies makes them visible.
