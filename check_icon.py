import os
from pathlib import Path

# Check icon paths
cwd = Path.cwd()
print(f"CWD: {cwd}")
for f in cwd.glob("RIShadowing*"):
    print(f"  Found: {f} ({f.stat().st_size} bytes)")
for f in cwd.glob("*.png"):
    print(f"  PNG: {f}")
