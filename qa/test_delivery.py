import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bundle
import check
import marketplace
import qa as gate
import release


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = bundle.assemble(bundle.ROOT)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="zhixing-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def git(self, repo, *args):
        return release.git(repo, "-c", "tag.gpgSign=false", "-c", "commit.gpgsign=false",
                           "-c", "core.hooksPath=/dev/null", *args)

    def repo(self):
        repo = self.root / "source"
        repo.mkdir()
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Zhixing test")
        self.git(repo, "config", "user.email", "test@example.invalid")
        bundle.write_new(self.payload, repo / "plugin")
        version = json.loads(self.payload["package.json"][0])["version"]
        (repo / "VERSION").write_text(version + "\n")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "fixture")
        self.git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.git(repo, "tag", "-a", "v" + version, "-m", "fixture release")
        return repo, "v" + version

    def market(self):
        repo = self.root / "market"
        repo.mkdir()
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Zhixing test")
        self.git(repo, "config", "user.email", "test@example.invalid")
        (repo / "releases.json").write_bytes(bundle.json_bytes({"format": 1, "releases": []}))
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "empty marketplace")
        self.git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        return repo

    def test_short_names_and_portable_resources(self):
        package = self.root / "package"
        bundle.write_new(self.payload, package)
        self.assertEqual(check.check(package), [])
        self.assertNotIn(".agents/skills/zhixing-release/SKILL.md", self.payload)
        self.assertNotIn("AGENTS.md", self.payload)
        self.assertEqual({p.split("/")[1] for p in self.payload if p.startswith("skills/")}, check.SKILLS)
        (package / "references/context.md").unlink()
        self.assertTrue(check.check(package))

    def test_user_documentation_is_independent_of_maintainer_inputs(self):
        source = self.root / "source"
        shutil.copytree(bundle.ROOT, source, ignore=shutil.ignore_patterns(
            ".git", "plugin", "__pycache__", ".venv", ".env*", "node_modules"))
        before = bundle.assemble(source)
        for name in ("README.md", "AGENTS.md", "RELEASING.md",
                     ".agents/skills/zhixing-release/SKILL.md",
                     ".github/workflows/ci.yml", "scripts/release.py", "qa/maintainer.txt"):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Changed maintainer-only input\n", encoding="utf-8")
        self.assertTrue(before == bundle.assemble(source),
                        "Maintainer-only changes leaked into the published payload")

        guide = source / "USAGE.md"
        guide.write_text(guide.read_text(encoding="utf-8") + "\nUpdated user guidance.\n",
                         encoding="utf-8")
        after = bundle.assemble(source)
        self.assertEqual(after["README.md"][0], guide.read_bytes())
        self.assertNotEqual(after["README.md"], before["README.md"])
        package = self.root / "package"
        bundle.write_new(after, package)
        self.assertEqual(check.check(package), [])

        guide.unlink()
        with self.assertRaises(FileNotFoundError):
            bundle.assemble(source)

    def test_complete_manifest_detects_add_remove_content_and_mode(self):
        bundle.verify_manifest(self.payload)
        for mutation in ("extra", "missing", "content", "mode"):
            with self.subTest(mutation=mutation):
                altered = dict(self.payload)
                path = "principles/feedback.md"
                if mutation == "extra":
                    altered["secret.txt"] = (b"not approved", 0o644)
                elif mutation == "missing":
                    del altered[path]
                elif mutation == "content":
                    altered[path] = (b"changed", 0o644)
                else:
                    altered[path] = (altered[path][0], 0o755)
                with self.assertRaises(ValueError):
                    bundle.verify_manifest(altered)

    def test_new_output_and_link_boundaries(self):
        package = self.root / "package"
        bundle.write_new(self.payload, package)
        with self.assertRaises(ValueError):
            bundle.write_new(self.payload, package)
        (package / "escape").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            bundle.inventory(package)
        for path in ("../x", "/x", "skills/../x", "skills\\x", "skills/.env", ".agents/skills/release/SKILL.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                bundle.safe_path(path)

    def test_npm_filtering_failure_is_detected(self):
        payload = dict(self.payload)
        package = json.loads(payload["package.json"][0])
        package["files"].remove("references/verification-example/notes.py")
        payload["package.json"] = (bundle.json_bytes(package), 0o644)
        manifest = json.loads(payload["manifest.json"][0])
        manifest["files"]["package.json"]["sha256"] = bundle.digest(payload["package.json"][0])
        payload["manifest.json"] = (bundle.json_bytes(manifest), 0o644)
        path = self.root / "package"
        bundle.write_new(payload, path)
        scratch = self.root / "scratch"
        scratch.mkdir()
        with self.assertRaisesRegex(ValueError, "npm payload differs"):
            gate.packed_contract(path, scratch)

    def test_release_is_repeatable_and_ignores_uncommitted_files(self):
        repo, tag = self.repo()
        expected = release.artifacts(repo, tag, True)
        (repo / "plugin/skills/align/SKILL.md").write_text("uncommitted")
        (repo / "VERSION").write_text("9.9.9")
        self.assertEqual(release.artifacts(repo, tag, True), expected)
        out = self.root / "download"
        bundle.write_new(expected, out)
        release.verify_download(repo, out, tag, True)
        (out / "release.json").write_text("{}")
        with self.assertRaises(ValueError):
            release.verify_download(repo, out, tag, True)
        self.assertFalse(json.loads(release.artifacts(repo, "HEAD")["release.json"][0])["official"])

    def test_formal_release_rejects_wrong_version_lightweight_and_non_main(self):
        repo, tag = self.repo()
        with self.assertRaises(ValueError):
            release.artifacts(repo, "HEAD", True)
        self.git(repo, "tag", "-d", tag)
        self.git(repo, "tag", tag)
        with self.assertRaisesRegex(ValueError, "annotated"):
            release.artifacts(repo, tag, True)
        self.git(repo, "tag", "-d", tag)
        (repo / "extra.txt").write_text("branch-only")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "outside main")
        self.git(repo, "tag", "-a", tag, "-m", "fixture")
        with self.assertRaises(subprocess.CalledProcessError):
            release.artifacts(repo, tag, True)

    def test_committed_tampering_and_link_rejected(self):
        repo, _ = self.repo()
        (repo / "plugin/README.md").write_text("changed")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "invalid payload")
        with self.assertRaises(ValueError):
            release.artifacts(repo, "HEAD")
        (repo / "plugin/escape").symlink_to("../VERSION")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "invalid symlink")
        with self.assertRaisesRegex(ValueError, "non-regular"):
            release.artifacts(repo, "HEAD")

    def test_catalogs_pin_one_commit_and_reject_repeated_release(self):
        repo, tag = self.repo()
        market = self.market()
        result = marketplace.candidate(repo, market, tag)
        record = json.loads(result["candidate.json"][0])
        dsh = json.loads(result["dsh/index.json"][0])["plugins"][0]
        claude = json.loads(result[".claude-plugin/marketplace.json"][0])["plugins"][0]
        codex = json.loads(result[".agents/plugins/marketplace.json"][0])["plugins"][0]
        self.assertEqual(claude["source"]["sha"], record["sourceCommit"])
        self.assertEqual(codex["source"]["sha"], record["sourceCommit"])
        self.assertEqual(dsh["versions"][0]["source"]["commit"], record["sourceCommit"])
        (market / "releases.json").write_bytes(result["releases.json"][0])
        self.git(market, "add", ".")
        self.git(market, "commit", "-m", "release record")
        with self.assertRaisesRegex(ValueError, "origin/main"):
            marketplace.candidate(repo, market, tag)
        self.git(market, "update-ref", "refs/remotes/origin/main", "HEAD")
        with self.assertRaisesRegex(ValueError, "advance"):
            marketplace.candidate(repo, market, tag)
        history = json.loads(result["releases.json"][0])
        history["releases"][0]["commit"] = "a" * 40
        (market / "releases.json").write_bytes(bundle.json_bytes(history))
        self.git(market, "add", ".")
        self.git(market, "commit", "-m", "forged history")
        self.git(market, "update-ref", "refs/remotes/origin/main", "HEAD")
        with self.assertRaisesRegex(ValueError, "immutable source"):
            marketplace.candidate(repo, market, tag)


if __name__ == "__main__":
    unittest.main()
