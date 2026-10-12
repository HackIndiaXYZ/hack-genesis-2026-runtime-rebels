import sys
import json
from vision import analyze_image, analyze_video, verify_fix

cmd = sys.argv[1]

if cmd == "image":
    print(json.dumps(analyze_image(sys.argv[2]), indent=2))
elif cmd == "video":
    print(json.dumps(analyze_video(sys.argv[2]), indent=2))
elif cmd == "verify":
    print(json.dumps(verify_fix(sys.argv[2], sys.argv[3]), indent=2))