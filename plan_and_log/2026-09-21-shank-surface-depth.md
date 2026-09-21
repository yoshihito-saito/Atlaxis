# Reference-shank surface depth

## Goal and scope

Use each selected shank's insertion-axis intersection with the annotated brain
surface as the common origin for insertion depth and tip DV. Selecting another
shank must preserve the complete physical probe pose. Entering zero moves the
rigid probe so the selected tip reaches its surface origin. Before entry,
insertion depth is negative. Other shanks need not reach the surface together.

The existing nonzero annotation voxel cells are the surface oracle, including
hidden regions. Trace the full insertion line in the forward insertion direction
and use its first occupied cell boundary; enumerate voxel-boundary intersections
without resampling the atlas. For unit insertion direction d, tip T and entry E
(all positions in mm), depth = dot(T-E, d), and DV = T_DV-E_DV. Only floating-point
roundoff, not an additional geometric approximation, is allowed. A line with no
tissue has no surface-relative depth. Horizontal insertion cannot change DV.

## Implementation steps

1. Add shared surface-intersection/reference calculations and rigid translation
   helpers while retaining the saved canonical pose convention and old plan poses.
2. Display signed shank-specific depths; switch shanks without moving the probe.
   Use the surface entry as the AP/ML and tilt pivot, preserving signed travel on
   those edits. Keep initial AP/ML placement on the existing dorsal surface.
3. Export the same per-shank entry/depth definitions in planned coordinates and
   explain the convention in the bundle README and installed quick-start guide.
4. Review the scoped diff and run one focused check of the reported tilted
   four-shank case, zeroing and no-movement selection. Record results and commit/push.

## Compatibility and limits

Keep JSON fields, canonical right-positive ML, rotations, channel routing and
voxel resolution unchanged. UI/CSV ML remains left-positive. Negative displayed
travel is represented by a translated canonical entry, without relaxing the
saved nonnegative depth contract. No full test suite, build or atlas-wide check.

## Outcome

Implemented shared native-voxel line intersections, signed per-shank UI depth and
DV, surface-based pose edits, and matching coordinate CSV/README descriptions.
The complete probe moves rigidly on depth edits. Shank selection only reads its
reference. AP/ML or orientation edits re-intersect the new axis before applying
the retained signed travel; this also handles voxel stair steps when tilting at
zero depth. Existing JSON pose validation and format remain unchanged.

Verification: one focused execution via `PYTHONPATH=src .venv/bin/python -B -`,
using the actual WHS 39 um annotation and bundled NP 2.0 four-shank geometry.
AP=-4 mm, canonical ML=-2 mm, AP tilt=-12 degrees and ML tilt=30 degrees reproduced
the reported legacy shank-3 depth=0.00 mm and DV=0.44 mm. The new shank-3 reference
reports depth=0.479052 mm and DV=0.405805 mm from its axis intersection. For all
four shanks, the check passed: annotation is empty just before and occupied just
after the calculated boundary; zero places the tip at that boundary; -0.5 mm
retracts along the same axis; all 5120 contacts share the same rigid translation;
and reading every reference leaves the saved pose unchanged. Numerical comparison
tolerances were 1e-10 mm / 1e-7 um (roundoff only).

The scoped diff was reviewed. The initial-placement and orientation re-intersection
calls were added after observing the native voxel stair-step offset in that check;
those UI paths and CSV output were inspected, not separately executed. No full
suite, GUI session or standalone build was run. Other atlases and horizontal/missing
surface UI behavior remain unverified in execution. The surface retains native
annotation resolution and can differ from the smoothed visual outline. Ready for
the user-requested commit and push.
