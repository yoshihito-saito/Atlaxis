from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class ImplantPose:
    ap_mm: float = 0.0
    ml_mm: float = 0.0
    dv_mm: float = 0.0
    azimuth_deg: float = 0.0
    elevation_deg: float = 0.0
    roll_deg: float = 0.0
    depth_mm: float = 0.0

    def __post_init__(self):
        if not np.isfinite(list(asdict(self).values())).all() or self.depth_mm < 0:
            raise ValueError("Pose values must be finite; insertion depth must be nonnegative.")
