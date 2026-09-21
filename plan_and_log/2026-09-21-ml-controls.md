# ML control direction

## Goal and scope

Make positive ML movement follow the user's intended rightward direction and
reverse the ML tilt control. Preserve existing physical placements and the
canonical plan JSON convention (anatomical right-positive ML).

## Steps

1. Use the user's confirmed request: simply reverse the existing ML +/- signs,
   independently of camera orientation.
2. Reverse the paired GUI tilt conversions and update their help text. Keep AP
   tilt, roll, insertion travel, surface lookup, and saved angles unchanged.
3. Apply the confirmed ML position convention at the UI boundary and keep the
   planning coordinate CSV and its README consistent with the controls.
4. Inspect the paired conversions and save/load paths; run at most one lightweight
   changed-file check. No new tests or broad validation.

## Acceptance

- A displayed ML position of +x gives the previous -x position and vice versa;
  the convention stays fixed when the camera rotates.
- A displayed ML tilt of +a gives the previous -a orientation and vice versa.
- Reading controls and writing the same values preserves the complete pose.
- Existing plan JSON loads without reflecting probes or changing atlas mappings.
- CSV entry/tip ML and tilt follow the displayed convention; probe-local geometry,
  atlas coordinates, hardware IDs, and canonical JSON remain unchanged.

## Outcome

Implemented, uncommitted.

- User confirmed a simple sign reversal, rather than camera-dependent controls.
- ML position is negated on control read/write and in the planning CSV; canonical
  poses remain right-positive. ML tilt's paired conversions now use Ry(AP) Rx(ML)
  Rz(roll), so the CSV automatically uses the same reversed tilt convention.
- Help text and each saved bundle's README state the new convention. Existing
  exports are updated on Save & Update; existing JSON plans retain their placement.
- Reviewed the scoped diff and inverse conversion paths. The unchanged save/load
  path continues to serialize canonical poses, including existing saved angles.
- Check passed (exit 0): `PYTHONPYCACHEPREFIX="$ml_check_dir" .venv/bin/python -m
  py_compile src/probe_planner/atlas/coordinates.py
  src/probe_planner/ui/main_window.py src/probe_planner/project/bundle.py`.
  The unique `/tmp/atlaxis-ml-check.XXXXXX` cache directory was removed afterward.
- GUI behavior and numerical execution were not tested; no tests were added.
