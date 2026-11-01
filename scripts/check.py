#!/usr/bin/env python3
"""Check package structure and declared contracts; does not evaluate agent behavior."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    sys.exit("Install check dependencies: python3 -m pip install -r scripts/requirements-check.txt")


EXPLICIT = set("setup align specify plan implement evolve".split())
AUTOMATIC = set("research handoff model constrain verify review debug prototype explain report".split())
SKILLS = EXPLICIT | AUTOMATIC
RESOURCE_DIRS = {"skills", "principles", "references", ".claude-plugin", ".codex-plugin"}
DOC_DIRS = {"docs", "evaluations"}
LOCAL_PATH = re.compile(r"(?:/Users/|/home/|/private/|/tmp/|/var/folders/|/Volumes/|(?<![A-Za-z0-9])[A-Za-z]:[\\/])")
LINK = re.compile(r"\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[\"'][^\n)]*)?\)")
REFERENCE = re.compile(r"^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)


def without_fences(text):
    """Example code is not a declaration of package resources."""
    result, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            result.append(line)
    return "\n".join(result)


def check(root):
    root = root.resolve()
    errors = []

    def fail(path, message):
        errors.append(f"{path.relative_to(root)}: {message}")

    def mapping(path, text, parser):
        try:
            value = parser(text)
            if not isinstance(value, dict):
                raise ValueError("expected a mapping")
            return value
        except (ValueError, yaml.YAMLError) as exc:
            fail(path, f"invalid metadata: {exc}")
            return {}

    manifests = []
    is_source = (root / "VERSION").is_file()
    for host in (() if is_source else (".claude-plugin", ".codex-plugin")):
        path = root / host / "plugin.json"
        if not path.is_file():
            fail(path, "missing manifest")
            continue
        manifest = mapping(path, path.read_text(encoding="utf-8"), json.loads)
        manifests.append(manifest)
        if manifest.get("name") != "zhixing":
            fail(path, "plugin name must be zhixing")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
            fail(path, "version must be a three-part version")
        if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
            fail(path, "description must be a nonempty string")
        # Claude discovers skills/ by default; Codex explicitly declares it.
        expected = "./skills/"
        if manifest.get("skills", expected if host == ".claude-plugin" else None) != expected:
            fail(path, "must discover the shared ./skills/ directory")
    if len(manifests) == 2:
        for field in ("name", "version", "description"):
            if manifests[0].get(field) != manifests[1].get(field):
                fail(root / ".codex-plugin/plugin.json", f"{field} differs between hosts")

    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    discovered = {path.parent.name for path in skill_files}
    if discovered != SKILLS:
        fail(root / "skills", f"skill set mismatch; missing={sorted(SKILLS - discovered)}, extra={sorted(discovered - SKILLS)}")
    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
        if not match:
            fail(path, "missing YAML frontmatter")
            continue
        meta = mapping(path, match[1], yaml.safe_load)
        if meta.get("name") != path.parent.name:
            fail(path, "name must match its canonical skill directory")
        if not isinstance(meta.get("description"), str) or not meta["description"].strip():
            fail(path, "description must be a nonempty string")
        if not text[match.end():].strip():
            fail(path, "missing skill instructions")
        explicit = path.parent.name in EXPLICIT
        if meta.get("disable-model-invocation", False) is not explicit:
            fail(path, "Claude invocation policy does not match the skill's role")
        if meta.get("user-invocable", True) is not True:
            fail(path, "all skills must remain explicitly invocable")
        config = path.parent / "agents/openai.yaml"
        data = mapping(config, config.read_text(encoding="utf-8"), yaml.safe_load) if config.exists() else {}
        policy = data.get("policy", {})
        if not isinstance(policy, dict) or policy.get("allow_implicit_invocation", True) is not (not explicit):
            fail(config, "Codex invocation policy does not match the skill's role")

    for directory in ("skills", "principles", "references"):
        if not (root / directory).is_dir() or not any((root / directory).iterdir()):
            fail(root / directory, "missing or empty shared content directory")
    required_docs = ("PHILOSOPHY.md", "README.md") if is_source else ()
    for name in required_docs:
        if not (root / name).is_file():
            fail(root / name, "missing product documentation")

    # Runtime instructions and metadata must be portable. Development tooling is
    # not scanned as prose; it intentionally contains examples of rejected paths.
    files = list(root.glob("*.md"))
    for directory in RESOURCE_DIRS | DOC_DIRS:
        resource = root / directory
        files.append(resource)
        if not resource.is_symlink():
            files.extend(resource.rglob("*"))
    for path in sorted(set(files)):
        if path.is_symlink():
            fail(path, "package resources must be real files, not symlinks")
            continue
        if path.is_dir():
            continue
        # Supporting assets may use other formats. This check validates text
        # resources and their links, not an exhaustive file-format whitelist.
        if path.suffix not in {".md", ".json", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            fail(path, f"cannot read resource: {exc}")
            continue
        if LOCAL_PATH.search(text):
            fail(path, "contains a machine-local absolute path")
        if path.name == "SKILL.md" and path not in skill_files:
            fail(path, "skill is outside the shared canonical skills directory")
        if path.suffix != ".md":
            continue
        prose = without_fences(text)
        for pattern in (LINK, REFERENCE):
            for match in pattern.finditer(prose):
                target = match[1] or match[2]
                parsed = urlsplit(target)
                if parsed.scheme and parsed.scheme != "file":
                    continue
                if not parsed.path:
                    continue
                destination = (path.parent / unquote(parsed.path)).resolve()
                if parsed.scheme == "file" or destination != root and root not in destination.parents:
                    fail(path, f"resource leaves the package: {target}")
                elif not destination.exists():
                    fail(path, f"resource does not exist: {target}")

    # Evidence, credentials, and generated state do not belong in the product.
    forbidden = {"experiments", "reports", "node_modules", ".venv"}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.name in forbidden or path.name == ".env" or path.name.startswith(".env."):
            fail(path, "local state or evidence is not product content")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root)
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(SKILLS)} short skill names, invocation policies, references and portable content")
    return 0


if __name__ == "__main__":
    sys.exit(main())
