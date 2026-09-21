# A2x32-6mm-70-200-177

Import [the existing geometry JSON](../A2x32-6mm-70-200-177.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## neuronexus_activus64

Official Activus 64 channel numbering (0-63). Use only the AV / AVH / AVI / AVIH package variants listed in this map.

- [XML](A2x32-6mm-70-200-177__neuronexus_activus64.xml)
- [CellExplorer coordinates](A2x32-6mm-70-200-177__neuronexus_activus64.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
