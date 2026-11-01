#!/usr/bin/env python3
"""A tiny persistent notes CLI used by the verification example."""

import argparse
import json
from pathlib import Path


VERSION = "notes-example 1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--store", type=Path, required=True,
                        help="JSON store; its parent directory must already exist")
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init", help="create a store; refuse to overwrite")
    initialize.add_argument("--id", required=True, help="identity of the new dataset")
    commands.add_parser("status", help="report program, store identity and note count")
    put = commands.add_parser("put", help="save or replace one named note")
    put.add_argument("--name", required=True)
    put.add_argument("--text", required=True)
    commands.add_parser("list", help="read all saved notes")
    args = parser.parse_args()

    try:
        if args.command == "init":
            data = {"schema": 1, "id": args.id, "notes": {}}
            with args.store.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False)
            result = {"created": args.id}
        else:
            data = json.loads(args.store.read_text(encoding="utf-8"))
            if data["schema"] != 1 or not isinstance(data["notes"], dict):
                raise ValueError("unsupported store format")
            if args.command == "status":
                result = {"program": VERSION, "schema": data["schema"],
                          "store": str(args.store.resolve()), "id": data["id"],
                          "count": len(data["notes"])}
            elif args.command == "put":
                data["notes"][args.name] = args.text
                args.store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                result = {"saved": args.name}
            else:
                result = data["notes"]
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"notes: {exc}\n")


if __name__ == "__main__":
    main()
