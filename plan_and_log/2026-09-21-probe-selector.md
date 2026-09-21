# Probe selection and favorites

## Follow-up: remove inside the dropdown (2026-09-21)

Move removal from the external action row into each probe entry in the left
dropdown. Keep normal selection, full-name tooltips and the summary selector.

1. Add opt-in row removal to ProbeSelector with a separate click target that
   does not activate a different probe before removal.
2. Connect it to the existing MainWindow removal path; remove the old button.
3. Inspect the scoped diff and run one focused Qt interaction check covering
   selection, removal and the ordinary non-removable dropdown.

Outcome (uncommitted): the left dropdown now draws a separate × target per row,
with a full-name removal tooltip and Delete-key access inside the popup. Removal
closes the popup before invoking the existing plan-probe removal handler. Clicking
the name still selects it; a press on × released elsewhere cancels removal. The
external × button was removed, and the summary dropdown remains selection-only.

Scoped source changes inspected. One focused check passed (exit 0):
`QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/python -B -`, using the three
catalog Neuropixels names and QTest events. It covered normal selection, removing
a different row without first selecting it, drag cancellation, Delete-key and
last-row removal, and ordinary summary-dropdown selection. No test files, broad
suite, full application launch or build were added/run.

The reported `TSMSendMessageToUIServer` log was not reproduced. Apple's installed
CFMessagePort.h defines -1 as kCFMessagePortSendTimeout; Apple documents TSM as
part of the text-input system. This single log does not establish an application
failure or its cause. No input-method settings or log suppression were changed.

## Original dropdown implementation

Goal: use a vertical dropdown like Reference shank, following the user's
clarification, with full-name hover text, a smaller + and a visible Favorite button.

1. Replace both probe tab headers with synchronized dropdowns. Provide full names
   in hover text and a wider, vertically scrolling popup for long names.
2. Keep + fixed and smaller. Provide a visible Favorite button that opens a table;
   clicking a row loads that saved template through the existing import preview.
   Preserve star registration/removal and removal of the selected plan probe.
3. Keep summary pages in QStackedWidget, preserving per-probe views/zoom and the
   selection on add/remove. Empty selectors must not create/import a probe.
4. Review these paths and run one lightweight changed-file check. No new tests,
   full GUI launch or build. Discard the superseded horizontal-scroll implementation.

Scope: probe navigation only. Preserve existing unrelated README/docs and current
UI changes. No coordinate, atlas, import/export or saved-plan semantics change.

Outcome (uncommitted): implemented synchronized probe dropdowns with explicit
full-name tooltip handling and wider popups, a 22 px + button, a visible Favorite
table picker, and selected-probe star/remove controls. Favorite rows carry their
stable keys so sorting cannot load the wrong template. Selection still uses probe
IDs and retained summary widgets. The superseded horizontal-scroll file was removed.

Reviewed the source for empty lists, selecting either dropdown, adding/removing the
selected probe, canceling favorites, and sorted favorite rows. One syntax check
passed (exit 0):
`PYTHONPYCACHEPREFIX="$check_dir/pycache" .venv/bin/python -m py_compile src/probe_planner/ui/main_window.py src/probe_planner/ui/probe_selection.py src/probe_planner/ui/style.py`
with a unique `/tmp/atlaxis-probe-selector-check.XXXXXX` directory removed afterward.
GUI rendering/interactions were not run. No new tests, builds, commits or pushes.
