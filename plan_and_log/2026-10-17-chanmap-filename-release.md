# chanMap filename fix and desktop update

## Goal and scope

Save the plan's combined processing map as `chanMap.mat`, preserving its MATLAB
variables, channel ordering and coordinates. Build v0.2.2 with the existing
desktop workflow, then update this PC's Windows installation. Manual
per-IMRO companion names remain independent snapshots.

## Steps

1. Rename the combined output and its documentation/destination protection;
   preserve manifest-based retirement of the previous `channelmap.mat`.
2. Synchronize package/runtime/lock versions to 0.2.2 and review the scoped diff.
3. Commit, push and tag the build commit; run the existing desktop workflow.
4. Verify the matching Windows artifact and install the update locally without
   changing user data.

## Source review

The scoped diff changes the combined output key/name, generated description,
destination protection and release versions. Existing manifest-based cleanup
also retires the old name; unrelated files and manual export snapshots are
preserved. The MATLAB payload construction is unchanged. The staged diff check
passed. No local tests or downstream sorting validation were run.

## Build and installation outcome

Commit `fc1552c131998b2fcc5e4edc1179ff9fd95bb46f` and tag `v0.2.2` were pushed.
[Desktop build 39042961668](https://github.com/yoshihito-saito/Atlaxis/actions/runs/39042961668)
succeeded for Windows x64 and macOS arm64. The downloaded Windows artifact
matched its API size/SHA-256; the accompanying source ZIP matched the build
commit and package/runtime/lock version 0.2.2.

The Windows installer SHA-256 is
`71e4f0e3346bdd3435cc801f4539bef700abeb6ba3de0e80119a3eb25cbc9427`.
Installation exited with code 0, and the local uninstall registry confirms
version 0.2.2 at `C:\Users\aalab\AppData\Local\Programs\Atlaxis`.
The log is `dist/release-v0.2.2/install-windows.log`. GUI operations were not tested.

GitHub Release publication was attempted as part of the inferred update flow but
blocked before execution by automatic approval review: the current request
explicitly authorized push and local installation, not a new public Release.
No Release was created or asset uploaded. Publication awaits explicit approval;
the requested build, push and local installation are complete.
