# ASSY-77-M1v2

Import [the existing geometry JSON](../ASSY-77-M1v2.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## intan-rhd-64-a64-om32x2

Intan RHD 64ch C3315/C3325 via Cambridge A64-Om32x2. Channel IDs are native, zero-based Intan amplifier inputs before recording-system port offsets. Front Omnetics mates with the chip-side headstage connector; Back with the opposite connector. Other adapter brands / wiring are not interchangeable.

- [XML](ASSY-77-M1v2__intan-rhd-64-a64-om32x2.xml)
- [CellExplorer coordinates](ASSY-77-M1v2__intan-rhd-64-a64-om32x2.chanCoords.channelInfo.mat)

