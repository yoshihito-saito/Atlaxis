from dataclasses import dataclass, asdict, field
import csv
import json
from pathlib import Path

from probe_planner.atlas.coordinates import AtlasCoordinates
from probe_planner.implant.pose import ImplantPose
from probe_planner.implant.instance import ProbeInstance
from probe_planner.implant.skull import Skull
from probe_planner.implant.drive import DriveMount
from probe_planner.probes.importers import geometry_from_dict
from probe_planner.probes.model import ChannelMap, ProbeGeometry


@dataclass
class Plan:
    atlas_name: str
    atlas_version: str
    coordinates: AtlasCoordinates
    geometry: ProbeGeometry
    channel_map: ChannelMap
    pose: ImplantPose
    additional_probes: list[ProbeInstance] = field(default_factory=list)
    probe_id: str = "probe_1"
    selected_shank_id: int | None = None
    selected_probe_id: str = "probe_1"
    skull: Skull | None = None
    # Legacy plans had no skull field. An explicit null in newer plans means removed.
    use_default_skull: bool = False
    drive: DriveMount | None = None

    @property
    def probes(self):
        return [ProbeInstance(self.probe_id, self.geometry, self.channel_map, self.pose,
                              self.selected_shank_id, self.drive), *self.additional_probes]

    @classmethod
    def from_instances(cls, atlas, coordinates, probes, selected_probe_id, *, skull=None):
        first, *remaining = probes
        return cls(atlas.name, atlas.version, coordinates, first.geometry,
                   first.channel_map, first.pose, remaining, first.id,
                   first.selected_shank_id, selected_probe_id, skull, False, first.drive)


def save_plan(path: Path, plan: Plan):
    probes = plan.probes
    ids = [probe.id for probe in probes]
    if len(ids) != len(set(ids)) or plan.selected_probe_id not in ids:
        raise ValueError("Probe IDs must be unique and include the selected probe.")
    for probe in probes:
        probe.channel_map.validate(probe.geometry)
    payload = {
        "version": 5,
        "atlas": {"name": plan.atlas_name, "version": plan.atlas_version},
        "coordinates": asdict(plan.coordinates),
        "selected_probe_id": plan.selected_probe_id,
        "skull": plan.skull.to_dict() if plan.skull is not None else None,
        "probes": [{"id": probe.id, "geometry": asdict(probe.geometry),
                    "channel_map": asdict(probe.channel_map), "pose": asdict(probe.pose),
                    "selected_shank_id": probe.selected_shank_id,
                    "drive": asdict(probe.drive) if probe.drive else None} for probe in probes],
    }
    # Replace only after the complete JSON has been serialized and written.
    import os
    import tempfile
    descriptor, temporary = tempfile.mkstemp(prefix=".implant-", suffix=".json", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_plan(path: Path) -> Plan:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["version"] not in (1, 2, 3, 4, 5) or not data["probes"]:
        raise ValueError("Expected a version 1–5 project containing at least one probe.")
    probes = [ProbeInstance(probe["id"], geometry_from_dict(probe["geometry"]),
                            ChannelMap(**probe["channel_map"]), ImplantPose(**probe["pose"]),
                            probe.get("selected_shank_id"),
                            DriveMount(**probe["drive"]) if probe.get("drive") else None) for probe in data["probes"]]
    ids = [probe.id for probe in probes]
    selected = data.get("selected_probe_id", probes[0].id)
    if len(ids) != len(set(ids)) or selected not in ids:
        raise ValueError("Project contains invalid or duplicate probe IDs.")
    first, *remaining = probes
    return Plan(data["atlas"]["name"], data["atlas"]["version"],
                AtlasCoordinates(**data["coordinates"]), first.geometry, first.channel_map,
                first.pose, remaining, first.id, first.selected_shank_id, selected,
                Skull.from_dict(data["skull"]) if data.get("skull") is not None else None,
                "skull" not in data, first.drive)


def export_contacts(path: Path, rows):
    if not rows:
        raise ValueError("Load and calibrate an atlas and probe before exporting contacts.")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
