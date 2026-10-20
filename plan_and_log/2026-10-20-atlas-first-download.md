# First-launch atlas discovery and download

## Goal and scope

Make supported atlas candidates available on a fresh installation and allow their
first download despite the observed slow GIN response. Preserve the existing
BrainGlobe v2 data format, atlas versions, coordinates, and saved-plan behavior.
Build v0.2.3 with the existing desktop workflow, update this PC's Windows
installation, and publish matching Windows/macOS installers and source as Latest.

## Implementation steps

1. Trace catalogue and archive requests and identify the failing connection stage.
2. Correct the observed request/timeout behavior while retaining supported-version
   checks and immediate first-launch candidates.
3. Review the scoped diff and check one first download in an isolated data folder.
4. Synchronize package/runtime/lock versions to 0.2.3, commit and tag the release,
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
- Keep the existing BrainGlobe v2 downloader and scientific data contracts. The
  actual first download succeeded, so no backend replacement was needed.

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
