# ASSY-325D-E-1

Import [the existing geometry JSON](../ASSY-325D-E-1.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## builtin-intan

Preserves the previously audited Atlaxis curated geometry and official wiring.

- [XML](ASSY-325D-E-1__builtin-intan.xml)
- [CellExplorer coordinates](ASSY-325D-E-1__builtin-intan.chanCoords.channelInfo.mat)

