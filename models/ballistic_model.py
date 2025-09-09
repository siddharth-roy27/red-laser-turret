"""
Optional ML stub. If you later train a model for estimating distance/offset from features,
load it here. For now, we keep a no-op that returns zero offsets.
"""
class BallisticModel:
    def __init__(self, model_path=None):
        self.ok = False

    def predict_offset(self, features_dict):
        # Return (dx_px, dy_px) offsets in image space
        return (0.0, 0.0)
