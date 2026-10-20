"""Versioned chooser policy and local v2/v3 atlas discovery."""

from pathlib import Path


# Presets recognize these grids; saved plans can still request other local data.
LEGACY_VERSIONS = {
    "whs_sd_rat_39um": "1.2",
    "whs_sd_swc_female_rat_39um": "1.0",
    "allen_mouse_10um": "1.2",
    "allen_mouse_25um": "1.2",
    "allen_mouse_50um": "1.2",
}
S3_VERSIONS = {name: "3.1" if name.startswith("allen_mouse_") else "3.0"
               for name in LEGACY_VERSIONS}


def supported_version(name, version):
    return (version == LEGACY_VERSIONS.get(name)
            or name in S3_VERSIONS and version in (
                {"3.0", "3.1"} if name.startswith("allen_mouse_") else {"3.0"}))


def local_atlases(root: Path):
    """Return explicit name/version pairs; a v3 manifest may precede its chunks."""
    pairs = set()
    for metadata in root.glob("*_v*/metadata.json"):
        name, version = metadata.parent.name.rsplit("_v", 1)
        pairs.add((name, version))
    for manifest in (root / "brainglobe-atlasapi" / "atlases").glob("*/*/manifest.json"):
        pairs.add((manifest.parent.parent.name, manifest.parent.name.replace("_", ".")))
    return pairs
