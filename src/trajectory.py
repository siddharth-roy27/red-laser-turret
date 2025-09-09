import numpy as np

class VisualBallistics:
    """
    SAFE demo: returns an image-space Y offset to visualize an arc correction.
    Not for aiming any projectile or weapon.
    """
    def __init__(self, cfg):
        b = cfg["ballistic_demo"]
        self.gain = float(b["gravity_demo_gain"])
        self.max_off = int(b["max_offset_px"])

    def offset_px(self, est_distance_cm):
        if est_distance_cm is None:
            return 0
        off = self.gain * (est_distance_cm ** 2)
        off = max(-self.max_off, min(self.max_off, off))
        return int(off)
