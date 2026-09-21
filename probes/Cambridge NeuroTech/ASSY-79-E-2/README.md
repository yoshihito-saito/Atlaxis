# ASSY-79-E-2

Import [the existing geometry JSON](../ASSY-79-E-2.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## intan-rhd-16

Intan RHD 16ch C3334/C3335, direct Omnetics connection. Channel IDs are native, zero-based Intan amplifier inputs before recording-system port offsets. Uses inputs 8-23 of a 32-input chip; inputs 0-7 and 24-31 are grounded. Not compacted to 0-15.

- [XML](ASSY-79-E-2__intan-rhd-16.xml)
- [CellExplorer coordinates](ASSY-79-E-2__intan-rhd-16.chanCoords.channelInfo.mat)

