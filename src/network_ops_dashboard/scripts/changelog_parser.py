import re
from pathlib import Path
from django.conf import settings

def parse_changelog():
    changelog_path=Path(settings.VENV_DIR) / "CHANGELOG.md"

    content = changelog_path.read_text(encoding="utf-8")
    blocks = re.split(r'^(?=##\s)', content, flags=re.M)
    entries = []

    for b in blocks:
        if not b.startswith("## "):
            continue
        lines = b.strip().splitlines()
        header = lines[0].lstrip("# ").strip()
        changes = [ln.strip("- ").strip() for ln in lines[1:] if ln.strip()]
        entries.append({"version": header, "changes": changes})
    return entries