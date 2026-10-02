from dataclasses import dataclass, field

from probe_planner.implant.pose import ImplantPose
from probe_planner.implant.drive import DriveMount
from probe_planner.probes.model import ProbeGeometry, ChannelMap
from probe_planner.probes.mounting import with_package_base


@dataclass
class ProbeInstance:
    id: str
    geometry: ProbeGeometry
    channel_map: ChannelMap
    pose: ImplantPose = field(default_factory=ImplantPose)
    selected_shank_id: int | None = None
    drive: DriveMount | None = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Each probe instance requires a nonempty ID.")
        self.channel_map.validate(self.geometry)
        self.geometry = with_package_base(self.geometry, self.channel_map)
        shanks = sorted({c.shank_id for c in self.geometry.contacts})
        if self.selected_shank_id is None:
            self.selected_shank_id = 0 if 0 in shanks else shanks[0]
        if self.selected_shank_id not in shanks:
            raise ValueError("Selected shank does not exist in the probe.")
