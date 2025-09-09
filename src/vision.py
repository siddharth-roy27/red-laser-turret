import cv2
import numpy as np

# Optional Picamera2 import
try:
    from picamera2 import Picamera2
    _PICAM_OK = True
except Exception:
    _PICAM_OK = False

_aruco_dicts = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
}

class Vision:
    def __init__(self, cfg):
        self.cfg = cfg
        res = tuple(cfg["camera"]["resolution"])
        if cfg["camera"].get("use_picamera2", True) and _PICAM_OK:
            self.cam = Picamera2()
            self.cam.configure(self.cam.create_video_configuration(
                main={"size": res, "format": "RGB888"},
                controls={"FrameRate": cfg["camera"]["framerate"]}
            ))
            self.cam.start()
            self.backend = "picamera2"
        else:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])
            self.cap.set(cv2.CAP_PROP_FPS, cfg["camera"]["framerate"])
            self.backend = "opencv"

        # ArUco setup
        dname = self.cfg["detection"]["aruco_dict"]
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(_aruco_dicts[dname])
        self.aruco_params = cv2.aruco.DetectorParameters()

    def get_frame(self):
        if self.backend == "picamera2":
            frame = self.cam.capture_array()  # RGB
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            ok, frame = self.cap.read()
            return frame if ok else None

    def detect_red_dot(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        d = self.cfg["detection"]
        m1 = cv2.inRange(hsv, np.array(d["red_hsv_lower1"]), np.array(d["red_hsv_upper1"]))
        m2 = cv2.inRange(hsv, np.array(d["red_hsv_lower2"]), np.array(d["red_hsv_upper2"]))
        mask = cv2.medianBlur(cv2.bitwise_or(m1, m2), 3)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts: return None, mask
        c = max(cnts, key=cv2.contourArea)
        (x, y), r = cv2.minEnclosingCircle(c)
        if r < self.cfg["detection"]["min_radius_px"]:
            return None, mask
        return (int(x), int(y), int(r)), mask

    def detect_aruco_distance_cm(self, frame):
        # Returns (cx, cy, est_distance_cm) or None
        corners, ids, _ = cv2.aruco.detectMarkers(frame, self.aruco_dict, parameters=self.aruco_params)
        if ids is None: return None
        # take largest marker
        areas = [(i, cv2.contourArea(c.reshape(-1,2))) for i, c in enumerate(corners)]
        if not areas: return None
        idx = max(areas, key=lambda t: t[1])[0]
        c = corners[idx].reshape(-1,2)
        cx, cy = c.mean(axis=0)
        # estimate “apparent size” = perimeter/4 ~ side length in px
        side_px = np.linalg.norm(c[0]-c[1])
        W = self.cfg["detection"]["aruco_marker_size_cm"]
        # simple pinhole: distance ~ (focal_px * W) / side_px ; use a rough focal guess (~ 700 px at 640x)
        focal_px = 700.0
        if side_px <= 1: return None
        dist_cm = (focal_px * W) / side_px
        return (int(cx), int(cy), float(dist_cm))

    def close(self):
        try:
            if self.backend == "picamera2":
                self.cam.stop()
            else:
                self.cap.release()
        except Exception:
            pass
