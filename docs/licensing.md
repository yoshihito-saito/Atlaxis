# Licensing and source distribution

Atlaxis is GPL-3.0-only. [Third-party notices](../THIRD_PARTY_NOTICES.md) describe
the software and data included or referenced by the project.

## Collect notices for a build

Use the same interpreter and dependencies as the standalone build. The
PyInstaller spec calls `packaging/collect_licenses.py` automatically and includes
the resulting notices. It traverses installed runtime requirements, evaluates
platform/extras markers, checks installed versions against `uv.lock`, and copies
original license and attribution files without rewriting their contents.
PyInstaller and its build dependencies are included when collecting for a build.

For a separate collection, choose an empty output directory:

```sh
uv run --no-sync python packaging/collect_licenses.py --include-build-tool --output build/license-review
```

The result includes an index, original notices and a JSON manifest containing
versions, platform, architecture, source-distribution URLs and SHA-256 hashes.
Unavailable license files and stale Qt/PySide/VTK/PyInstaller notice versions
cause collection to fail. The script makes no network requests and does not
install or import GUI dependencies.

`third_party/licenses/environment/` is the checked-in source-environment
snapshot. Build collection replaces that snapshot inside the application with
the target environment's result. It does not overwrite the repository snapshot.
To update the snapshot, collect to an empty staging directory and review the
replacement. Upstream files under `third_party/licenses/upstream/` retain their
original contents; their manifest records pinned source commits, file URLs and
hashes. Refresh them from those projects when updating dependency versions.

The index may contain more packages than the frozen app. Installed metadata and
RECORD files cannot prove that every embedded native dependency has been found.

## What accompanies the binary

The standalone app includes:

- `LICENSE.md` and `THIRD_PARTY_NOTICES.md`;
- `third_party/licenses/` with the build environment's notices and the pinned
  upstream and probe-data notices;
- this document and `docs/development.md`;
- the ProbeMaps source lock identifying the original bundled XMLs.

PyInstaller places these under its resource directory, usually `_internal/` on
Windows and `Contents/Resources/` in a macOS app. Keep them with the application.

The desktop workflow also creates `Atlaxis-source.zip` from the same Git commit
as the build. It contains application source, the lockfile, build configuration,
documentation and checked-in notices. The workflow uploads artifacts for review;
it does not publish releases.

## Corresponding source

When publishing a binary, publish its matching `Atlaxis-source.zip` alongside it
and provide equivalent access to the corresponding source of bundled GPL/LGPL
components. Keep the source locations clearly linked from the download page.
An application source archive alone does not supply Qt/PySide source.

Source locations are recorded in:

- `third_party/licenses/environment/manifest.json`: exact Python version and
  source archive, plus available locked Python-package sdists and their hashes;
- `third_party/licenses/upstream/manifest.json`: pinned Qt/PySide, VTK and
  PyInstaller source repositories and source archives;
- `uv.lock`: platform wheel URLs and hashes used to resolve the environment.

Before release, obtain the complete corresponding sources for the actual
binaries, including any vendor patches, submodules, generated-source inputs and
scripts/configuration needed to build and install them. Preserve the build's
Python version, OS/architecture and dependency manifest. Qt/PySide build
instructions are in their matching source trees and the
[Qt for Python source-build guide](https://doc.qt.io/qtforpython-6/building_from_source/index.html).
Atlaxis build instructions are in [development.md](development.md).

A source-archive URL or a generic upstream homepage is not, by itself, evidence
that it reproduces a vendor wheel. Verify source completeness and access, and
mirror the required archives with the release when needed. Sources have not
been downloaded and rebuilt as part of this documentation change.

For the GPLv3 option used with Qt/PySide, preserve original notices, provide the
required source and avoid additional restrictions on recipients' GPL rights.
If distributing any component under LGPL instead, also preserve its LGPL/GPL
texts and the applicable replacement/relinking rights. Supply installation
information where required; verify signed macOS packages do not prevent the
permitted use of modified versions. See
[GPLv3 section 6](https://doc.qt.io/qt-6/gpl.html) and
[LGPLv3 section 4](https://doc.qt.io/qt-6/lgpl.html).

## Outstanding release checks

No standalone binary has been built or audited by this change. Before publishing:

1. Resolve permission to redistribute the seven ProbeMaps XMLs. No upstream
   license was found; do not infer permission from public availability.
2. Resolve the WHS atlas citation-page license-link discrepancy for the exact
   package and README images. Other downloaded atlases retain their own terms.
3. Inspect the actual macOS arm64 and Windows bundles for all native components,
   Qt modules/plugins, Python runtime libraries and font assets. Supplement
   notices for any embedded code not covered by the collected originals.
4. Verify complete, matching corresponding-source access and build/installation
   information for the distributed GPL/LGPL components. The supplied URLs are
   source references, not a claim that this verification is complete.

These unresolved items must not be represented as cleared by a successful
notice collection or by the presence of Atlaxis's `LICENSE.md`.
