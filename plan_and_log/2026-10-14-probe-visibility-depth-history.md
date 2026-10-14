# Probe visibility, depth, and edit history

## Goal and scope
Add a per-probe eye control for the 3D scene, make probe contacts obey the
shared depth buffer so skull/probe bases/drives can occlude them, and add
Ctrl+Z / Ctrl+Shift+Z for plan edits. Preserve existing geometry, routing,
camera controls, and unrelated uncommitted work.

## Steps
1. Persist each probe's visible state with a backward-compatible default and
   connect an eye control to the selected probe and its 3D actors/drive.
2. Render contacts in the main scene depth buffer so opaque skull, other probe
   bodies, and drives can occlude them by camera angle.
3. Capture bounded plan-state snapshots at existing edit completion points;
   wire Undo/Redo shortcuts and restore controls, scene, and dirty state.
4. Review the scoped diff and run at most one lightweight changed-file check
   if needed, then record behavior boundaries and unverified GUI behavior.

## Result and boundaries
Each probe now has a saved `visible` flag (older plans default to visible).
The eye control affects that probe's 3D body, contacts, base, and mounted drive;
it does not remove channels or alter scientific exports. Contact actors now
share the main scene depth buffer with the opaque skull, bases, and drives.
For probes without supplied body geometry, display-only contact markers are
placed 1 um outside the generated schematic shaft so they remain visible from
their face; model coordinates are unchanged. A deliberately translucent skull
can still show geometry through it.

Undo/Redo captures up to 100 plan states at existing edit completion points,
including pose, probe selection/visibility, channel/ROI edits, drive, skull,
and calibration. Restoring a state refreshes controls and the scene while
keeping the camera angle. Camera movement, atlas loading, region display
filters, and favorites are outside plan history.

Reviewed the scoped source diffs, preserving pre-existing uncommitted work.
One `ast.parse` check of main_window.py passed before the final guarded-action
and schematic-marker edits; those final edits were source-inspected only. No
GUI run, visual occlusion check, save/load round trip, or broad tests were run.
Runtime appearance and keyboard focus behavior remain for user validation.

## Eye icon follow-up
Replace the Unicode eye/combining-slash text with a QPainter-drawn eye and
slashed-eye icon. Remove the visibility button's inherited horizontal padding
so its 18 px icon fits the existing 27 px button. Keep visibility, tooltip and
enablement behavior unchanged. Verify only this button's offscreen rendering;
the full application and 3D behavior remain outside this check.

Scoped diffs were reviewed. The offscreen render of the visible, hidden and
disabled 27 px buttons was visually inspected: eye/slashed-eye icons fit and
remain visible. The preview was rendered once more to the visualization
folder after the sandbox temporary output was unavailable for inspection.
No full application GUI, visibility toggle, 3D occlusion or broad checks ran.

## Per-probe indicator and orientation cube follow-up
Keep the shared eye button's icon tied to its checked state using explicit
On/Off icon images, and handle user clicks rather than programmatic state
changes. Toggle the selected probe's own `visible` flag, then synchronize the
button from that flag. Preserve all other probes' flags and scene visibility.
Also increase the upper-right orientation cube's edge width slightly to 1.5.
Review the scoped diff and run one focused visibility interaction check.

The eye button now has explicit On/Off pixmaps in one QIcon. Refreshing the
selected probe only synchronizes its checked state and tooltip. Only `clicked`
changes visibility, toggling the selected probe's own flag; programmatic
selection refreshes do not mutate probe visibility. Cube edges now use 1.5.
The scoped source diffs were reviewed.

The focused two-probe interaction check could not complete in this environment.
The first attempt with PyVista offscreen mode lacked an interactor. One retry
with Qt's offscreen platform and the normal interactor failed to initialize
Windows OpenGL (invalid pixel format / OpenGL 3.2 unavailable). Neither attempt
reached the interaction assertions. No environment repair or broader checks
were performed. Actual switching, icon/scene synchronization and the cube's
rendered appearance remain unverified in the running application.
