import cv2, time, yaml
from src.vision import Vision
from src.turret_controller import TurretController
from src.trajectory import VisualBallistics

def main():
    with open("configs/config.yaml") as f:
        cfg = yaml.safe_load(f)

    vision = Vision(cfg)
    turret = TurretController(cfg)
    vb = VisualBallistics(cfg)

    mode_ballistic = False
    debounced = False

    res = cfg["camera"]["resolution"]
    cx, cy = res[0]//2, res[1]//2
    tol = cfg["control"]["center_tolerance_px"]
    Kpx = cfg["control"]["kp_deg_per_px_x"]
    Kpy = cfg["control"]["kp_deg_per_px_y"]
    show = not cfg["camera"].get("headless", False)

    print("Started. Button toggles Simple <-> Ballistic (visual) mode.")
    try:
        while True:
            frame = vision.get_frame()
            if frame is None:
                continue

            target_xy = None
            est_dist_cm = None

            if cfg["detection"]["mode"] == "aruco":
                info = vision.detect_aruco_distance_cm(frame)
                if info:
                    tx, ty, est_dist_cm = info
                    target_xy = (tx, ty)
                    cv2.circle(frame, (tx, ty), 5, (0,255,0), -1)
                    cv2.putText(frame, f"{est_dist_cm:.0f} cm", (tx+8, ty-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
            else:
                dot, mask = vision.detect_red_dot(frame)
                if dot:
                    tx, ty, r = dot
                    target_xy = (tx, ty)
                    cv2.circle(frame, (tx, ty), r, (0,255,0), 2)

            # button toggle (simple debounce)
            pressed = turret.button_pressed()
            if pressed and not debounced:
                mode_ballistic = not mode_ballistic
                debounced = True
                print("Mode:", "BALLISTIC (visual)" if mode_ballistic else "SIMPLE")
            if not pressed and debounced:
                debounced = False

            if target_xy:
                tx, ty = target_xy
                off_y = 0
                if mode_ballistic and cfg["ballistic_demo"]["enabled"]:
                    off_y = vb.offset_px(est_dist_cm)
                    ty = int(ty - off_y)  # compensate upwards in image space
                    cv2.line(frame, (tx, ty), (tx, ty+off_y), (255, 200, 0), 2)

                err_x = tx - cx
                err_y = ty - cy

                if abs(err_x) > tol or abs(err_y) > tol:
                    d_ang_x = -Kpx * err_x
                    d_ang_y =  Kpy * err_y
                    turret.nudge(d_ang_x, d_ang_y)

                # draw HUD
                cv2.circle(frame, (cx, cy), tol, (255,255,255), 1)
                cv2.putText(frame, f"Mode: {'BALLISTIC VISUAL' if mode_ballistic else 'SIMPLE'}",
                            (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

            if show:
                cv2.imshow("red-laser-turret", frame)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    break

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        vision.close()
        turret.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
