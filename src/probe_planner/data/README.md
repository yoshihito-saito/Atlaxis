# Atlaxis

Plan electrophysiology probe placement and Neuropixels recording channels in a
3D brain atlas. This is your Atlaxis data folder, selected during first launch.

## Folders

- `atlases/`: downloaded BrainGlobe atlases. Atlases download when first loaded.
- `probes/standard/`: the bundled probe library and its reference files.
- `probes/custom/`: your own probe definitions.
- `planning/`: saved plans, coordinates and channel-map outputs.
- `skulls/`: CT reference surfaces downloaded from their providers and prepared
  on first use. Later atlas loads reuse these compact files; provider terms apply.
- `.atlaxis/`: application metadata and BrainGlobe configuration. Keep this folder.

App updates do not require replacing this data folder. Keep backups of your
plans and custom probes. Standard probe files that you edit are preserved.
This README is created only when missing, so your edits are kept as well.

## Getting started

1. Click **Load atlas**, select an atlas, and verify the Bregma origin.
2. Click **+** in the Probe section, choose a probe, review it and click **Import**.
3. Choose the reference shank and set coordinates, AP/ML tilt and insertion depth.
4. Use the 3D view and sections to inspect the planned placement.
5. Click **Save & Update** to create a plan under `planning/`. Click it again after
   editing to update the same plan and its associated outputs.

Each reference shank uses its own insertion-axis intersection with the annotated
brain surface as zero. **Insertion depth** measures distance along that axis;
**DV (tip)** measures the vertical distance from the same point. Negative depth
means before entry. Switching shanks updates the displayed coordinates without
moving the probe. Entering zero moves the whole probe until the selected tip
reaches the surface; other shanks can remain above or below it. **No surface**
means the axis misses annotated tissue. **Set Bregma** means the atlas coordinate
origin is missing; **Load atlas** means no atlas is loaded.

Choose a supported rat or mouse atlas from **Load atlas**. Bregma is set automatically.

## Neuropixels channel selection

1. Open **Probe plane**, draw a rectangle or polygon, and choose its Region and
   Density. Double-click the final polygon vertex to finish drawing.
2. Region supports multiple checks, such as **CA1 + DG**. A checked parent
   includes its subregions. The drawn ROI still limits the candidate sites.
3. Use a row's **Activate** to assign its channels. **Add ROI** adds another range.
   The bottom **Activate channels** shares remaining channels among unassigned
   ROIs while keeping existing assignments. Counts depend on available sites,
   density and hardware routing. **Reset all** clears the selection.
4. Use **Export** when you need recording files. IMRO fills all 384 hardware
   channels, adding sites outside your targets when necessary. CSV includes all
   exported channels and marks target sites with `is_target=1`.
   The `.selection.json` companion restores your target selection in Atlaxis.

Ordinary probes use all contacts; Neuropixels selection controls are not needed.
Always verify channel IDs against the actual probe, headstage, adapter and
manufacturer wiring documents before recording.

## Documentation

- [Full guide and project](https://github.com/yoshihito-saito/Atlaxis#readme)
- [Probe library and wiring](https://github.com/yoshihito-saito/Atlaxis/blob/main/probes/README.md)
- [License](https://github.com/yoshihito-saito/Atlaxis/blob/main/LICENSE.md)
- [Third-party notices](https://github.com/yoshihito-saito/Atlaxis/blob/main/THIRD_PARTY_NOTICES.md)
