#!/usr/bin/env python3
"""Verify the example notes CLI through fresh processes; retain JSON evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import uuid


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(directory):
    return {
        str(path.relative_to(directory)): (
            {"bytes": path.stat().st_size, "sha256": digest(path)}
            if path.is_file() else {"directory": True}
        )
        for path in sorted(directory.rglob("*"))
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", type=Path, default=Path(__file__).with_name("notes.py"),
                        help="notes.py or a compatible copy (default: beside this script)")
    parser.add_argument("--evidence", type=Path, required=True,
                        help="new evidence directory outside the source tree; never overwritten")
    args = parser.parse_args()
    program, evidence = args.program.resolve(), args.evidence.resolve()
    try:
        evidence.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.error(f"cannot create a new evidence directory: {exc}")

    expected = {"existing": "保留已有笔记", "added": "Saved across processes\n第二行"}
    dataset_id = str(uuid.uuid4())
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "program": {"path": str(program)},
        "verifier": {"path": str(Path(__file__).resolve()), "sha256": digest(Path(__file__))},
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform()},
        "dataset_id": dataset_id, "expected_notes": expected,
        "steps": [], "checks": [], "snapshots": {}, "result": "FAIL",
    }
    workspace = None

    def expect(claim, actual, wanted):
        passed = actual == wanted
        report["checks"].append({"claim": claim, "actual": actual,
                                 "expected": wanted, "passed": passed})
        if not passed:
            raise AssertionError(claim)

    def run(*arguments):
        command = [sys.executable, str(program), "--store", str(store), *arguments]
        step = {"argv": command, "returncode": None, "stdout": "", "stderr": ""}
        report["steps"].append(step)
        try:
            completed = subprocess.run(command, cwd=workspace, capture_output=True,
                                       text=True, encoding="utf-8", timeout=10)
        except subprocess.TimeoutExpired as exc:
            # run() kills and waits for the child; captured output can still be bytes.
            def captured_text(output):
                return output.decode("utf-8", errors="replace") if isinstance(output, bytes) else (output or "")

            step.update(timed_out=True, timeout_seconds=10,
                        stdout=captured_text(exc.stdout), stderr=captured_text(exc.stderr))
            raise
        step.update(returncode=completed.returncode, stdout=completed.stdout,
                    stderr=completed.stderr)
        if completed.returncode:
            raise RuntimeError(f"CLI exited {completed.returncode}: {arguments[0]}")
        return completed.stdout

    def read(*arguments):
        return json.loads(run(*arguments))

    try:
        report["program"]["sha256"] = digest(program)
        with tempfile.TemporaryDirectory(prefix="notes-verification-") as temporary:
            workspace = Path(temporary).resolve()
            store = workspace / "notes.json"
            report["workspace"] = str(workspace)
            expect("program identity", run("--version").strip(), "notes-example 1")
            expect("new dataset created", read("init", "--id", dataset_id),
                   {"created": dataset_id})
            status = {"program": "notes-example 1", "schema": 1, "store": str(store),
                      "id": dataset_id, "count": 0}
            expect("correct readable empty dataset", read("status"), status)
            expect("empty initial notes", read("list"), {})
            report["snapshots"]["initial"] = snapshot(workspace)

            expect("seed save acknowledged", read("put", "--name", "existing", "--text",
                                                  expected["existing"]), {"saved": "existing"})
            expect("seed survives a new process", read("list"),
                   {"existing": expected["existing"]})
            report["snapshots"]["seeded"] = snapshot(workspace)

            expect("new save acknowledged", read("put", "--name", "added", "--text",
                                                 expected["added"]), {"saved": "added"})
            report["snapshots"]["written"] = snapshot(workspace)
            expect("new process reads both exact notes", read("list"), expected)
            expect("same dataset after writes", read("status"), dict(status, count=2))
            report["snapshots"]["read"] = snapshot(workspace)
            expect("only the intended store exists", list(snapshot(workspace)), ["notes.json"])
            expect("write changed persistent bytes",
                   report["snapshots"]["written"] != report["snapshots"]["seeded"], True)
            expect("reads leave persistent bytes unchanged",
                   report["snapshots"]["read"], report["snapshots"]["written"])
        report["result"] = "PASS"
    except Exception as exc:
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}

    report["workspace_removed"] = workspace is not None and not workspace.exists()
    if workspace is not None and not report["workspace_removed"]:
        report["result"] = "FAIL"
        report["cleanup_failure"] = "owned workspace still exists"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    output = evidence / "report.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"{report['result']}: {output}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
