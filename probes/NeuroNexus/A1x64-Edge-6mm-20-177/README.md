# A1x64-Edge-6mm-20-177

Import [the existing geometry JSON](../A1x64-Edge-6mm-20-177.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## neuronexus_activus64

Official Activus 64 channel numbering (0-63). Use only the AV / AVH / AVI / AVIH package variants listed in this map.

- [XML](A1x64-Edge-6mm-20-177__neuronexus_activus64.xml)
- [CellExplorer coordinates](A1x64-Edge-6mm-20-177__neuronexus_activus64.chanCoords.channelInfo.mat)

## neuronexus_h64lp_smartlink64_chronic

H64LP / MRH64LP + SmartLink64 Chronic only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order.

- [XML](A1x64-Edge-6mm-20-177__neuronexus_h64lp_smartlink64_chronic.xml)
- [CellExplorer coordinates](A1x64-Edge-6mm-20-177__neuronexus_h64lp_smartlink64_chronic.chanCoords.channelInfo.mat)

## neuronexus_h64lp_intan_rhd64

H64LP / MRH64LP + Intan RHD64 (C3315 / C3325) only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order.

- [XML](A1x64-Edge-6mm-20-177__neuronexus_h64lp_intan_rhd64.xml)
- [CellExplorer coordinates](A1x64-Edge-6mm-20-177__neuronexus_h64lp_intan_rhd64.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
