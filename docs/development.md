# Development setup

[Back to README](../README.md)

The standalone app includes its Python environment. These steps are for
contributors running or building Atlaxis from source.

## Install and run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then:

```sh
git clone https://github.com/yoshihito-saito/Atlaxis.git
cd Atlaxis
uv sync --locked
uv run atlaxis
```

The repository selects Python 3.11 through `.python-version`; `uv sync --locked`
creates `.venv` and installs the pinned dependencies from `uv.lock`, including
BrainGlobe and NeuroCarto. No separate NeuroCarto server is needed.
If using a repository-local uv installation, run `.tools/bin/uv run atlaxis`.

macOS Apple Silicon and Windows x64 are the intended desktop platforms.
Source runs use the same first-launch data-folder dialog as packaged apps.
Atlas volumes download on demand and are not part of the environment install.

## Build a standalone app

[`packaging/Atlaxis.spec`](../packaging/Atlaxis.spec) describes a native PyInstaller one-folder build including
Python, dependencies and the probe library. Atlas volumes and user plans are not
bundled. The supplied `logo/Atlaxis.icns` is the macOS app icon, `logo/Atlaxis.ico`
is the Windows executable icon, and `logo/Atlaxis.png` is included for Qt windows
in source, wheel and standalone launches. Build on the target OS with Python 3.11:

```sh
uv sync --locked
uv pip install "pyinstaller==6.22.3"
uv run --no-sync python -m PyInstaller --noconfirm packaging/Atlaxis.spec
```

macOS produces `dist/Atlaxis.app`; Windows produces `dist/Atlaxis/Atlaxis.exe`
with its required sibling files. GitHub Actions' **Build standalone desktop apps**
workflow is manually triggered and packages these as installers. It uses macOS
`hdiutil` and the Inno Setup compiler already installed on the Windows runner.
It does not publish releases automatically.

On macOS, package the app with:

```sh
bash packaging/build_macos_dmg.sh
```

This produces `dist/Atlaxis-macOS-arm64.dmg` containing the app, an Applications
shortcut and installation instructions. `ditto` preserves app bundle symlinks;
`hdiutil verify` checks the resulting compressed disk image.

On Windows with Inno Setup 6 installed, run in PowerShell:

```powershell
$appVersion = uv run --no-sync python -c "import pathlib, tomllib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "/DAppVersion=$appVersion" packaging/Atlaxis.iss
```

This produces `dist/Atlaxis-Windows-x64-Setup.exe`. It installs the complete bundle
under the current user's `LocalAppData\Programs\Atlaxis`, adds a Start menu shortcut
and offers an optional desktop shortcut. A stable AppId retains the installation
location across upgrades. Uninstall removes installed app files, not the user's
chosen atlas/probe/plan data folder or Qt settings. The data folder is still chosen
by Atlaxis on first launch, not by the installer.

Upload the DMG, setup EXE and matching `Atlaxis-source.zip` to a release targeting
the build commit. Actions downloads wrap each installer/source pair in an artifact
ZIP; extract that outer ZIP before uploading the individual release assets.
Developer ID signing, Apple notarization, Windows signing and interactive
installation/GUI validation remain separate release tasks.

The build collects third-party notices from its own environment and bundles them
with the app. The workflow also creates a matching application source archive.
Before publishing, follow the [licensing and source distribution instructions](licensing.md),
including the outstanding probe-data permission and native-library checks.

## Development notes

Reusable logic and the Qt UI live under `src/probe_planner/`. The repository's
`probes/` is the distribution source; use the data folder's `probes/custom/`
for personal designs. See the [probe library](../probes/README.md) for its
source provenance and regeneration commands.

Before importing BrainGlobe, startup sets the process-local `BRAINGLOBE_CONFIG_DIR`
to `.atlaxis/brainglobe`. Global BrainGlobe configuration files are not modified.
Atlas downloads remain optional; only selecting **Load** downloads a volume.
