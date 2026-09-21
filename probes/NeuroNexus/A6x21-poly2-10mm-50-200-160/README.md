# A6x21-poly2-10mm-50-200-160

Import [the existing geometry JSON](../A6x21-poly2-10mm-50-200-160.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## provisional

Provisional Channel IDs 0-127: left-to-right shanks, tip-to-base within each shank. Assigned at user request; manufacturer recording wiring is not verified.

- [XML](A6x21-poly2-10mm-50-200-160__provisional.xml)
- [CellExplorer coordinates](A6x21-poly2-10mm-50-200-160__provisional.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
