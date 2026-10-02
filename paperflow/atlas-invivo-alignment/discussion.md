# Reusable atlas alignment — 2026-10-02

The user requests mouse in-vivo correction, skull-level coronal sections and
reuse of the saved correction. This is a software alignment change, not a new
registration of the CT specimen to an individual brain.

## Sources and decision

- [Pinpoint in-vivo alignment](https://virtualbrainlab.org/pinpoint/in_vivo_alignment.html)
  documents the Qiu-derived linear scale in AP/ML/DV: 1.031/0.952/0.885, plus
  nominal 5-degree pitch. Its nonlinear-transform section says “Coming soon”.
- [IBL MRITorontoAtlas](https://docs.internationalbrainlab.org/_modules/iblatlas/atlas.html#MRITorontoAtlas)
  independently implements those factors (ordered ML/AP/DV in that library),
  citing [Qiu et al. 2018](https://pubmed.ncbi.nlm.nih.gov/29976930/).
  These are implementation-derived atlas scaling factors, not an individual
  subject's deformation field or numbers claimed to appear directly in the paper.
- The connected Google Drive library contains `paperpile.bib` (about 10 MB);
  discovery was checked before settling the implementation from the primary
  software documentation. A provider full-text search restricted to that file
  did not return the DOI; the full bibliography was not downloaded. No private
  library content is copied into the repo.

Adopt that documented affine correction for new recognized Allen mouse sessions.
Scale native anatomical displacements around Bregma, then level pitch. Preserve
the existing rat landmark-based rotation and unit scale: the mouse factors do
not establish a rat correction. Implement independently from the documented
equations; do not copy Pinpoint code/assets.

Nonlinear registration is not required to reproduce this documented correction.
No validated displacement field for the selected CCF/CT pair is available here;
inventing one or adjusting a warp to conceal skull overlap would change the
scientific problem. Dorr scaling is a different reference and is not mixed in.

## Persistence and sampling

Persist the full affine parameters in plans. Cache computed skull-level slices
by atlas identity, source file revision, transform and slice index. Transform
the original 3D meshes exactly through actor matrices; retain native annotation
IDs for inverse coordinate lookup. Avoid a second resampling of an already
resampled volume. Reconstruct intensity with trilinear interpolation and labels
with the application's existing containing-voxel convention.

Residual limits: population-average scaling does not validate skull fit, size
for a particular age/strain, or specimen-specific targeting. A cached slice is
a sampled view of the affine volume, not a newly registered anatomical atlas.

## Mouse pitch sign correction — 2026-10-02

The initial +5 degree Atlaxis preset inverted the intended correction. The
published [BrainAtlas native space](https://github.com/VirtualBrainLab/BrainAtlas/blob/652467cd1812b948e13dd6382d23da9aa578a68c/Packages/vbl.brainatlas/Scripts/Runtime/CoordinateSystems/BGAtlasSpace.cs)
has posterior/right/ventral axes. [Pinpoint's Qiu definition](https://github.com/VirtualBrainLab/Pinpoint/blob/142489d9c8213ac2aea6a76d70bbb8331a71b64f/Assets/Scripts/Pinpoint/CoordinateSystems/Qiu2018Transform.cs)
and [affine implementation](https://github.com/VirtualBrainLab/BrainAtlas/blob/652467cd1812b948e13dd6382d23da9aa578a68c/Packages/vbl.brainatlas/Scripts/Runtime/CoordinateSystems/AffineTransform.cs)
specify native Ry(-5), with signed scales (-AP, +ML, -DV). Its output DV is
dorsal-positive. Expressing both input and output in Atlaxis's
anterior/right/ventral convention gives forward Ry(+5); posterior points move
ventrally. The Atlaxis inverse lookup therefore needs pitch=-5. This sign is
derived from coordinate conventions, not selected by optimizing CT overlap.

Keep the existing independent scale-then-level composition. Pinpoint's code
instead rotates before scaling; the implementations are not claimed to be
numerically identical. The scale factors are defined in native anatomical axes
by the IBL reference, and nominal leveling is applied afterward here. No
translation, scale adjustment or deformation is fitted to the screenshot.
The separate CT reference remains an approximate, unregistered specimen.

## Additional CT/MRI investigation — 2026-10-02

The corrected sign removes dorsal cerebellar exposure on the sampled grid, but
does not resolve the inferior mismatch. Full-source CT triangle intersections
confirm that this is not merely display simplification. An enclosure-only fit
would not establish anatomical correspondence and is not adopted.

The [Henderson surgical atlas](https://db.phm.utoronto.ca/surgical.htm) supplies
paired C57BL/6J MRI, CT and regional labels. [Chan et al.](https://db.phm.utoronto.ca/Chan.pdf)
describe their registration and use a lambda–rostral-confluence-of-sinuses frame,
not a Bregma-origin flat-skull frame. Local MINC headers specify 0.06 mm voxels.
An exploratory affine ICP fit of its brain-label surface to the corrected Allen
outline improves overall shape agreement, but does not validate internal-region
correspondence or enforce Bregma/Lambda placement. Sampled surface distances have
p95 0.45 mm (Allen to MRI) and 0.78 mm (MRI to Allen), with different fissures and
brainstem extents contributing to this metric. These are fitting diagnostics,
not targeting accuracy. Neither this matrix nor this replacement CT is used in
the application.

The [Perens/Gubra resource](https://www.neuropedia.dk/resource/multimodal-3d-mouse-brain-atlas-framework-with-the-skull-derived-coordinate-system/)
lists published bidirectional MRI/CCF deformation fields and skull-derived
coordinate volumes. Its listed contents do not establish availability of the
corresponding CT surface. Direct archive retrieval returned HTTP 403; browser
download attempts did not complete. The [Duke atlas](https://pmc.ncbi.nlm.nih.gov/articles/PMC12042906/)
provides another scientifically relevant CT/MRI/CCF framework, but its linked
data portal requires an account. No access request was submitted.

Remaining work is to obtain or independently validate a brain registration with
its corresponding CT and skull landmarks, then apply that registration
consistently to surfaces and inverse annotation lookup. A fitted external brain
outline alone is insufficient. The pitch bug is corrected; complete anatomical
alignment remains unresolved. No unvalidated deformation or dataset substitution
has been installed as a default.

Implementation and verification are recorded in
[the ongoing plan/log](../../plan_and_log/2026-09-26-skull-drive-planning.md).
