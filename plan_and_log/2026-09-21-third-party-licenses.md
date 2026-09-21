# Third-party distribution notices

## Goal and scope

Include third-party license texts, attribution, source locations and build
instructions alongside Atlaxis's GPL-3.0-only license. Preserve the existing UI
and README work. Do not publish a release or claim a complete binary compliance
audit without a built artifact.

## Steps

1. Inspect installed dependency notices and the provenance of bundled probe data.
2. Collect original license/notice files with versions and source references;
   supplement Qt/PySide, Python and PyInstaller notices where needed.
3. Include notices in standalone builds and document matching source distribution
   and platform-specific collection in the developer instructions.
4. Run one focused collection check, inspect the scoped diff, and record any
   unresolved third-party permissions or release checks.

## Constraints

- Preserve original notices verbatim; do not assign Atlaxis's license to upstream
  code, probe data or atlas data.
- A metadata license identifier is not a substitute for the license text.
- Collect from the actual build environment; the current macOS x86_64 environment
  is not evidence of the contents of macOS arm64 or Windows binaries.
- No dependency installation, app build, broad tests or runtime UI changes.

## Result (uncommitted)

- Added `THIRD_PARTY_NOTICES.md`, original notices for 49 installed dependency
  distributions and Python, and 274 original Qt/PySide/VTK/PyInstaller upstream
  license/attribution files (about 2.8 MB including the environment snapshot).
- Recorded immutable upstream source references and hashes. Included the existing
  ProbeInterface MIT notice and the two CC texts referenced by the WHS pages.
- Added environment-specific collection to the standalone spec and license files
  to package metadata. The desktop workflow now also archives application source
  from its build commit. README remains a single license/notices link line.
- Documented corresponding-source access and developer build steps. No binary,
  source release or external publication was created by this task.

## Verification

Ran the focused collection command successfully:

```sh
.venv/bin/python packaging/collect_licenses.py --output third_party/licenses/environment
```

Result: 49 distributions plus Python; original upstream file hashes and copied
notice bytes checked by the collector. Inspected the task's diff and generated
index/manifest. After source review, removed a silent skip for missing installed
notice files; missing files now raise on read. This small guard correction was
reviewed in source, not followed by another execution.

No tests, package build, standalone build, Windows/macOS arm64 execution or
complete native binary/source audit was run. Existing UI changes and other
unrelated work were left intact.

## Remaining release requirements

- ProbeMaps XML redistribution permission is unverified; no upstream license was
  located. Do not invent a license or infer permission from public availability.
- WHS project/citation pages say CC BY 4.0 but the citation page links to CC BY-SA
  4.0. Confirm terms for the exact atlas package and derived README images.
- Inspect actual target binaries for additional native notices, source completeness
  (including vendor build inputs), and applicable installation/relinking rights.
- The current snapshot excludes PyInstaller because it is not installed locally;
  its pinned upstream texts are included, and the build collects it and its
  dependencies after the workflow's existing installation step.

## Windows checkout follow-up (2026-09-21)

Build run 35650868482 on commit ae9a766 failed on Windows with
`Upstream notice has changed: pyinstaller/COPYING.txt`. The macOS build produced
its artifact. The failed check reads the tracked upstream notice, not an
installed package's license. No repository attributes currently prevent Windows
checkout line-ending conversion from changing those hash-locked bytes.

Scope and steps:
1. Preserve original upstream notice bytes during Git checkout with a targeted
   `.gitattributes` rule; leave notice files, expected hashes and strict validation intact.
2. Run one focused Git checkout-filter check with `core.autocrlf=true` on the
   reported file, comparing the previous and corrected checkout hashes.
3. Review the two-file change and commit/push the build correction. A fresh
   Windows workflow run is still required to verify the complete build.

Added `third_party/licenses/upstream/** -text`; strict SHA-256 validation and
all original notice files remain unchanged. The focused check ran via
`.venv/bin/python -B -`, using Git's `cat-file --filters` with
`core.autocrlf=true`. The first invocation did not isolate the previous attributes
because it still ran inside the real working directory; after correcting the
working directory, the single rerun passed. The previous checkout introduced 648
CRLF sequences and hash `2f715155...`; the corrected checkout retained the manifest
hash `0598064c...`. This reproduces the reported mismatch without weakening it.
The targeted diff was reviewed. No local app build was run.

The user subsequently requested completing the GitHub build from Codex as well;
dispatch and target-platform build verification are now in scope.
