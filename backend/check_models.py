import sys, collections
from pathlib import Path
import cv2

root = Path(sys.argv[1])
split = sys.argv[2] if len(sys.argv) > 2 else "train"
names = {0: "pothole", 1: "crack", 2: "alligator_crack", 3: "manhole"}
out = Path("label_check"); out.mkdir(exist_ok=True)

counts = collections.Counter()
by_prefix = collections.defaultdict(collections.Counter)
samples = collections.defaultdict(list)

for lbl in sorted((root / split / "labels").glob("*.txt")):
    for line in lbl.read_text().splitlines():
        p = line.split()
        if len(p) != 5:
            continue
        c = int(p[0])
        counts[c] += 1
        by_prefix[lbl.stem.split("_")[0]][c] += 1
        if len(samples[c]) < 6:
            samples[c].append((lbl.stem, [float(x) for x in p[1:]]))

print("instances per class:", {names.get(c, c): n for c, n in sorted(counts.items())})
print("per filename prefix:")
for pre, cnt in sorted(by_prefix.items(), key=lambda x: -sum(x[1].values()))[:10]:
    print(" ", pre, {names.get(c, c): n for c, n in sorted(cnt.items())})

for c, items in samples.items():
    for i, (stem, (xc, yc, w, h)) in enumerate(items):
        img_path = next((root / split / "images").glob(stem + ".*"), None)
        img = cv2.imread(str(img_path)) if img_path else None
        if img is None:
            continue
        H, W = img.shape[:2]
        x1, y1 = int((xc - w / 2) * W), int((yc - h / 2) * H)
        x2, y2 = int((xc + w / 2) * W), int((yc + h / 2) * H)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 4)
        cv2.putText(img, names.get(c, str(c)), (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.imwrite(str(out / f"class{c}_{i}.jpg"), img)
print("saved samples to", out.resolve())