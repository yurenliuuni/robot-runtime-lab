#!/usr/bin/env python3
"""Standard-library entry point for auditable research runs (Python 3.11+)."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import tomllib
import uuid

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {"smoke": (2, 0, False), "baseline": (30, 0, False),
            "validation": (30, 30, True)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path leaves the research lab: {value}")
    return path


def registry(root=ROOT):
    data = tomllib.loads((root / "experiments/registry.toml").read_text())
    if data.get("schema_version") != 1:
        raise ValueError("unsupported registry schema")
    items = data["experiment"]
    if len({x["id"] for x in items}) != len(items):
        raise ValueError("duplicate experiment IDs")
    for item in items:
        if item["status"] not in {"planned", "active", "measured", "retired"}:
            raise ValueError(f"invalid status: {item['id']}")
        for key in ("path", "protocol", "results"):
            if key in item and not within(root, item[key]).exists():
                raise ValueError(f"missing {key} for {item['id']}")
        if item["status"] == "measured" and not {"protocol", "results"} <= item.keys():
            raise ValueError("measured experiments need protocol and results")
    return items


def verify_hashes(root, hashes):
    for name, expected in hashes.items():
        path = within(root, name)
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"evidence hash mismatch: {name}")


def check(root=ROOT):
    items = registry(root)
    lock = json.loads((root / "experiments/results/evidence-lock.json").read_text())
    if not lock["sha256"]:
        raise ValueError("empty evidence lock")
    verify_hashes(root, lock["sha256"])
    count = 0
    for path in sorted((root / "experiments/results").glob("*/*/run.json")):
        run = json.loads(path.read_text())
        if run["status"] not in {"completed", "failed", "running"}:
            raise ValueError(f"invalid run status: {path}")
        if run["status"] == "running":
            raise ValueError(f"unfinished run needs inspection: {path}")
        if (run["status"] == "completed") != (run["exit_code"] == 0):
            raise ValueError(f"inconsistent run outcome: {path}")
        if run["status"] == "completed" and "artifacts/manifest.json" not in run["output_sha256"]:
            raise ValueError(f"completed run has no manifest: {path}")
        verify_hashes(path.parent, run["output_sha256"])
        count += 1
    print(f"OK: {len(items)} experiments, {len(lock['sha256'])} archived artifacts, {count} run records")


def git_info(root):
    def read(*args):
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else None
    commit = read("rev-parse", "HEAD")
    status = read("status", "--porcelain")
    return {"commit": commit, "dirty": None if status is None else bool(status)}


def run_command(command, cwd, run_dir, metadata):
    """Create once; never reuse/overwrite an old run, even on failure."""
    run_dir.mkdir(parents=True, exist_ok=False)
    record = {**metadata, "command": command, "cwd": str(cwd),
              "started_at": datetime.now(timezone.utc).isoformat(),
              "status": "running", "python": platform.python_version(),
              "platform": platform.platform()}
    record_path = run_dir / "run.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    start = time.perf_counter()
    returncode = 1
    try:
        with (run_dir / "stdout.log").open("w") as out, (run_dir / "stderr.log").open("w") as err:
            returncode = subprocess.run(command, cwd=cwd, stdout=out, stderr=err).returncode
            if returncode == 0 and not (run_dir / "artifacts/manifest.json").is_file():
                err.write("Expected artifacts/manifest.json was not produced.\n")
                returncode = 1
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record.update(status="completed" if returncode == 0 else "failed", exit_code=returncode,
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      wall_seconds=time.perf_counter() - start)
        record["output_sha256"] = {p.relative_to(run_dir).as_posix(): digest(p)
                                    for p in sorted(run_dir.rglob("*"))
                                    if p.is_file() and p != record_path}
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return returncode


def benchmark(experiment_id, profile, root=ROOT):
    items = {x["id"]: x for x in registry(root)}
    if experiment_id not in items:
        raise ValueError(f"unknown experiment: {experiment_id}")
    if experiment_id not in {"RRL-001", "SYS-001", "RRL-002"} or items[experiment_id]["status"] not in {"active", "measured"}:
        raise ValueError("planned experiments have no executable benchmark yet")
    seeds, seed_start, improved = PROFILES[profile]
    if experiment_id == "SYS-001":
        seeds, seed_start, improved = {"smoke": (2,120,False), "baseline": (30,60,False), "validation": (30,90,False)}[profile]
    if experiment_id == "RRL-002":
        seeds, seed_start, improved = {"smoke": (2,400,False), "baseline": (100,200,False), "validation": (100,300,False)}[profile]
    workdir = within(root, items[experiment_id]["path"])
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = root / "experiments/results" / experiment_id / run_id
    command = [sys.executable, "-m", "robot_runtime_lab.experiment", "--seeds", str(seeds),
               "--seed-start", str(seed_start), "--out", str(run_dir / "artifacts")]
    if experiment_id == "SYS-001":
        command = [sys.executable, "ablation.py", "--profile", profile, "--out", str(run_dir / "artifacts")]
    if experiment_id == "RRL-002":
        command = [sys.executable, "experiment.py", "--profile", profile, "--out", str(run_dir / "artifacts")]
    if improved:
        command.append("--include-v3")
    sources = sorted((workdir / "robot_runtime_lab").glob("*.py"))
    sources += sorted((workdir / "docs").glob("*protocol.md"))
    if experiment_id in {"SYS-001", "RRL-002"}:
        sources += sorted(workdir.glob("*.py")) + [workdir / "protocol.md"]
        sources += sorted((root / "robotics/resource-scheduling/robot_runtime_lab").glob("*.py"))
    sources += [root / "scripts/lab.py", root / "experiments/registry.toml"]
    metadata = {"run_id": run_id, "experiment_id": experiment_id, "profile": profile,
                "purpose": "pipeline-validation" if profile == "smoke" else "research-reproduction",
                "git": git_info(root), "seeds": list(range(seed_start, seed_start + seeds)),
                "source_sha256": {p.relative_to(root).as_posix(): digest(p) for p in sources}}
    code = run_command(command, workdir, run_dir, metadata)
    print(f"{'completed' if code == 0 else 'failed'}: {run_dir.relative_to(root)}")
    return code


def test(root=ROOT):
    for cwd, directory in [(root, "tests"), (root / "robotics/resource-scheduling", "tests"), (root / "computer-systems/process-scheduling", "tests"), (root / "robotics/robot-runtime", "tests")]:
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", directory, "-v"], cwd=cwd)
        if result.returncode:
            return result.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "check", "test"):
        commands.add_parser(name)
    bench = commands.add_parser("benchmark")
    bench.add_argument("experiment_id")
    bench.add_argument("--profile", choices=PROFILES, default="smoke")
    args = parser.parse_args()
    try:
        if args.command == "list":
            for item in registry():
                print(f"{item['id']:8} {item['status']:9} {item['title']}")
        elif args.command == "check":
            check()
        elif args.command == "test":
            return test()
        else:
            return benchmark(args.experiment_id, args.profile)
    except (ValueError, OSError, KeyError) as exc:
        print(f"lab: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
