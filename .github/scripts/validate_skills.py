#!/usr/bin/env python3
"""Validate this repository's shared skills and Claude/Codex catalogs."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import yaml


class ValidationError(ValueError):
    """A catalog, manifest, or skill cannot be loaded consistently."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"{path}: cannot read file: {exc}") from exc
    except ValueError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc
    require(isinstance(data, dict), f"{path}: expected a JSON object")
    return data


def require_text(data: dict, field: str, location: object) -> str:
    value = data.get(field)
    require(isinstance(value, str) and bool(value.strip()),
            f"{location}: '{field}' must be a nonempty string")
    return value


def local_directory(root: Path, value: object) -> Path:
    require(isinstance(value, str) and value.startswith("./"),
            f"{value!r}: path must start with './' and stay inside {root}")
    target = (root / value).resolve()
    require(target != root and target.is_relative_to(root),
            f"{value!r}: path must stay inside {root}")
    require(target.is_dir(), f"{value!r}: source directory does not exist")
    return target


def catalog_plugins(catalog: dict, root: Path, codex: bool) -> dict[str, Path]:
    entries = catalog.get("plugins")
    require(isinstance(entries, list), "catalog plugins must be an array")
    plugins = {}
    for entry in entries:
        require(isinstance(entry, dict), "plugin entry must be an object")
        name = require_text(entry, "name", "catalog entry")
        require(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)),
                f"{name}: plugin name must use lowercase kebab-case")
        require(name not in plugins, f"{name}: duplicate plugin entry")
        source = entry.get("source")
        if codex:
            require(isinstance(source, dict) and source.get("source") == "local",
                    f"{name}: Codex source must be a local source object")
            source = source.get("path")
            policy = entry.get("policy")
            require(isinstance(policy, dict), f"{name}: policy must be an object")
            require(policy.get("installation") in
                    ("AVAILABLE", "NOT_AVAILABLE", "INSTALLED_BY_DEFAULT"),
                    f"{name}: invalid installation policy")
            require(policy.get("authentication") in ("ON_INSTALL", "ON_USE"),
                    f"{name}: invalid authentication policy")
            require_text(entry, "category", name)
        plugins[name] = local_directory(root, source)
        require(plugins[name].name == name, f"{name}: source directory name must match")
    return plugins


def validate_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    require(match is not None, f"{path}: missing or unterminated YAML frontmatter")
    try:
        metadata = yaml.safe_load(match[1])
        nodes = yaml.compose(match[1])
    except yaml.YAMLError as exc:
        raise ValidationError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    require(isinstance(metadata, dict), f"{path}: frontmatter must be a mapping")
    name = require_text(metadata, "name", path)
    require(name == path.parent.name, f"{path}: skill name must match directory name")
    require_text(metadata, "description", path)
    # Plain scalars silently discard inline comments, including quoted examples
    # embedded in an otherwise unquoted description. Require explicit quoting.
    for key, value in nodes.value:
        if key.value == "description" and value.style is None:
            line = match[1].splitlines()[value.end_mark.line]
            require(not line[value.end_mark.column:].lstrip().startswith("#"),
                    f"{path}: quote or fold description containing an inline '#' comment")


def validate_plugin(name: str, root: Path, catalog_entry: dict) -> list[Path]:
    claude = read_object(root / ".claude-plugin/plugin.json")
    codex = read_object(root / ".codex-plugin/plugin.json")
    for manifest in (claude, codex):
        require(manifest.get("name") == name, f"{root}: manifest name must match catalog")
        version = require_text(manifest, "version", root)
        require(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", version)),
                f"{root}: invalid semantic version")
        require_text(manifest, "description", root)
    require(claude["version"] == codex["version"] == catalog_entry.get("version"),
            f"{root}: version mismatch between catalogs and manifests")
    require(codex.get("skills") in ("./skills", "./skills/"),
            f"{root}: Codex skills must point to shared './skills/'")
    interface = codex.get("interface")
    require(isinstance(interface, dict), f"{root}: interface must be an object")
    require_text(interface, "displayName", root)
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    require(bool(skills), f"{root}: no skills found")
    for directory in (root / "skills").iterdir():
        if directory.is_dir():
            require((directory / "SKILL.md").is_file(), f"{directory}: missing SKILL.md")
    for skill in skills:
        require(skill.resolve().is_relative_to(root), f"{skill}: skill must stay inside plugin")
        validate_skill(skill)
    return skills


def validate_repository(root: Path) -> int:
    claude = read_object(root / ".claude-plugin/marketplace.json")
    codex = read_object(root / ".agents/plugins/marketplace.json")
    require(require_text(claude, "name", "Claude catalog") ==
            require_text(codex, "name", "Codex catalog"), "marketplace names must match")
    claude_plugins = catalog_plugins(claude, root, codex=False)
    codex_plugins = catalog_plugins(codex, root, codex=True)
    require(claude_plugins.keys() == codex_plugins.keys(), "catalog plugin sets must match")
    require(bool(claude_plugins), "catalogs must contain at least one plugin")
    require(claude_plugins == codex_plugins, "catalog source paths must match")
    discovered = {path.parent.parent.resolve() for platform in ("claude", "codex")
                  for path in root.glob(f"*/.{platform}-plugin/plugin.json")}
    require(discovered == set(claude_plugins.values()), "unlisted plugin manifests found")
    skills = []
    for entry in claude["plugins"]:
        skills.extend(validate_plugin(entry["name"], claude_plugins[entry["name"]], entry))
    discovered_skills = set(root.glob("*/skills/*/SKILL.md"))
    require(discovered_skills == set(skills), "unlisted skills found outside registered plugins")
    return len(skills)


def main() -> int:
    try:
        count = validate_repository(Path.cwd().resolve())
    except (ValidationError, OSError) as exc:
        print(f"Validation failed: {exc}")
        return 1
    print(f"Validation passed: {count} skill(s), Claude and Codex catalogs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
