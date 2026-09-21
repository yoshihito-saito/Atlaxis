# A4x16-Poly2-lin-5mm-20s-150-160

Import [the existing geometry JSON](../A4x16-Poly2-lin-5mm-20s-150-160.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## probemaps_normal

Uses the supplied ProbeMaps normal XML configuration (base-to-tip site order). Select only if your recording uses this XML; confirm Channel ID / Site against the actual probe and connection.

- [XML](A4x16-Poly2-lin-5mm-20s-150-160__probemaps_normal.xml)
- [CellExplorer coordinates](A4x16-Poly2-lin-5mm-20s-150-160__probemaps_normal.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
