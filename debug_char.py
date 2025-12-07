
with open("/Users/atakhadivi/Documents/GitHub/QircuitLearn/seed.py", "rb") as f:
    lines = f.readlines()
    print(len(lines))
    if len(lines) > 198:
        print(repr(lines[198].decode('utf-8'))) # Line 199 (0-indexed 198)
