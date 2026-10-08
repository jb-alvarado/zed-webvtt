#!/usr/bin/env python3
"""Build an isolated dev extension without changing the public manifest."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GRAMMAR = ROOT / "tree-sitter-webvtt"
LOCAL = ROOT / ".local"
SNAPSHOT = LOCAL / "grammar"
DEV_EXTENSION = LOCAL / "dev-extension"


def run(*args: str, cwd: Path | None = None) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def generate_parser() -> None:
    # Always regenerate so changes to grammar.js take effect.
    executable = "tree-sitter.cmd" if os.name == "nt" else "tree-sitter"
    installed = GRAMMAR / "node_modules" / ".bin" / executable
    cli = str(installed) if installed.exists() else shutil.which("tree-sitter")
    if cli:
        run(cli, "generate", cwd=GRAMMAR)
    elif npx := shutil.which("npx"):
        run(npx, "--yes", "tree-sitter-cli@0.27.0", "generate", cwd=GRAMMAR)
    else:
        raise SystemExit("Install tree-sitter-cli or Node.js, then run this script again.")


def snapshot_grammar() -> str:
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    # This directory is owned by this script. Keep Git history, replace inputs.
    for child in SNAPSHOT.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(
        GRAMMAR, SNAPSHOT, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git", "node_modules", ".DS_Store"),
    )
    if not (SNAPSHOT / ".git").exists():
        run("git", "init", cwd=SNAPSHOT)
    run("git", "add", ".", cwd=SNAPSHOT)
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=SNAPSHOT, text=True,
    )
    if status:
        run(
            "git", "-c", "user.name=WebVTT local setup",
            "-c", "user.email=local@example.invalid", "commit",
            "-m", "Update local grammar snapshot", cwd=SNAPSHOT,
        )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=SNAPSHOT, text=True,
    ).strip()


def write_dev_extension(rev: str) -> None:
    DEV_EXTENSION.mkdir(parents=True, exist_ok=True)
    languages = DEV_EXTENSION / "languages"
    if languages.exists():
        shutil.rmtree(languages)
    shutil.copytree(ROOT / "languages", languages)
    shutil.copyfile(ROOT / "LICENSE", DEV_EXTENSION / "LICENSE")
    # Preserve public metadata, replace the grammar reference only in the copy.
    manifest = (ROOT / "extension.toml").read_text(encoding="utf-8")
    metadata, _ = manifest.split("[grammars.webvtt]", 1)
    manifest = (
        metadata + "[grammars.webvtt]\n"
        + f"repository = {json.dumps(SNAPSHOT.as_uri())}\n"
        + f"rev = {json.dumps(rev)}\n"
    )
    (DEV_EXTENSION / "extension.toml").write_text(manifest, encoding="utf-8")


def main() -> None:
    if not shutil.which("git"):
        raise SystemExit("Git is required to prepare the local grammar snapshot.")
    generate_parser()
    write_dev_extension(snapshot_grammar())
    print(f"\nReady. In Zed: Extensions -> Install Dev Extension -> {DEV_EXTENSION}")
    print("After edits, rerun this script and use Rebuild on the dev extension.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Command failed with exit code {exc.returncode}.") from exc
