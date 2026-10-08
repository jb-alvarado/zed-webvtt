#!/usr/bin/env python3
"""Check parser behavior, highlight captures, and release/dev configuration."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "tree-sitter-webvtt"


def run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT)


def main() -> None:
    executable = "tree-sitter.cmd" if os.name == "nt" else "tree-sitter"
    installed = GRAMMAR / "node_modules" / ".bin" / executable
    cli = str(installed) if installed.exists() else shutil.which("tree-sitter")
    if not cli:
        raise SystemExit("Run npm ci in tree-sitter-webvtt first.")

    manifest_path = ROOT / "extension.toml"
    original = manifest_path.read_bytes()
    manifest = tomllib.loads(original.decode())
    grammar = manifest["grammars"]["webvtt"]
    assert manifest["authors"] == ["jb-alvarado"]
    assert manifest["repository"] == "https://github.com/jb-alvarado/zed-webvtt"
    assert grammar["repository"] == manifest["repository"] + ".git"
    assert grammar["path"] == "tree-sitter-webvtt"
    assert re.fullmatch(r"[0-9a-f]{40}", grammar["rev"])
    run("git", "merge-base", "--is-ancestor", grammar["rev"], "HEAD")
    # A stale grammar pin would make the published extension use an older parser.
    for p in [GRAMMAR / "grammar.js", *sorted((GRAMMAR / "src").rglob("*"))]:
        if p.is_file():
            committed = subprocess.check_output(
                ["git", "show", f"{grammar['rev']}:{p.relative_to(ROOT).as_posix()}"], cwd=ROOT,
            )
            assert committed == p.read_bytes(), f"Update grammar rev after committing {p.name}"

    print(run(cli, "test", cwd=GRAMMAR))
    run(cli, "parse", "--quiet", str(ROOT / "examples/demo.vtt"), cwd=GRAMMAR)
    sample = (
        "WEBVTT\n\nSTYLE\n::cue {\n  color: lime;\n}\n\n"
        "REGION\nid:top\nwidth:40%\nregionanchor:50.5%, 10%\nscroll:up\n\n"
        "00:00:01.000 --> 00:00:04.000 align:start position:10% line:-1 size:70%\n"
        "<v Alice>Hello <b>world</b></v>\n\n"
        "00:00:05.000 --> 00:00:06.000 line:auto position:10.5%\n<v Bob>Hi!</v>\n"
    )
    with tempfile.TemporaryDirectory(prefix="webvtt-check-") as directory:
        p = Path(directory) / "sample.vtt"
        p.write_text(sample, encoding="utf-8")
        for folder in (ROOT / "languages/webvtt", GRAMMAR / "queries"):
            output = run(cli, "query", str(folder / "highlights.scm"), str(p), cwd=GRAMMAR)
            for value, role in (
                ("start", "string"), ("auto", "string"), (" Alice", "string"),
                (" Bob", "string"), ("10%", "number"), ("-1", "number"),
                ("70%", "number"), ("10.5%", "number"), ("40%", "number"),
                ("50.5%, 10%", "number"), ("top", "string"), ("up", "string"),
                ("width", "property"),
            ):
                assert re.search(r" - " + role + r",.*text: `" + re.escape(value) + "`", output), (folder, value)
            output = run(cli, "query", str(folder / "injections.scm"), str(p), cwd=GRAMMAR)
            assert "capture: injection.content, start: (3, 0), end: (5, 1)" in output

    # Both first setup and reruns must preserve the publishable manifest.
    for _ in range(2):
        run(sys.executable, "prepare_local.py")
        assert manifest_path.read_bytes() == original
    dev = tomllib.loads((ROOT / ".local/dev-extension/extension.toml").read_text(encoding="utf-8"))
    assert dev["grammars"]["webvtt"]["repository"] == (ROOT / ".local/grammar").as_uri()
    assert "path" not in dev["grammars"]["webvtt"]
    for p in (ROOT / "languages").rglob("*.scm"):
        assert p.read_bytes() == (ROOT / ".local/dev-extension/languages" / p.relative_to(ROOT / "languages")).read_bytes()
    print("Highlight captures, CSS injection range, grammar pin, and isolated dev setup passed.")


if __name__ == "__main__":
    main()
