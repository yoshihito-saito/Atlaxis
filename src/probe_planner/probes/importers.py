"""Import independent geometry and acquisition metadata; no basename required."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from scipy.io import loadmat

from .model import ChannelMap, Contact, ProbeGeometry, ProbeBody
from .mounting import with_package_base


def geometry_from_dict(data):
    return ProbeGeometry(
        name=data["name"], contacts=[Contact(**c) for c in data["contacts"]],
        tip_um=tuple(data["tip_um"]), y_to_base=data["y_to_base"], units=data["units"],
        bodies=[ProbeBody(**body) for body in data.get("bodies", [])],
        metadata=data.get("metadata", {}),
        mounting_base=ProbeBody(**data["mounting_base"]) if data.get("mounting_base") else None,
    )


def load_geometry_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    geometry = geometry_from_dict(data["geometry"])
    channels = ChannelMap(**data["channel_map"])
    channels.validate(geometry)
    geometry = with_package_base(geometry, channels)
    return geometry, channels


def _vector(data, key, count=None, integer=False):
    value = np.atleast_1d(data[key]).reshape(-1)
    if not np.issubdtype(value.dtype, np.number) or not np.isfinite(value).all():
        raise ValueError(f"chanCoords.{key} must contain finite numeric values.")
    if count is not None and len(value) != count:
        raise ValueError(f"chanCoords.{key} has a different number of contacts.")
    if integer and (np.any(value != np.floor(value)) or np.any(value > 2**31 - 1)):
        raise ValueError(f"chanCoords.{key} must contain integer IDs.")
    return value.astype(int if integer else float)


def load_cellexplorer(path: Path, tip_um, y_to_base):
    """Read MATLAB <=7.2. channel is explicitly 1-based, not a contact ID.

    Raw x/y/z remain unchanged. Absent z means planar geometry; absent shank
    explicitly means one shank. Absent channel is rejected to avoid guessing.
    """
    try:
        data = loadmat(path, simplify_cells=True)["chanCoords"]
    except NotImplementedError as error:
        raise ValueError("MATLAB v7.3 is unsupported; save chanCoords with MATLAB '-v7'.") from error
    if not isinstance(data, dict) or not {"x", "y", "channel"}.issubset(data):
        raise ValueError("MAT requires chanCoords.x, y and explicit 1-based channel IDs.")
    x = _vector(data, "x")
    y = _vector(data, "y", len(x))
    z = _vector(data, "z", len(x)) if "z" in data else np.zeros(len(x))
    shanks = _vector(data, "shank", len(x), True) if "shank" in data else np.zeros(len(x), int)
    channels = _vector(data, "channel", len(x), True) - 1
    if not len(x) or np.any(channels < 0):
        raise ValueError("CellExplorer channels must be nonempty positive 1-based IDs.")
    contacts = [Contact(f"site_{i}", int(s), float(a), float(b), float(c))
                for i, (s, a, b, c) in enumerate(zip(shanks, x, y, z))]
    geometry = ProbeGeometry(path.stem, contacts, tuple(tip_um), y_to_base)
    mapping = ChannelMap({c.contact_id: int(ch) for c, ch in zip(contacts, channels)},
                         int(channels.max()) + 1)
    mapping.validate(geometry)
    return geometry, mapping


def load_neurosuite(path: Path, geometry: ProbeGeometry, mapping: ChannelMap):
    # XML contains channel groups, not physical contact-to-channel associations.
    source = path.read_text(encoding="utf-8-sig")
    if "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
        raise ValueError("XML document types and entity declarations are unsupported.")
    root = ET.fromstring(source)
    if root.tag != "parameters":
        raise ValueError("Expected a NeuroSuite <parameters> document.")
    count = int(root.findtext("acquisitionSystem/nChannels", default="0"))
    groups, skipped = [], []
    for group in root.findall("anatomicalDescription/channelGroups/group"):
        channels = []
        for element in group.findall("channel"):
            channel = int(element.text)
            skip = element.get("skip", "0")
            if skip not in ("0", "1"):
                raise ValueError("XML channel skip must be 0 or 1.")
            channels.append(channel)
            if skip == "1":
                skipped.append(channel)
        groups.append(channels)
    if count <= 0 or not groups or not any(groups):
        raise ValueError("XML requires nChannels and anatomicalDescription/channelGroups.")
    result = ChannelMap(dict(mapping.contact_to_channel), count, groups, skipped, source)
    result.validate(geometry)
    return result
