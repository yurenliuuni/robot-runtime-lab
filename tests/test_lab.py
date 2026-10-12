import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("lab", Path(__file__).resolve().parents[1] / "scripts/lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        # platform.platform() may launch its own subprocess on macOS. Keep that
        # environment probe outside the subprocess mock used for runner tests.
        patcher = patch.object(lab.platform, "platform", return_value="test-platform")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_hash_detects_tampering_and_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "data.csv"
            p.write_text("original")
            hashes = {"data.csv": lab.digest(p)}
            lab.verify_hashes(root, hashes)
            p.write_text("changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                lab.verify_hashes(root, hashes)
            with self.assertRaisesRegex(ValueError, "leaves"):
                lab.within(root, "../outside")

    def test_success_preserves_outputs_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root, target = Path(d), Path(d) / "run"
            def fake(*args, **kwargs):
                (target / "artifacts").mkdir()
                (target / "artifacts/manifest.json").write_text('{"runs": 1}')
                return subprocess.CompletedProcess([], 0)
            with patch.object(lab.subprocess, "run", side_effect=fake):
                self.assertEqual(lab.run_command(["dummy"], root, target, {}), 0)
            record = json.loads((target / "run.json").read_text())
            self.assertEqual(record["status"], "completed")
            self.assertIn("artifacts/manifest.json", record["output_sha256"])
            before = (target / "run.json").read_bytes()
            with self.assertRaises(FileExistsError):
                lab.run_command(["dummy"], root, target, {})
            self.assertEqual(before, (target / "run.json").read_bytes())

    def test_failed_run_keeps_returncode_and_logs(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "failure"
            with patch.object(lab.subprocess, "run", return_value=subprocess.CompletedProcess([], 7)):
                self.assertEqual(lab.run_command(["dummy"], Path(d), target, {}), 7)
            record = json.loads((target / "run.json").read_text())
            self.assertEqual((record["status"], record["exit_code"]), ("failed", 7))
            self.assertIn("stderr.log", record["output_sha256"])

    def test_success_exit_without_artifact_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "missing"
            with patch.object(lab.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
                self.assertEqual(lab.run_command(["dummy"], Path(d), target, {}), 1)

    def test_launch_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "failure"
            with patch.object(lab.subprocess, "run", side_effect=OSError("cannot execute")):
                self.assertEqual(lab.run_command(["dummy"], Path(d), target, {}), 1)
            record = json.loads((target / "run.json").read_text())
            self.assertEqual(record["status"], "failed")
            self.assertIn("cannot execute", record["error"])

    def test_planned_experiment_cannot_be_run(self):
        with self.assertRaisesRegex(ValueError, "planned"):
            lab.benchmark("SYS-001", "smoke")


if __name__ == "__main__":
    unittest.main()
