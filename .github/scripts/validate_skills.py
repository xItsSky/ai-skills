#!/usr/bin/env python3
"""Validate plugin and marketplace JSON manifests and every SKILL.md frontmatter.

Run from the repo root:
    python .github/scripts/validate_skills.py

Exits non-zero on the first class of failure it finds. This catches a broken
YAML frontmatter (for example a colon inside an unquoted description), which
loads the skill with empty metadata at runtime.
"""
import glob
import json
import sys

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

errors = []

for path in glob.glob("**/.claude-plugin/*.json", recursive=True):
    try:
        with open(path, encoding="utf-8") as handle:
            json.load(handle)
    except (OSError, ValueError) as exc:
        errors.append(f"{path}: invalid JSON: {exc}")

skill_files = glob.glob("**/SKILL.md", recursive=True)
if not skill_files:
    errors.append("no SKILL.md found")

for path in skill_files:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if not text.startswith("---"):
        errors.append(f"{path}: missing YAML frontmatter")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{path}: unterminated frontmatter")
        continue
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        errors.append(f"{path}: frontmatter YAML parse error: {exc}")
        continue
    if not isinstance(meta, dict):
        errors.append(f"{path}: frontmatter is not a mapping")
        continue
    for field in ("name", "description"):
        if not meta.get(field):
            errors.append(f"{path}: missing '{field}' in frontmatter")

if errors:
    print("Validation failed:")
    for item in errors:
        print(f"  - {item}")
    sys.exit(1)

print(f"Validation passed: {len(skill_files)} skill(s), manifests OK")
