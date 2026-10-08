#!/usr/bin/env python3
"""Validate a version tag and print the matching changelog section."""
import re
import sys
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
version = tomllib.loads((root / "extension.toml").read_text())["version"]
if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag) or tag != f"v{version}":
    raise SystemExit("The tag must match the extension version, e.g. v0.1.0.")
changelog = (root / "CHANGELOG.md").read_text()
match = re.search(r"^## \[" + re.escape(version) + r"\][^\n]*\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
if not match or not match.group(1).strip():
    raise SystemExit("Add release notes for this version to CHANGELOG.md first.")
print(match.group(1).strip())
