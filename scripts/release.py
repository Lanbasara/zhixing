#!/usr/bin/env python3
"""Create reproducible release files from committed Git objects, never the worktree."""

import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

import bundle

REF = re.compile(r"(?:HEAD|[0-9a-f]{40}|v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          timeout=60).stdout


def blobs(repo, ids):
    request = ("\n".join(ids) + "\n").encode()
    command = ["git", "-C", str(repo), "cat-file"]
    sizes = subprocess.run([*command, "--batch-check"], input=request, check=True,
                           capture_output=True, timeout=60).stdout.splitlines()
    total = 0
    for row in sizes:
        _, kind, size = row.split()
        if kind != b"blob" or int(size) > bundle.MAX_FILE:
            raise ValueError("invalid or oversized release object")
        total += int(size)
    if len(sizes) != len(ids) or total > 32 * 1024 * 1024:
        raise ValueError("release exceeds package bounds")
    output = io.BytesIO(subprocess.run([*command, "--batch"], input=request, check=True,
                                      capture_output=True, timeout=60).stdout)
    result = {}
    for expected in ids:
        oid, kind, size = output.readline().split()
        if oid.decode() != expected or kind != b"blob":
            raise ValueError("Git object identity mismatch")
        result[expected] = output.read(int(size))
        if output.read(1) != b"\n":
            raise ValueError("truncated Git object")
    if output.read():
        raise ValueError("extra Git object data")
    return result


def committed(repo, ref, official=False):
    if not REF.fullmatch(ref):
        raise ValueError("expected HEAD, full commit SHA or a stable version tag")
    commit = git(repo, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
    entries = []
    for row in git(repo, "ls-tree", "-rz", commit, "--", "plugin/").split(b"\0"):
        if not row:
            continue
        info, path_bytes = row.split(b"\t", 1)
        mode, kind, oid = info.split()
        path = path_bytes.decode()
        if not path.startswith("plugin/") or kind != b"blob" or mode not in {b"100644", b"100755"}:
            raise ValueError("release tree contains a non-regular file")
        relative = path[len("plugin/"):]
        bundle.safe_path(relative)
        entries.append((relative, oid.decode(), int(mode[-3:], 8)))
    if not entries or len(entries) > 4096:
        raise ValueError("missing or oversized release tree")
    objects = blobs(repo, list(dict.fromkeys(oid for _, oid, _ in entries)))
    payload = {path: (objects[oid], mode) for path, oid, mode in entries}
    if not payload:
        raise ValueError("commit has no plugin/ release tree")
    manifest = bundle.verify_manifest(payload)
    version = git(repo, "show", commit + ":VERSION").decode().strip()
    if not bundle.VERSION.fullmatch(version) or version != manifest["version"]:
        raise ValueError("committed VERSION differs from package")
    if official:
        if ref != "v" + version:
            raise ValueError("formal release tag must equal v + VERSION")
        if git(repo, "cat-file", "-t", "refs/tags/" + ref).strip() != b"tag":
            raise ValueError("formal release needs an annotated tag")
        git(repo, "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main")
    timestamp = int(git(repo, "show", "-s", "--format=%ct", commit))
    return payload, {"format": 1, "name": "zhixing", "version": version, "commit": commit,
                     "tag": ref if official else None, "official": official, "timestamp": timestamp}


def zip_bytes(payload):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, (data, mode) in sorted(payload.items()):
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return output.getvalue()


def artifacts(repo, ref, official=False):
    payload, identity = committed(repo, ref, official)
    archive = zip_bytes(payload)
    metadata = bundle.json_bytes({**identity, "artifact": "zhixing-plugin.zip", "sha256": bundle.digest(archive)})
    result = {"zhixing-plugin.zip": (archive, 0o644), "release.json": (metadata, 0o644)}
    result["SHA256SUMS"] = ("".join(bundle.digest(data) + "  " + name + "\n"
                                          for name, (data, _) in sorted(result.items())).encode(), 0o644)
    return result


def verify_download(repo, directory, ref, official=False):
    expected = artifacts(repo, ref, official)
    actual = bundle.inventory(directory)
    # Product ZIP can exceed individual source file bounds in larger versions.
    if actual != expected:
        raise ValueError("downloaded artifact differs from a rebuild of the exact Git objects")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=bundle.ROOT)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--official", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify_download(args.repo, args.verify, args.ref, args.official)
    else:
        bundle.write_new(artifacts(args.repo, args.ref, args.official), args.out)
    print("PASS: exact committed source, complete manifest and repeatable release files")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc)) from exc
