# Neuropixels-2.0-four-shank

Import [the existing geometry JSON](../Neuropixels-2.0-four-shank.json).

XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;
MAT row i+1 always describes device channel i. XYZ are local micrometers.
XML groups list sites base-to-tip within each left-to-right shank.
Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.
Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to
`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;
merge actual acquisition metadata before use.

Select active channels in Atlaxis, then Save & update. The planning folder
receives current per-probe XML/chanCoords companions. No static all-site
acquisition map is supplied. IMRO remains a separate manual Export.
