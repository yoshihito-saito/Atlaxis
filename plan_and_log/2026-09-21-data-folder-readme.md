# Data-folder README

Goal: provide an installed, locally readable quick-start guide in the user's
chosen Atlaxis data folder. macOS apps have no separate installer, so first-run
folder preparation creates the guide; existing installations receive it on the
next launch if missing. Never overwrite an existing README or user data.

1. Add a self-contained English guide as package data, with working external
   links to the full documentation rather than missing local image/doc links.
2. Include it in desktop builds and copy it to the data-folder root during the
   existing preparation path. Python wheels include it inside the package.
3. Mention the guide in setup and repository installation instructions.
4. Inspect the diff and perform one focused storage-preparation check. Do not run
   a local application build or broad validation. Commit and push this change
   along with the previously requested multi-region selection commit.

Outcome: added the packaged quick-start guide, desktop data inclusion and the
create-if-missing step in prepare_storage. Setup and installation instructions
now mention README.md. Existing README files are intentionally preserved rather
than refreshed automatically. No settings, atlas locations or plans are moved.

Scoped source/diff review completed. One focused check passed (exit 0):
`PYTHONPATH=src .venv/bin/python -B -`, calling the real prepare_storage in a
temporary data folder with the bundled probe library. The installed README
matched the packaged guide, normal data folders were present, and a second setup
preserved edited README content. Temporary files were cleaned. Desktop/wheel
builds and full GUI validation were not run.
