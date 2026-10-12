import os

import cv2
import numpy as np
from ultralytics import YOLO

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Models
# Main model: civicfix_v3_best.pt (pothole, crack, alligator_crack, manhole)
# Second opinion for potholes: civic_best.pt (older pothole-only model)
# ---------------------------------------------------------------------------
WEIGHTS = os.path.join(BASE, "civicfix_v3_best.pt")
if not os.path.exists(WEIGHTS):
    WEIGHTS = os.path.join(BASE, "civic_best.pt")
if not os.path.exists(WEIGHTS):
    print("Custom weights not found, using default yolov8n.pt for testing")
    WEIGHTS = "yolov8n.pt"

model = YOLO(WEIGHTS)
CONF_MIN = 0.35

OLD_WEIGHTS = os.path.join(BASE, "civic_best.pt")
old_model = None
if os.path.exists(OLD_WEIGHTS) and WEIGHTS != OLD_WEIGHTS:
    old_model = YOLO(OLD_WEIGHTS)

# Minimum confidence per class (a weak manhole guess is ignored)
MIN_CONF = {"pothole": 0.30, "crack": 0.30, "alligator_crack": 0.30, "manhole": 0.60}
POTHOLE_MIN = 0.30


def _load(img):
    """Accept a file path or a numpy image."""
    if isinstance(img, str):
        loaded = cv2.imread(img)
        if loaded is None:
            raise ValueError(f"Could not read image: {img}")
        return loaded
    return img


def _iou(a, b):
    """Overlap between two boxes [x1, y1, x2, y2]."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def detect(img):
    dets = []
    r = model(img, conf=0.25, verbose=False)[0]
    for b in r.boxes:
        name = model.names[int(b.cls[0])]
        conf = float(b.conf[0])
        if conf < MIN_CONF.get(name, CONF_MIN):
            continue
        dets.append({"category": name, "confidence": round(conf, 3),
                     "box": [float(v) for v in b.xyxy[0]]})

    # second opinion from the older pothole-only model
    if old_model is not None:
        ro = old_model(img, conf=POTHOLE_MIN, verbose=False)[0]
        for b in ro.boxes:
            box = [float(v) for v in b.xyxy[0]]
            # a pothole found here replaces an overlapping manhole guess
            dets = [d for d in dets
                    if not (d["category"] == "manhole" and _iou(d["box"], box) > 0.3)]
            if not any(d["category"] == "pothole" and _iou(d["box"], box) > 0.5
                       for d in dets):
                dets.append({"category": "pothole",
                             "confidence": round(float(b.conf[0]), 3),
                             "box": box})
    return dets


def severity(det, frame_shape, n_dets):
    """Score 0..1 from box size, number of detections and confidence."""
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = det["box"]
    area_ratio = ((x2 - x1) * (y2 - y1)) / (h * w)
    score = (0.6 * min(area_ratio / 0.25, 1.0)
             + 0.25 * min(n_dets / 5, 1.0)
             + 0.15 * det["confidence"])
    label = "Low" if score < 0.33 else "Medium" if score < 0.66 else "High"
    return round(score, 2), label


def analyze_image(img):
    img = _load(img)
    dets = detect(img)
    if not dets:
        return {"found": False, "detections": []}
    for d in dets:
        d["severity"], d["severity_label"] = severity(d, img.shape, len(dets))
    best = max(dets, key=lambda d: d["severity"] * d["confidence"])
    return {"found": True, "primary": best, "detections": dets}


def analyze_video(path, n_frames=8):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        raise ValueError(f"Could not read video: {path}")
    best, best_score, best_idx = None, -1, None
    for idx in np.linspace(0, total - 1, n_frames, dtype=int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue
        res = analyze_image(frame)
        if res["found"]:
            p = res["primary"]
            score = p["confidence"] * p["severity"]
            if score > best_score:
                best, best_score, best_idx = res, score, int(idx)
    cap.release()
    if best is None:
        return {"found": False, "detections": []}
    best["frame_index"] = best_idx
    return best


def verify_fix(before_img, after_img):
    """Compare a before photo and an after photo of the same spot."""
    before = analyze_image(before_img)
    after = analyze_image(after_img)

    if not before["found"]:
        return {"verdict": "invalid_before", "confidence": 0.0}

    cat = before["primary"]["category"]
    same_after = [d for d in after["detections"] if d["category"] == cat]

    if not same_after:
        return {"verdict": "resolved", "confidence": 0.8}

    drop = before["primary"]["severity"] - max(d["severity"] for d in same_after)
    if drop > 0.3:
        return {"verdict": "partially_resolved", "confidence": 0.6}
    return {"verdict": "not_resolved", "confidence": 0.7}