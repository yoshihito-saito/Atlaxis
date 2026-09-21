# ASSY-236-H8

Import [the existing geometry JSON](../ASSY-236-H8.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## mini-amp-64-v1

Direct ASSY-236 connection: probe Bottom to J1, Top to J2. REF/GND are not recording channels.

- [XML](ASSY-236-H8__mini-amp-64-v1.xml)
- [CellExplorer coordinates](ASSY-236-H8__mini-amp-64-v1.chanCoords.channelInfo.mat)

