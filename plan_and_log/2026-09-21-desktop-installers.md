# Desktop installer distribution

## Goal and scope

Replace the platform ZIP downloads with a macOS Apple Silicon DMG and a Windows
x64 setup executable. Keep the existing PyInstaller application, logo, bundled
probes/notices, first-launch data-folder selection and saved user data unchanged.
Installer packaging does not add signing, notarization or automatic publication.

## Steps

1. Package the macOS app in a compressed disk image containing an Applications
   shortcut and concise installation instructions, preserving bundle symlinks.
2. Add an Inno Setup definition that installs the entire Windows bundle per user,
   supplies Start menu/optional desktop shortcuts and normal uninstall support.
   Use a stable application ID and the version from pyproject.toml. Do not delete
   data folders or settings on uninstall/upgrade.
3. Update the manual GitHub workflow to build these installers with native tools
   already on the runners, and upload them with the matching source ZIP.
4. Update installation/build documentation, inspect the scoped diff, commit/push
   and execute the user-authorized desktop workflow. Check both final artifacts.

## Verification and outcome

Implemented DMG staging with ditto, an Applications symlink and installation
instructions, plus hdiutil integrity verification. Added an Inno Setup definition
with a per-user installation directory, stable AppId, bundled icon, Start menu
shortcut, optional desktop shortcut and standard uninstall. Installer version
comes from pyproject.toml. The workflow uploads installers and matching source;
installation/build documentation now describes these formats.

Source and the scoped diff were reviewed. No local PyInstaller build, dependency
installation, broad tests or new test infrastructure.

Committed and pushed as `dfc1bb5`. The manually dispatched [desktop build
35655285060](https://github.com/yoshihito-saito/Atlaxis/actions/runs/35655285060)
completed successfully on macos-14 and windows-2022 at that commit. Both native
PyInstaller builds, installer packaging and artifact uploads succeeded; the macOS
packaging step also ran `hdiutil verify`. Artifacts are `Atlaxis-macOS-arm64`
(10664045905) and `Atlaxis-Windows-x64` (10664326581), containing the DMG or setup
EXE and matching source ZIP. README installation/update/uninstall instructions are
included in that source revision. No Release was published.

Interactive install/uninstall and installed-app GUI operation were not tested.
Signing and notarization are not configured, so OS trust warnings remain possible.
