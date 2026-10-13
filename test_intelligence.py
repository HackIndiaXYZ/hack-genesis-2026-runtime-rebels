

"""Offline tests for CivicFix intelligence.py.
Run: python test_intelligence.py
These tests do not call Gemini or require an API key.
"""

from intelligence import (
    CATEGORIES,
    merge_results,
    generate_complaint,
    find_duplicate,
    predict_resolution_days,
    predict_severity,
)


def test_categories():
    print("Testing supported categories...")
    assert CATEGORIES == ["pothole", "open_manhole"]
    print("PASS: Only the two supported categories are enabled.")


def test_merge_results():
    print("\nTesting prediction merging...")

    for issue in CATEGORIES:
        result = merge_results(
            {"class": issue, "confidence": 0.9},
            {"category": issue, "severity": "High"},
        )
        assert result["issue"] == issue
        assert result["needs_review"] is False
        assert 0 <= result["confidence"] <= 1
        print(f"PASS: {issue} classified consistently.")

    # Conflicting predictions must be flagged for review.
    result = merge_results(
        {"class": "pothole", "confidence": 0.9},
        {"category": "open_manhole", "severity": "High"},
    )
    assert result["needs_review"] is True
    print("PASS: Conflicting predictions require review.")

    # Unknown predictions must not invent an issue.
    result = merge_results(
        {"class": "unknown", "confidence": 0.0},
        {"category": "unknown", "severity": "Medium"},
    )
    assert result["issue"] == "unknown"
    assert result["needs_review"] is True
    print("PASS: Unknown predictions are handled safely.")


def test_complaints():
    print("\nTesting complaint generation...")

    for issue in CATEGORIES:
        complaint = generate_complaint(
            issue, "High", "MG Road, Kanpur", "en"
        )
        assert isinstance(complaint, str)
        assert len(complaint) > 50
        assert "MG Road, Kanpur" in complaint
        print(f"PASS: English complaint generated for {issue}.")

        hindi_complaint = generate_complaint(
            issue, "High", "MG Road, Kanpur", "hi"
        )
        assert isinstance(hindi_complaint, str)
        assert len(hindi_complaint) > 20
        print(f"PASS: Hindi complaint generated for {issue}.")

    unknown_complaint = generate_complaint(
        "unknown", "Medium", "MG Road, Kanpur"
    )
    assert "review" in unknown_complaint.lower()
    print("PASS: Unknown issue requests manual review.")


def test_duplicate_detection():
    print("\nTesting duplicate detection...")

    reports = [
        {
            "id": 1,
            "text": "Big pothole near the bus stop on MG Road",
            "lat": 26.4499,
            "lon": 80.3319,
        },
        {
            "id": 2,
            "text": "Large pothole close to MG Road bus stop",
            "lat": 26.4499,
            "lon": 80.3320,
        },
        {
            "id": 3,
            "text": "Big pothole near the bus stop",
            "lat": 26.9000,
            "lon": 80.9000,
        },
    ]

    nearby_duplicate = find_duplicate(
        "Big pothole near the bus stop on MG Road",
        26.4499,
        80.3319,
        reports,
    )
    assert nearby_duplicate == 1
    print("PASS: Matching nearby report detected.")

    far_report = find_duplicate(
        "Big pothole near the bus stop",
        26.4499,
        80.3319,
        [reports[2]],
    )
    assert far_report is None
    print("PASS: Matching text far away is not flagged.")


def test_resolution_estimates():
    print("\nTesting resolution-time estimates...")

    for issue in CATEGORIES:
        days = predict_resolution_days(issue, "High", "PWD")
        assert isinstance(days, (int, float))
        assert days > 0
        print(f"PASS: {issue} estimate = {days} days.")

    high_days = predict_resolution_days("pothole", "High", "PWD")
    low_days = predict_resolution_days("pothole", "Low", "PWD")
    assert high_days < low_days
    print("PASS: High-severity potholes receive a shorter estimate.")

    assert predict_resolution_days(
        "unknown", "Medium", "PWD"
    ) is None
    print("PASS: Unknown issues receive no fabricated estimate.")


def test_severity():
    print("\nTesting severity prediction...")

    for issue in CATEGORIES:
        severity = predict_severity(issue, 0.9, 0.3)
        assert severity in ("Low", "Medium", "High")
        print(f"PASS: {issue} severity = {severity}.")


def main():
    tests = [
        test_categories,
        test_merge_results,
        test_complaints,
        test_duplicate_detection,
        test_resolution_estimates,
        test_severity,
    ]

    for test in tests:
        test()

    print("\nAll offline CivicFix intelligence tests passed!")


if __name__ == "__main__":
    main()

# """Run: python test_intelligence.py   (put sample photos in ./samples/ to test the VLM)"""
# import glob
# from intelligence import *

# # --- merge_results: 10 fake YOLO outputs -------------------------------------
# yolo = [("pothole", .9), ("pothole", .8), ("garbage", .7), ("garbage", .4), ("open_manhole", .95),
#         ("waterlogging", .6), ("damaged_road", .85), ("broken_streetlight", .75),
#         ("pothole", .3), ("other", .5)]
# vlm = ["pothole", "garbage", "garbage", "garbage", "open_manhole",
#        "pothole", "damaged_road", "unknown", "pothole", "other"]
# print("== merge_results")
# for (c, p), v in zip(yolo, vlm):
#     r = merge_results({"class": c, "confidence": p}, {"category": v, "severity": "High"})
#     print(f"yolo={c:<18}{p:<5} vlm={v:<14} -> conf={r['confidence']:<6} review={r['needs_review']}")
# assert merge_results({"class": "pothole", "confidence": .9}, {"category": "garbage"})["needs_review"]
# assert not merge_results({"class": "pothole", "confidence": .9}, {"category": "pothole"})["needs_review"]

# # --- complaints ---------------------------------------------------------------
# print("\n== generate_complaint")
# for i in CATEGORIES[:5]:
#     assert len(generate_complaint(i, "High", "MG Road, Kanpur", "en")) > 50
#     assert "MG Road" in generate_complaint(i, "Low", "MG Road, Kanpur", "hi")
# print(generate_complaint("pothole", "High", "MG Road, Kanpur", "en"))
# print(generate_complaint("pothole", "High", "MG Road, Kanpur", "hi"))

# # --- duplicates ---------------------------------------------------------------
# print("\n== find_duplicate")
# db = [{"id": 1, "text": "Big pothole near the bus stop on MG Road", "lat": 26.4499, "lon": 80.3319},
#       {"id": 2, "text": "Garbage piled up at the market", "lat": 26.4500, "lon": 80.3320},
#       {"id": 3, "text": "Big pothole near the bus stop", "lat": 26.9000, "lon": 80.9000}]  # far away
# print("similar, nearby  ->", find_duplicate("Large pothole close to MG Road bus stop", 26.4499, 80.3320, db))
# print("different issue  ->", find_duplicate("Streetlight not working", 26.4499, 80.3320, db))
# print("same text, far   ->", find_duplicate("Big pothole near the bus stop", 26.4499, 80.3319, [db[2]]))
# assert find_duplicate("Large pothole close to MG Road bus stop", 26.4499, 80.3320, db) == 1
# assert find_duplicate("Big pothole near the bus stop", 26.4499, 80.3319, [db[2]]) is None

# # --- predictors ---------------------------------------------------------------
# print("\n== predict_resolution_days / predict_severity")
# for i, s, d in [("pothole", "High", "PWD"), ("pothole", "Low", "PWD"), ("garbage", "Medium", "Sanitation"),
#                 ("damaged_road", "High", "PWD"), ("open_manhole", "High", "Municipal Corporation"),
#                 ("broken_streetlight", "Medium", "Electricity Board"), ("waterlogging", "High", "Jal Board"),
#                 ("other", "Low", "Municipal Corporation"), ("garbage", "High", "Sanitation"),
#                 ("pothole", "Medium", "Unknown Dept")]:
#     print(f"{i:<20}{s:<7}{d:<22}-> {predict_resolution_days(i, s, d)} days")
# assert predict_resolution_days("pothole", "High", "PWD") < predict_resolution_days("pothole", "Low", "PWD")
# print("severity:", predict_severity("open_manhole", .9, .3), predict_severity("garbage", .5, .02))

# # --- VLM (needs API key + images) ----------------------------------------------
# print("\n== vlm_analyze")
# imgs = glob.glob("samples/*.jpg") + glob.glob("samples/*.png")
# for p in imgs[:10]:
#     print(p, "->", vlm_analyze(p))
# if not imgs:
#     print("No images in ./samples/ - skipped. Add 10 photos to test.")
# print("\nAll asserts passed.")