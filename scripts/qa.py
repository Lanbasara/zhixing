#!/usr/bin/env python3
"""Offline PR gate, or validate a freshly built package before replacing plugin/."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

import bundle
import check


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, timeout=180, **kwargs)


def packed_contract(package, scratch):
    expected = bundle.inventory(package)
    bundle.verify_manifest(expected)
    errors = check.check(package)
    if errors:
        raise ValueError("\n".join(errors))
    staging = scratch / "input"
    bundle.write_new(expected, staging)
    archives = scratch / "archives"
    archives.mkdir()
    for name in ("npm-user", "npm-global"):
        (scratch / name).write_text("", encoding="utf-8")
    env = {key: os.environ[key] for key in ("PATH", "HOME", "SYSTEMROOT", "VOLTA_HOME", "TMPDIR")
           if key in os.environ}
    result = run(["npm", "pack", "--json", "--offline", "--ignore-scripts",
                  "--cache", str(scratch / "npm-cache"),
                  "--userconfig", str(scratch / "npm-user"),
                  "--globalconfig", str(scratch / "npm-global"),
                  "--pack-destination", str(archives)], cwd=staging, env=env,
                 capture_output=True, text=True)
    packs = list(archives.glob("*.tgz"))
    if len(packs) != 1:
        raise ValueError("npm did not produce exactly one archive")
    actual = {}
    with tarfile.open(packs[0], "r:gz") as archive:
        for member in archive:
            if not member.name.startswith("package/") or not member.isfile():
                raise ValueError("npm archive has a non-file entry")
            name = member.name[len("package/"):]
            bundle.safe_path(name)
            if name in actual or member.size > bundle.MAX_FILE:
                raise ValueError("duplicate or oversized npm member")
            actual[name] = (archive.extractfile(member).read(), member.mode)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(p for p in expected.keys() & actual.keys() if expected[p] != actual[p])
        raise ValueError(f"npm payload differs: missing={missing}, extra={extra}, changed={changed}")
    unpacked = scratch / "unpacked"
    bundle.write_new(actual, unpacked)
    run(["node", str(bundle.ROOT / "qa/dsh.mjs"), str(unpacked)], env=env)
    print(f"PASS: npm archive preserves all {len(actual)} paths, bytes and modes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.package:
        with tempfile.TemporaryDirectory(prefix="zhixing-qa-") as temp:
            packed_contract(args.package.resolve(), Path(temp))
        return
    errors = check.check(bundle.ROOT)
    if errors:
        raise ValueError("\n".join(errors))
    payload = bundle.assemble(bundle.ROOT)
    if payload != bundle.inventory(bundle.ROOT / "plugin"):
        raise ValueError("plugin/ is stale; build, validate and replace it before running QA")
    run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "qa", "-p", "test_*.py", "-v"],
        cwd=bundle.ROOT)
    with tempfile.TemporaryDirectory(prefix="zhixing-qa-") as temp:
        packed_contract(bundle.ROOT / "plugin", Path(temp))
    print("PASS: offline PR/release gate; no host installation or model evaluation claimed")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from exc
