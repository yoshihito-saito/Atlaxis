# chanMap filename fix and desktop update

## Goal and scope

Save the plan's combined processing map as `chanMap.mat`, preserving its MATLAB
variables, channel ordering and coordinates. Build and publish v0.2.2 with the
existing desktop workflow, then update this PC's Windows installation. Manual
per-IMRO companion names remain independent snapshots.

## Steps

1. Rename the combined output and its documentation/destination protection;
   preserve manifest-based retirement of the previous `channelmap.mat`.
2. Synchronize package/runtime/lock versions to 0.2.2 and review the scoped diff.
3. Commit, push and tag the build commit; run the existing desktop workflow.
4. Verify matching artifacts, publish the installers/source and install the
   Windows update locally without changing user data.

## Source review

The scoped diff changes the combined output key/name, generated description,
destination protection and release versions. Existing manifest-based cleanup
also retires the old name; unrelated files and manual export snapshots are
preserved. The MATLAB payload construction is unchanged. No local tests or
downstream sorting validation were run. Desktop build and installation pending.
