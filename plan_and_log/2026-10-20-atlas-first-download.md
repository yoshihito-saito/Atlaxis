# First-launch atlas discovery and download

## Goal and scope

Make supported atlas candidates available on a fresh installation and use the
official BrainGlobe 3/S3 distribution for new downloads. Preserve existing v2
data and saved-plan versions, coordinate conventions, physical units, and label
IDs. Build v0.3.0 with the existing desktop workflow, update this PC's Windows
installation, and publish matching Windows/macOS installers and source as Latest.

## Implementation steps

1. Trace the GIN failure and inspect the official S3 reader/data contracts.
2. Update the runtime/dependency and integrate S3 images and meshes, preserving
   bounded image-memory use and a separate reader for existing v2 folders.
3. Make chooser versions explicit and retain coordinate/preset contracts for
   recognized grids; check one fresh Allen mouse loading path.
4. Synchronize package/runtime/lock versions to 0.3.0, commit and tag the release,
   push it, and run the existing native desktop workflow.
5. Verify matching artifacts, install the Windows update, publish the release,
   and record the final outcome and validation limits.

## Findings

- The GIN home page responds, but the catalogue request took approximately
  42 seconds; the original chooser aborted requests after 10 seconds.
- The archive began responding after approximately 64 seconds. Its first 1 MiB
  was valid gzip data, confirming that the archive endpoint was reachable from
  this connection after a slow initial response.
- BrainGlobe 2.3.1 makes repeated catalogue requests and downloads archives without
  request timeouts. BrainGlobe v3's S3 content uses a different data format.
- The earlier candidate-display fix is an existing task-owned change and is kept.

## Decisions and changes

- Initialize the chooser from its existing five supported atlas/version pairs;
  cached, online, and installed versions still override those initial entries.
- Increase the asynchronous catalogue request's inactivity timeout from 10 to
  90 seconds and explain the slow response while candidates remain selectable.
- The initial v0.2.3 fix kept the upstream downloader after one successful first
  download. A subsequent user screenshot exposed an additional preflight failure;
  the follow-up below corrects the archive transport while retaining v2 data.

## Validation and remaining work

- Reviewed the scoped source diff.
- Ran one first-download check through `prepare_storage`, `activate_storage`, and
  `load_atlas` with an isolated temporary data folder containing zero atlas files.
  Downloaded `allen_mouse_50um` v1.2 (approximately 66 MB) and opened annotation
  and reference images, both shape `(264, 160, 228)` at 50 um resolution. The root
  mesh file existed. The operation completed in 362.05 seconds, and temporary
  data were removed after closing the memory maps.
- No package-wide tests or GUI checks were run. Other atlas archives were not
  downloaded in full.

## Desktop release

- The user authorized rebuilding, local installation, and release publication.
- Build commit `9b6c8685cad3a9682f45cc82e60ba47a3326c83b` and annotated tag
  `v0.2.3` were pushed. The
  [desktop build](https://github.com/yoshihito-saito/Atlaxis/actions/runs/39480847095)
  succeeded for Windows x64 and macOS arm64.
- Both downloaded Actions archives matched their API sizes/SHA-256 digests.
  Their source ZIPs matched the tagged commit and package/runtime/lock version
  0.2.3.
- After a normal close request, the user saved and closed the running application.
  The Windows installer exited 0 and the uninstall registry confirmed version
  0.2.3 at `C:\Users\aalab\AppData\Local\Programs\Atlaxis`.
  The installation log is `dist/release-v0.2.3/install-windows.log`.
- The installed Windows installer SHA-256 is
  `206477364f6e8dd84ebf74995717dfda13d0fb9432b12ccdde6ba1cf3fd6e0e8`.
- [Atlaxis v0.2.3](https://github.com/yoshihito-saito/Atlaxis/releases/tag/v0.2.3)
  is published as Latest with the Windows installer, macOS DMG, and matching
  source ZIP. All uploaded sizes/SHA-256 digests matched the prepared files;
  the public Windows installer is the one used for the local update.
- Packaged GUI operations and atlas downloads were not tested. The source-based
  first-download result above is unchanged; native build and artifact checks do
  not establish full GUI or scientific validation.

## v0.2.4 follow-up: archive preflight failure

The user reported `GIN server is down.` when loading Allen mouse after installing
v0.2.3. The upstream downloader probes the GIN home page with a five-second
timeout before fetching the archive. This check is independent of the chooser's
90-second timeout and can block access to an otherwise reachable archive.

Implementation steps:

1. Compare the home-page probe and archive request using the packaged SSL files.
2. Pass the chooser's selected atlas version to the loader and replace the
   upstream preflight/download path with bounded direct resource requests.
3. Download into temporary staging, then publish a fully extracted atlas; retain
   BrainGlobe's existing local-data loading and version checks.
4. Check one fresh Allen mouse download, rebuild v0.2.4, install it, and publish
   matching native installers/source with the existing release workflow.

A direct v2 transport with selected-version forwarding, staged extraction, and
bounded connection retries was implemented but not released. The installed app
and published release remained v0.2.3 at that stage; v0.2.4 was not published.

Follow-up evidence:

- A process using the installed `_ssl.pyd` and bundled CA file reproduced a
  five-second connection timeout to the GIN home page and a ten-second connection
  timeout to the Allen mouse archive.
- The one isolated first-download check with the new transport also failed:
  all three 30-second connection attempts timed out. No atlas was published to
  the temporary data folder; the temporary folder was removed on failure.
- A normal Python/SSL environment likewise timed out connecting to the GIN home
  page and catalogue. Increasing request timeouts alone has not restored access.
- Official S3 manifests for `allen_mouse_50um` versions 3.0 and 3.1 are reachable.
  They describe shape `(264, 160, 228)`, 50 um resolution, and ASR orientation,
  but have independently versioned components. This does not establish data
  equivalence with the v1.2 archive.
- The user explicitly selected migration to BrainGlobe 3/S3 while retaining
  existing atlas data and saved plans. The unsuccessful v0.2.4 approach is
  superseded; its failed connection result is retained above.

## v0.3.0 migration decisions

- Use the official pinned BrainGlobe 3.0.3 reader and its required Python 3.12
  runtime. Existing Neuropixels code requires Python >=3.11 and permits 3.12.
- New atlas data remain versioned separately from v2 folders and saved plans.
  Existing local v2 TIFF/JSON/OBJ data remain readable; a plan requiring an
  unavailable legacy version must request that original data rather than load
  a different version silently.
- Materialize S3 images into an exact, unresampled disk-backed cache in bounded
  slabs. Convert official decoded mesh objects into local OBJ files in the
  reader's ASR/micrometre coordinates; retain the existing rendering pipeline.
- Respect the selected NGFF level's physical translation: express both decoded
  meshes and the existing physical Bregma landmark relative to the first voxel.
  Allen 50 um v3.1 records a 20 um origin on each axis in both image components.
  Image values, label IDs, resolution, pitch and in-vivo scale are unchanged.
- Fetch the selected image level completely before publishing its TIFF cache;
  an interrupted Zarr download must not be treated as complete merely because
  its chunk directory exists. Cache publication uses a temporary file and rename.
- Keep first-launch candidates and show version explicitly. Online discovery
  uses the S3 catalogue and recognized preset versions only.
- Bundle Wasmtime's platform library at its package-relative location, as its
  ctypes loader constructs that location dynamically in the new dependency.

## v0.3.0 validation and release progress

- Reviewed the scoped source diff. Ran the existing `AtlasLoader.run` path once
  with an empty, isolated temporary data folder and Allen mouse 50 um v3.1.
  Official S3 metadata/images/meshes and the mouse CT reference downloaded;
  the annotation and reference opened as disk-backed arrays of shape
  `(264, 160, 228)`, `uint32`/`uint16`, 50 um spacing, ASR orientation.
- The loading path prepared 683 region meshes and a 50,000-cell display outline,
  and reached its loaded signal with the skull available in 350.25 seconds.
  Both NGFF image origins were `(20, 20, 20)` um and the resulting Allen Bregma
  was `(5380, -20, 5680)` um relative to the first voxel. The common origin shift
  cancels in displacement relative to Bregma; pitch and scale are unchanged.
- The process exited 0. Its temporary data folder was removed after exit;
  ignored `.tools/s3-first-load-result.json` and `.tools/s3-first-load.log` retain
  the local result. No tests were added or package-wide suites run.
- Other resolutions, rat volumes, existing legacy-folder runtime loading,
  packaged GUI operation, and anatomical landmark accuracy were not validated.
- Native build/install and release publication remain pending.
