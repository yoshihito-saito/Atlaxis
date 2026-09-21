# Atlases with orphan annotation labels

## Goal and scope

Do not reject an otherwise readable atlas because annotation label 17714 (or
another positive ID) is absent from its structures table. Preserve original voxel
IDs, anatomy, known region metadata and coordinate calibration. Unknown labels
must be explicitly identified rather than mapped to background or a guessed region.

## Steps

1. Replace the missing-metadata failure with application-local placeholders:
   original ID, an explicit Unknown name/acronym, neutral gray and no inferred parent.
2. Derive missing-region surfaces from their native annotation label, bypassing
   backend ontology lookups that cannot resolve the missing ID. Keep the existing
   handling of known regions, the Brain filter and Bregma requirements unchanged.
3. Show a persistent missing-metadata notice in the atlas information and tooltip.
4. Inspect the scoped diff and run one focused real-atlas check of the orphan label
   metadata and surface. Do not download atlases, build all region meshes, or add tests.

## Verification and outcome

Implemented local Unknown placeholders and native-label surface generation;
atlas information now reports missing metadata and lists the original IDs in its
tooltip. No downloaded atlas files, original annotations, known structure records
or Bregma presets were changed. Known Brain subtree filtering remains unchanged;
an orphan label is not assigned an inferred anatomical parent.

Ran one focused check via `PYTHONPATH=src .venv/bin/python -B -` against the installed
`admba_3d_p28_mouse_16.752um_v1.1` annotation and structures. Confirmed the original
table lacks 17714, added the application-only Unknown description, and generated
an 80-cell native surface with finite coordinates. The read-only annotation and
original ontology remained untouched; all known records retained their identity.
The diff was reviewed. Full GUI atlas loading and other atlas datasets have not
been exercised; errors unrelated to missing region metadata are outside this fix.

Previous Windows-build correction a69d57b is already pushed; triggering a fresh
remote build was interrupted because browser control was not approved. This
atlas correction is to be included in the next user-authorized build.
