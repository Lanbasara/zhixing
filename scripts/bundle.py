#!/usr/bin/env python3
"""Assemble Zhixing's content package; no installation or network access."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

import yaml

import check

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
MAX_FILE = 2 * 1024 * 1024


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(value):
    path = PurePosixPath(value)
    if not value or str(path) != value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError("invalid package path")
    if any(part.startswith(".env") or part in {".git", "__pycache__", "node_modules", ".agents"}
           for part in path.parts):
        raise ValueError("development state is not package content")
    return path


def read_file(root, relative):
    path = root
    for part in safe_path(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("package input is a symbolic link: " + relative)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
        raise ValueError("invalid package file: " + relative)
    return path.read_bytes(), 0o755 if info.st_mode & 0o111 else 0o644


def inventory(root):
    result = {}
    if root.is_symlink():
        raise ValueError("package root is a symbolic link")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("package contains a symbolic link")
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            result[rel] = read_file(root, rel)
    return result


def metadata(root):
    version = read_file(root, "VERSION")[0].decode().strip()
    if not VERSION.fullmatch(version):
        raise ValueError("VERSION must be a stable three-part version")
    data = json.loads(read_file(root, "distribution.json")[0])
    if set(data) != {"name", "description", "author", "repository", "dsh"}:
        raise ValueError("unexpected distribution metadata fields")
    if data["name"] != "zhixing" or data["repository"] != "https://github.com/Lanbasara/zhixing":
        raise ValueError("unexpected product identity")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 4096 for v in data.values()):
        raise ValueError("invalid distribution value")
    if not re.fullmatch(r">=\d+\.\d+\.\d+(?:-rc\.\d+)? <\d+\.\d+\.\d+", data["dsh"]):
        raise ValueError("expected a bounded DSH compatibility range")
    return {**data, "version": version}


def assemble(root):
    meta = metadata(root)
    payload = {}
    for directory in ("skills", "principles", "references"):
        if (root / directory).is_symlink():
            raise ValueError("source directory is a symbolic link")
        for path in sorted((root / directory).rglob("*")):
            if path.is_symlink():
                raise ValueError("source resource is a symbolic link")
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                payload[rel] = read_file(root, rel)
    for source, target in {
        "PHILOSOPHY.md": "PHILOSOPHY.md",
        "INSTALL.md": "INSTALL.md",
        "evaluations/README.md": "evaluations/README.md",
        "USAGE.md": "README.md",
        "adapters/dsh.mjs": "host/dsh.mjs",
    }.items():
        payload[target] = read_file(root, source)
    catalog = []
    for name in sorted(check.SKILLS):
        data = payload["skills/" + name + "/SKILL.md"][0].decode()
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", data, re.DOTALL)
        if not match:
            raise ValueError("missing skill frontmatter: " + name)
        skill = yaml.safe_load(match[1])
        if not isinstance(skill, dict) or skill.get("name") != name:
            raise ValueError("skill identity differs from its path")
        catalog.append({"name": name, "description": skill["description"],
                        "invocation": {"modelInvocable": not skill.get("disable-model-invocation", False),
                                       "userInvocable": skill.get("user-invocable", True)}})
    identity = {k: meta[k] for k in ("name", "version", "description")}
    identity.update({"author": {"name": meta["author"]}, "license": "UNLICENSED"})
    generated = {
        "plugin.json": {**identity, "author": {"name": meta["author"]}},
        ".claude-plugin/plugin.json": identity,
        ".codex-plugin/plugin.json": {**identity, "skills": "./skills/"},
        "host/catalog.json": catalog,
    }
    payload["cordis.patch.yml"] = (b"- insert:\n    - id: zhixing-skills\n      name: ./host/dsh.mjs\n", 0o644)
    for name, value in generated.items():
        payload[name] = (json_bytes(value), 0o644)
    package = {**identity, "type": "module", "main": "./host/dsh.mjs", "license": "UNLICENSED",
               "author": meta["author"], "homepage": meta["repository"],
               "repository": {"type": "git", "url": meta["repository"] + ".git"},
               "engines": {"dsh": meta["dsh"]}, "dsh": {"bundle": {"patch": "./cordis.patch.yml"}},
               "files": sorted([*payload, "manifest.json"])}
    payload["package.json"] = (json_bytes(package), 0o644)
    manifest = {"format": 1, "name": meta["name"], "version": meta["version"],
                "files": {p: {"sha256": digest(data), "mode": mode}
                          for p, (data, mode) in sorted(payload.items())}}
    payload["manifest.json"] = (json_bytes(manifest), 0o644)
    return payload


def verify_manifest(payload):
    manifest = json.loads(payload["manifest.json"][0])
    actual = {p: {"sha256": digest(data), "mode": mode}
              for p, (data, mode) in payload.items() if p != "manifest.json"}
    if set(manifest) != {"format", "name", "version", "files"} or manifest["format"] != 1:
        raise ValueError("invalid manifest schema")
    if manifest["name"] != "zhixing" or manifest["files"] != actual:
        raise ValueError("package differs from its complete manifest")
    package = json.loads(payload["package.json"][0])
    if package["name"] != "zhixing" or package["version"] != manifest["version"]:
        raise ValueError("package identity differs from manifest")
    for path in payload:
        safe_path(path)
    return manifest


def write_new(payload, out):
    if out.exists() or out.is_symlink():
        raise ValueError("output must be a new directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".zhixing-", dir=out.parent) as temporary:
        staged = Path(temporary) / "package"
        staged.mkdir()
        for relative, (data, mode) in payload.items():
            path = staged.joinpath(*safe_path(relative).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(mode)
        # mkdir refuses an existing destination; never replace a user's tree.
        out.mkdir()
        for path in staged.iterdir():
            os.rename(path, out / path.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    errors = check.check(args.root)
    if errors:
        raise ValueError("\n".join(errors))
    payload = assemble(args.root)
    verify_manifest(payload)
    if args.check:
        if inventory(args.root / "plugin") != payload:
            raise ValueError("plugin/ differs from source; build and validate a fresh directory first")
    else:
        write_new(payload, args.out)
        errors = check.check(args.out)
        if errors:
            raise ValueError("\n".join(errors))
    print("PASS: reproducible Zhixing bundle and complete manifest")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, yaml.YAMLError) as exc:
        raise SystemExit(str(exc)) from exc
