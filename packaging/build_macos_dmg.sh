#!/bin/bash
# Wrap the completed app without changing its bundle or first-launch setup.
set -euo pipefail
cd "$(dirname "$0")/.."

dmg_stage=$(mktemp -d "${TMPDIR:-/tmp}/atlaxis-dmg.XXXXXX")
trap 'rm -rf "$dmg_stage"' EXIT
ditto dist/Atlaxis.app "$dmg_stage/Atlaxis.app"
ln -s /Applications "$dmg_stage/Applications"
cp packaging/INSTALL-macOS.txt "$dmg_stage/Installation.txt"
hdiutil create -volname Atlaxis -srcfolder "$dmg_stage" -ov -format UDZO \
    -fs HFS+ dist/Atlaxis-macOS-arm64.dmg
hdiutil verify dist/Atlaxis-macOS-arm64.dmg
