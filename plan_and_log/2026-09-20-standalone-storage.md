# Standalone storage and build configuration

Goal: retain the repository layout while standalone/source GUI sessions use a
user-selected persistent data folder, initialized on first launch. Prepare native
macOS/Windows build configuration without building or publishing in this task.

1. Add shared data paths, first-run selection and persistent settings. Create
   probes/standard, probes/custom, atlases and planning; allow an existing atlas
   folder. Configure BrainGlobe privately before importing it.
2. Copy bundled standard probes and track installed hashes. Update only unchanged
   managed files; preserve user edits/custom files. Keep old favorites' relative
   library paths and existing plan formats. Do not move/delete existing plans or
   atlases. CLI companion generation continues to use the checkout library.
3. Add Settings access to folders; changed destinations take effect on restart.
   Add a one-folder PyInstaller spec and manually triggered native build workflow.
4. Document migration/use, inspect scoped diffs and run one lightweight changed-file
   check. No new tests, dependencies installed, full build or GUI verification.

Constraints: no scientific/coordinate/atlas changes, no changes to globally shared
BrainGlobe configuration, no automatic atlas volume copying/downloading or commits.
Existing untracked planning/260920_NP1_test is user data and stays untouched.
First-run cancellation exits before creating the main window. Failed preparation
must not replace the previously saved storage selection. Application upgrades must
never overwrite an edited standard file merely because its path matches a bundle.

## Outcome (2026-09-20, uncommitted)

- Added first-run folder selection, persistent paths, managed standard-probe copies
  with hash-based edit protection, and Settings actions to select/open data folders.
- Existing atlas directories can be reused. BrainGlobe receives a private config
  before its first import. Folder changes are saved for the next launch; existing
  plans/atlases are not migrated or deleted. CLI library generation keeps its
  checkout defaults, and favorite IDs keep their existing relative paths.
- Added a PyInstaller one-folder spec and manual GitHub Actions workflow using
  native macOS/Windows runners. README documents setup, migration and builds.
- Reviewed the scoped source/diff. The one permitted lightweight check passed:
  `PYTHONPYCACHEPREFIX="$check_dir/pycache" .venv/bin/python -m py_compile src/probe_planner/storage.py src/probe_planner/ui/storage_dialog.py src/probe_planner/__main__.py src/probe_planner/probes/library.py src/probe_planner/ui/main_window.py packaging/Atlaxis.spec`
  (`check_dir` was a unique `/tmp/atlaxis-storage-check.XXXXXX` directory and was
  removed afterward; exit code 0).
- No tests, GUI sessions, dependency installs, application builds, commits or pushes
  were run. Frozen-app startup, downloads and exports require native validation;
  signing/notarization and release publishing remain future work.

## Follow-up: one Atlaxis folder

Goal: select only the Atlaxis data folder; always keep atlas downloads in its
`atlases/` subfolder, including when loading a previously saved separate atlas path.

1. Derive the atlas path from the root and save only the root. Stop detecting or
   automatically selecting external BrainGlobe directories.
2. Remove the separate atlas picker. Browsing chooses where to create `Atlaxis`;
   Settings uses the same single-folder selection.
3. Update the documentation and inspect the changed source. Existing external
   downloads stay untouched and may be copied manually into `Atlaxis/atlases/`.

Outcome: implemented the single-folder dialog and root-derived atlas path. Old
settings retain their data root but ignore the separate atlas destination on next
launch. Browse adds `Atlaxis` under the chosen location, without nesting another
`Atlaxis` when that folder itself is selected. Updated Settings labels and README.
Reviewed the changed source and constructor call sites; no tests or runtime checks
were run for this follow-up. GUI behavior and atlas loading remain unverified.

## Native macOS build

User requested a macOS build. Target: this machine's Apple Silicon (arm64).

1. Create an isolated arm64 build environment using the locked dependencies and
   pinned PyInstaller. The existing `.venv` and local uv executable are x86_64;
   preserve them and user data while installing native Python under `.python/`.
2. Build with `packaging/Atlaxis.spec`, resolving concrete packaging failures only.
3. Inspect the produced bundle and package `Atlaxis.app` into a distributable ZIP.
   Record actual results and signing/runtime limitations. No commit or publishing.

Result: macOS build remains incomplete. Installed native CPython 3.11.16 under
`.python/`, synced the locked dependencies into `build/macos-venv`, and installed
PyInstaller 6.22.3 with hooks 2026.7 there. Existing `.venv` was not modified.

Commands run (repository-local cache/install directories supplied via environment):

- `.tools/bin/uv python install cpython-3.11-macos-aarch64-none --no-bin`
- `.tools/bin/uv sync --locked --python "$PWD/.python/cpython-3.11.16-macos-aarch64-none/bin/python3.11"`
  with `UV_PROJECT_ENVIRONMENT="$PWD/build/macos-venv"`.
- `.tools/bin/uv pip install --python "$PWD/build/macos-venv/bin/python" "pyinstaller==6.22.3"`
- `PYINSTALLER_CONFIG_DIR="$PWD/build/pyinstaller-cache" MPLCONFIGDIR="$PWD/build/matplotlib" BRAINGLOBE_CONFIG_DIR="$PWD/build/brainglobe-config" build/macos-venv/bin/python -m PyInstaller --noconfirm packaging/Atlaxis.spec`

The first build reached arm64 executable assembly, then failed with permission
denied while copying PyInstaller's `bootloader/Darwin-64bit/runw`, followed by a
missing-file error. Before the cause was known, PyInstaller was reinstalled from
cache and a second build started. The user then provided an antivirus quarantine
screenshot naming `runw` and a `FileRepMalware` detection. Stopped that build with
SIGTERM (exit 143). No app/ZIP was completed, launched, signed or distributed.

The quarantine explains the disappearing file. Official PyInstaller documentation
acknowledges bootloader false positives, but this particular detection has not
been cleared or established to be a false positive:
https://www.pyinstaller.org/en/stable/bootloader-building.html
No antivirus exclusion, disablement or quarantine restoration was performed.
Resolve the detection before retrying the build; GUI validation remains pending.

## Logo integration and requested commit/push (2026-09-21)

Goal: include the user's existing logo in native builds and commit/push the
standalone storage/build work. Do not regenerate or modify the supplied artwork.

1. Set macOS bundle and Windows executable icons from `logo/Atlaxis.icns` and
   `logo/Atlaxis.ico`.
2. Include `logo/Atlaxis.png` in frozen/wheel resources and set the Qt application
   icon before showing setup or main windows; retain source-checkout support.
3. Inspect the scoped diff, run one syntax check, update documentation, then
   commit the related changes and push `main`. Do not restart the quarantined
   local build or dispatch the manual build workflow in this step.

Outcome: wired all three supplied icon files into the platform-specific build and
Qt runtime paths; wheel packaging also includes the PNG. The frozen entrypoint
resolves resources relative to the imported package, not its relocated script.
Reviewed the related source/diff and inspected the provided PNG/ICNS/ICO formats.
Syntax check passed (exit 0):
`PYTHONPYCACHEPREFIX="$check_dir/pycache" .venv/bin/python -m py_compile src/probe_planner/__main__.py packaging/Atlaxis.spec`
using a unique `/tmp/atlaxis-logo-check.XXXXXX` directory, removed afterward.
No new application build, GUI validation or tests were run. Antivirus detection
remains unresolved. The user authorized committing/pushing these changes with the
earlier standalone storage/build work; generated environments and user data are
excluded. Commit/push results are reported in the task response.
