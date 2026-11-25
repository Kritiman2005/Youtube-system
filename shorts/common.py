import json, subprocess, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
for d in ("sources", "raw", "clips", "out"):
    (DATA / d).mkdir(parents=True, exist_ok=True)

def cfg():
    return yaml.safe_load((ROOT / "config.yaml").read_text())

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw).stdout

def load(p, default=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default

def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2))
