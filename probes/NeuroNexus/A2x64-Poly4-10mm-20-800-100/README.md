# A2x64-Poly4-10mm-20-800-100

Import [the existing geometry JSON](../A2x64-Poly4-10mm-20-800-100.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## neuronexus_activus128

Official Activus 128 channel numbering (0-127). Use only the AV / AVH / AVI / AVIH package variants listed in this map.

- [XML](A2x64-Poly4-10mm-20-800-100__neuronexus_activus128.xml)
- [CellExplorer coordinates](A2x64-Poly4-10mm-20-800-100__neuronexus_activus128.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
