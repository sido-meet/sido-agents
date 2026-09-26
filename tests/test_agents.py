import importlib.util
import tempfile
import tomllib
import unittest
import shutil
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location("agents", Path(__file__).resolve().parents[1] / "scripts/agents.py")
agents = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agents)


class AgentTests(unittest.TestCase):
    def test_codex_roundtrip_and_readonly(self):
        files = agents.render("codex", "strict-dev-team")
        for a in agents.catalog("strict-dev-team"):
            config = tomllib.loads(files[f'.codex/agents/strict-dev-team-{a["name"]}.toml'].decode())
            self.assertIn("## 快照与证据", config["developer_instructions"])
            self.assertEqual(config["name"], "strict-dev-team-" + a["name"])
            if a["access"] == "read":
                self.assertEqual(config["sandbox_mode"], "read-only")

    def test_conflict_preflight_preserves_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "existing").write_bytes(b"user content")
            with self.assertRaises(ValueError):
                agents.write_files(root, {"new": b"new", "existing": b"replacement"})
            self.assertFalse((root / "new").exists())
            self.assertEqual((root / "existing").read_bytes(), b"user content")

    def test_dry_run_install_and_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = agents.render("claude", "strict-dev-team", ["reviewer"])
            agents.write_files(root, files, dry_run=True)
            self.assertEqual(list(root.iterdir()), [])
            agents.write_files(root, files)
            agents.write_files(root, files)
            self.assertEqual({p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}, files)
            content = files[".claude/agents/strict-dev-team-reviewer.md"].decode()
            self.assertIn("tools: Read, Grep, Glob\n", content)
            self.assertIn("disallowedTools: Write, Edit, Bash", content)

    def test_unknown_agent(self):
        with self.assertRaises(ValueError):
            agents.render("workbuddy", "strict-dev-team", ["missing"])

    def test_bundles_with_same_roles_install_together(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = agents.ROOT / "strict-dev-team"
            for name in ("first-team", "second-team"):
                target = root / name
                target.mkdir()
                shutil.copy2(source / "catalog.json", target / "catalog.json")
                shutil.copytree(source / "agents", target / "agents")
                shutil.copytree(source / "workflows", target / "workflows")
            with patch.object(agents, "ROOT", root):
                self.assertEqual(agents.bundles(), ["first-team", "second-team"])
                first = agents.render("codex", "first-team")
                second = agents.render("codex", "second-team")
                self.assertFalse(first.keys() & second.keys())
                config = tomllib.loads(first[".codex/agents/first-team-tester.toml"].decode())
                self.assertIn("owner: first-team-developer", config["developer_instructions"])
                agents.write_files(root / "project", first)
                agents.write_files(root / "project", second)
                with self.assertRaises(ValueError):
                    agents.render("codex", "unknown-team")
                with self.assertRaises(ValueError):
                    agents.render("codex", "../first-team")


if __name__ == "__main__":
    unittest.main()
