# A8x8-Edge-5mm-50-150-177

Import [the existing geometry JSON](../A8x8-Edge-5mm-50-150-177.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

## neuronexus_h64lp_smartlink64_chronic

H64LP / MRH64LP + SmartLink64 Chronic only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order.

- [XML](A8x8-Edge-5mm-50-150-177__neuronexus_h64lp_smartlink64_chronic.xml)
- [CellExplorer coordinates](A8x8-Edge-5mm-50-150-177__neuronexus_h64lp_smartlink64_chronic.chanCoords.channelInfo.mat)

## neuronexus_h64lp_intan_rhd64

H64LP / MRH64LP + Intan RHD64 (C3315 / C3325) only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order.

- [XML](A8x8-Edge-5mm-50-150-177__neuronexus_h64lp_intan_rhd64.xml)
- [CellExplorer coordinates](A8x8-Edge-5mm-50-150-177__neuronexus_h64lp_intan_rhd64.chanCoords.channelInfo.mat)

## neuronexus_a64_smartlink64_acute

A64 / MRA64 / OA64LP + SmartLink64 Acute only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order. Not for OA64LP V2.

- [XML](A8x8-Edge-5mm-50-150-177__neuronexus_a64_smartlink64_acute.xml)
- [CellExplorer coordinates](A8x8-Edge-5mm-50-150-177__neuronexus_a64_smartlink64_acute.chanCoords.channelInfo.mat)


Any original ProbeMaps XML is kept separately in `ProbeMaps/`.
