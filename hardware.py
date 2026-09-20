# BlindSpot v2 - hardware (camera + 4-zone haptics)

import time
import threading
import numpy as np
import cv2
from picamera2 import Picamera2
from gpiozero import OutputDevice

MOTORS = {
    "LT": (OutputDevice(26), OutputDevice(19)),
    "LB": (OutputDevice(13), OutputDevice(6)),
    "RT": (OutputDevice(22), OutputDevice(17)),
    "RB": (OutputDevice(24), OutputDevice(23)),
}
WIDTH, HEIGHT = 320, 240
SENSITIVITY, SMOOTHING, DEADZONE = 5.0, 0.5, 6
FAR_CUTOFF, CLOSE_CUTOFF, CYCLE, ZONE_HZ = 12, 55, 0.30, 30

cam = None
latest_frame = None
frame_lock = threading.Lock()


def motor_on(p):
    p[1].off()
    p[0].on()


def motor_off(p):
    p[0].off()
    p[1].off()


def all_off():
    for p in MOTORS.values():
        motor_off(p)


def to_gray(f):
    return cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (5, 5), 0)


def quad_scores(prev, curr):
    d = cv2.absdiff(prev, curr)
    h, w = d.shape
    mx, my = w // 2, h // 2
    s = lambda r: min(100.0, float(np.mean(r)) * SENSITIVITY)
    return {
        "LT": s(d[:my, :mx]),
        "RT": s(d[:my, mx:]),
        "LB": s(d[my:, :mx]),
        "RB": s(d[my:, mx:]),
    }


def duty_for(v):
    if v < FAR_CUTOFF:
        return 0.0
    if v < CLOSE_CUTOFF:
        return 0.15 + (v - FAR_CUTOFF) / (CLOSE_CUTOFF - FAR_CUTOFF) * 0.45
    return 0.60 + (min(v, 100) - CLOSE_CUTOFF) / (100 - CLOSE_CUTOFF) * 0.40


def zone_loop():
    global latest_frame
    prev = to_gray(cam.capture_array())
    sm = {k: 0.0 for k in MOTORS}
    interval = 1.0 / ZONE_HZ
    while True:
        arr = cam.capture_array()
        with frame_lock:
            latest_frame = arr.copy()
        curr = to_gray(arr)
        raw = quad_scores(prev, curr)
        prev = curr
        phase = (time.time() % CYCLE) / CYCLE
        for k in MOTORS:
            sm[k] = SMOOTHING * sm[k] + (1 - SMOOTHING) * raw[k]
            v = 0 if sm[k] < DEADZONE else min(100, int(sm[k]))
            d = duty_for(v)
            if d > 0 and phase < d:
                motor_on(MOTORS[k])
            else:
                motor_off(MOTORS[k])
        time.sleep(interval)


def get_frame():
    with frame_lock:
        if latest_frame is None:
            return None
        return latest_frame.copy()


def start_camera():
    global cam
    all_off()
    cam = Picamera2()
    cfg = cam.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "RGB888"})
    cam.configure(cfg)
    cam.start()
    time.sleep(1.0)
    threading.Thread(target=zone_loop, daemon=True).start()


def stop_camera():
    all_off()
    if cam:
        cam.stop()
