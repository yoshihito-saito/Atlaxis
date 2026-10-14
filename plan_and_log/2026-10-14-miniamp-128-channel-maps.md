# Mini-Amp-128 H20 and E-1 channel maps

## Goal and scope

Add selectable Mini-Amp-128 wiring to the existing H20 and E-1 128-site probes,
using the two user-supplied Cambridge NeuroTech maps. Preserve physical Site IDs,
geometry, the Built-in Intan default, and unrelated working-tree changes.

## Implementation

1. Transcribe both maps against the existing shank/face/site conventions and
   record the supplied image titles, revision dates and SHA-256 hashes.
2. Retain additional headstage profiles during Cambridge library conversion
   and update only the two affected offline JSONs and manifest entries.
3. Document profile selection and saved-plan behavior; inspect the scoped diff
   and run one lightweight check of the two profiles.

## Outcome and verification

- Added Mini-Amp-128 H20 and Mini-Amp-128 E-1-D / E-2-D to the existing
  Headstage selector. The Built-in Intan default and all geometry remain intact.
- H20 uses A-D shanks with remote channels 127/95/63/31. E-1 uses D-A shanks
  in the common front projection for both faces, without a second back-face mirror.
- The source wiring tables retain the additional profiles; the converter now
  preserves and validates them. Only the two offline JSONs and their manifest
  entries were updated. Existing saved plans/favorites require re-import.
- Source provenance identifies the supplied PNGs by title, map revision date
  and SHA-256; no public Mini-Amp map URL was verified.
- Scoped diff inspection completed. One lightweight check loaded the two JSONs
  through the existing importer/headstage mapper and compared all 256 pairs to
  the supplied spatial tables. Both covered channels 0-127 exactly once, matched
  the development profiles, and retained the Built-in Intan default.
- No new tests, full library regeneration, broad suite, GUI check or physical
  hardware validation was run. Remaining validation is GUI/actual recording
  hardware confirmation by the user. No commit was requested or made.
