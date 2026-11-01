#!/usr/bin/env python3
"""Produce three host catalogs from an immutable release and committed market history."""

import argparse
import json
from pathlib import Path
import subprocess

import bundle
import release

REPOSITORY = "https://github.com/Lanbasara/zhixing"
FILES = ("releases.json", ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "dsh/index.json")


def catalogs(history, description):
    claude = {"name": "zhixing", "owner": {"name": "Lanbasara"}, "plugins": []}
    codex = {"name": "zhixing", "interface": {"displayName": "知行 Zhixing"}, "plugins": []}
    dsh = {"format": 1, "title": {"en": "Zhixing", "zh": "知行"}, "plugins": []}
    if history:
        latest = history[0]
        source = {"source": "git-subdir", "url": REPOSITORY + ".git", "path": "plugin",
                  "sha": latest["commit"], "ref": "v" + latest["version"]}
        claude["plugins"] = [{"name": "zhixing", "description": description, "source": source}]
        codex["plugins"] = [{"name": "zhixing", "description": description,
                              "source": {**source, "path": "./plugin"},
                              "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
                              "category": "Productivity"}]
        dsh["plugins"] = [{"name": "zhixing", "title": {"en": "Zhixing", "zh": "知行"},
                            "description": description, "author": "Lanbasara", "homepage": REPOSITORY,
                            "versions": [{"version": row["version"], "publishTimestamp": row["timestamp"],
                                          "engines": {"dsh": row["dsh"]},
                                          "source": {"type": "git", "url": REPOSITORY + ".git",
                                                     "commit": row["commit"], "path": "plugin"}}
                                         for row in history]}]
    return dict(zip(FILES, ({"format": 1, "releases": history}, claude, codex, dsh)))


def row_for(repo, tag):
    payload, identity = release.committed(repo, tag, official=True)
    package = json.loads(payload["package.json"][0])
    return {"version": identity["version"], "commit": identity["commit"],
            "timestamp": identity["timestamp"], "dsh": package["engines"]["dsh"]}, package["description"]


def candidate(repo, market, tag):
    base = release.git(market, "rev-parse", "HEAD").decode().strip()
    if base != release.git(market, "rev-parse", "refs/remotes/origin/main").decode().strip():
        raise ValueError("market history must be committed origin/main")
    data = json.loads(release.git(market, "show", base + ":releases.json"))
    if not isinstance(data, dict) or set(data) != {"format", "releases"} or data["format"] != 1:
        raise ValueError("invalid market history schema")
    history = data["releases"]
    if not isinstance(history, list) or len(history) > 1000:
        raise ValueError("invalid market history")
    new, description = row_for(repo, tag)
    versions = []
    for row in history:
        if not isinstance(row, dict) or set(row) != {"version", "commit", "timestamp", "dsh"}:
            raise ValueError("invalid release history entry")
        if not isinstance(row["version"], str) or not bundle.VERSION.fullmatch(row["version"]):
            raise ValueError("invalid historical version")
        authenticated, _ = row_for(repo, "v" + row["version"])
        if row != authenticated:
            raise ValueError("market history differs from its immutable source tag")
        versions.append(tuple(map(int, row["version"].split("."))))
    target = tuple(map(int, new["version"].split(".")))
    if versions != sorted(set(versions), reverse=True) or any(target <= version for version in versions):
        raise ValueError("new version must advance strictly descending, unique history")
    result = {name: (bundle.json_bytes(value), 0o644)
              for name, value in catalogs([new, *history], description).items()}
    record = {"format": 1, "sourceCommit": new["commit"], "tag": tag, "marketplaceBase": base,
              "files": {path: bundle.digest(data) for path, (data, _) in sorted(result.items())}}
    result["candidate.json"] = (bundle.json_bytes(record), 0o644)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=bundle.ROOT)
    parser.add_argument("--marketplace", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # The catalog is a data-only review artifact, never an automatic remote write.
    payload = candidate(args.repo, args.marketplace, args.tag)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("marketplace output must be new")
    args.out.mkdir()
    for name, (data, _) in payload.items():
        # These exact generated paths intentionally include the Codex host catalog.
        if name not in (*FILES, "candidate.json"):
            raise ValueError("unexpected marketplace output")
        path = args.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print("PASS: three host catalogs pin one immutable tag and committed market base")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from exc
