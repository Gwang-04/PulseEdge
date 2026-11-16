from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "pulseedge-deploy-rehearsal.zip"

INCLUDE_PATHS = [
    "app.py",
    "auth_service.py",
    "market_data.py",
    "settings.py",
    "user_store.py",
    "signal_engine.py",
    "backtest_engine.py",
    "static",
    "tests",
    "scripts",
    ".env.example",
    "README.md",
    "PULSEEDGE_SPEC.md",
    "PULSEEDGE_REPORT.md",
    "PULSEEDGE_OPERATION_PLAN.md",
    "DEPLOY_DIGITALOCEAN.md",
]

DENY_PARTS = {
    ".env",
    "config.json",
    "user_data",
    "__pycache__",
}

DENY_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".zip",
}

REQUIRED_ARCHIVE_FILES = {
    "app.py",
    "auth_service.py",
    "market_data.py",
    "settings.py",
    "user_store.py",
    "signal_engine.py",
    "backtest_engine.py",
    "static/index.html",
    "static/app.js",
    "static/styles.css",
    "static/service-worker.js",
    "static/icon-192.png",
    "static/icon-512.png",
    ".env.example",
    "tests/test_settings.py",
    "tests/test_auth_service.py",
    "tests/test_user_store.py",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify a safe PulseEdge deployment archive.")
    parser.add_argument("--output", type=Path, default=DEFAULT_ARCHIVE, help="Archive path to create.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip extracted Python unittest run.")
    args = parser.parse_args()

    archive_path = args.output if args.output.is_absolute() else ROOT / args.output
    files = collect_files()
    build_archive(archive_path, files)
    verify_archive(archive_path)
    if not args.skip_tests:
        run_extracted_tests(archive_path)

    print(f"OK deployment rehearsal archive: {archive_path}")
    print(f"OK files included: {len(files)}")
    return 0


def collect_files() -> list[Path]:
    output: list[Path] = []
    for entry in INCLUDE_PATHS:
        path = ROOT / entry
        if not path.exists():
            raise SystemExit(f"Missing required deploy path: {entry}")
        if path.is_dir():
            output.extend(file for file in sorted(path.rglob("*")) if file.is_file() and allowed(file))
        elif allowed(path):
            output.append(path)
    return output


def allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    parts = set(relative.parts)
    if parts & DENY_PARTS:
        return False
    if path.suffix.lower() in DENY_SUFFIXES:
        return False
    return True


def build_archive(archive_path: Path, files: list[Path]) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, file.relative_to(ROOT).as_posix())


def verify_archive(archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())

    missing = sorted(REQUIRED_ARCHIVE_FILES - names)
    if missing:
        raise SystemExit(f"Archive missing required files: {', '.join(missing)}")

    blocked = []
    for name in sorted(names):
        path = Path(name)
        if set(path.parts) & DENY_PARTS or path.suffix.lower() in DENY_SUFFIXES:
            blocked.append(name)
    if blocked:
        raise SystemExit(f"Archive contains blocked files: {', '.join(blocked)}")


def run_extracted_tests(archive_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="pulseedge-deploy-") as temp_dir:
        extract_dir = Path(temp_dir) / "app"
        extract_dir.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=extract_dir,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            sys.stderr.write(completed.stdout)
            sys.stderr.write(completed.stderr)
            raise SystemExit(completed.returncode)
        shutil.rmtree(extract_dir / "user_data", ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
