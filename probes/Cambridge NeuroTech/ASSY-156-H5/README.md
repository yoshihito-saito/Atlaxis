# ASSY-156-H5

Import [the existing geometry JSON](../ASSY-156-H5.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## intan-rhd-64

Intan RHD 64ch C3315/C3325, direct Omnetics connection. Channel IDs are native, zero-based Intan amplifier inputs before recording-system port offsets. Front Omnetics mates with the chip-side headstage connector; Back with the opposite connector.

- [XML](ASSY-156-H5__intan-rhd-64.xml)
- [CellExplorer coordinates](ASSY-156-H5__intan-rhd-64.chanCoords.channelInfo.mat)

