# ASSY-37-H7b

Import [the existing geometry JSON](../ASSY-37-H7b.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## intan-rhd-32-a32-om32

Intan RHD 32ch C3314/C3324 via Cambridge A32-Om32. Channel IDs are native, zero-based Intan amplifier inputs before recording-system port offsets. Other adapter brands / wiring are not interchangeable.

- [XML](ASSY-37-H7b__intan-rhd-32-a32-om32.xml)
- [CellExplorer coordinates](ASSY-37-H7b__intan-rhd-32-a32-om32.chanCoords.channelInfo.mat)

