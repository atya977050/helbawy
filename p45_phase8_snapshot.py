from pathlib import Path
import json
import hashlib
import tarfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "بلبل-الجديد"
VERIFY = ROOT / "plans" / "repair-composition-verification.json"
SNAP_DIR = ROOT / "snapshots"
OUT = ROOT / "plans" / "p45-snapshot-manifest.json"
REPORT = ROOT / "reports" / "p45-phase8-snapshot-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    print("=== P45 PHASE 8 — SNAPSHOT GATE ===")
    print(f"TIME: {now()}")

    if not TARGET.is_dir():
        raise SystemExit(f"STOP: target project missing: {TARGET}")

    if not VERIFY.is_file():
        raise SystemExit(f"STOP: Phase 7 verification missing: {VERIFY}")

    verification = json.loads(
        VERIFY.read_text(encoding="utf-8")
    )

    if verification.get("status") != "COMPOSITION_VERIFIED_NO_EXECUTION":
        raise SystemExit(
            "STOP: Phase 7 is not COMPOSITION_VERIFIED_NO_EXECUTION."
        )

    if verification.get("execution_allowed") is not False:
        raise SystemExit(
            "STOP: execution_allowed must remain False before snapshot."
        )

    SNAP_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive = SNAP_DIR / f"p45-pre-repair-{stamp}.tar.gz"

    files = []
    for path in sorted(TARGET.rglob("*")):
        if path.is_file():
            rel = path.relative_to(TARGET).as_posix()
            files.append({
                "path": rel,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            })

    project_hash = hashlib.sha256()
    for item in files:
        project_hash.update(item["path"].encode("utf-8"))
        project_hash.update(item["sha256"].encode("ascii"))

    project_sha = project_hash.hexdigest()

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(TARGET, arcname="بلبل-الجديد")

    archive_sha = sha256_file(archive)

    manifest = {
        "schema": "P45-SnapshotManifest-v1",
        "phase": 8,
        "created_at": now(),
        "snapshot_status": "CREATED",
        "target": "بلبل-الجديد",
        "target_path": str(TARGET),
        "archive": str(archive),
        "archive_sha256": archive_sha,
        "project_sha256": project_sha,
        "file_count": len(files),
        "files": files,
        "source_verification": {
            "phase": 7,
            "status": verification["status"],
            "execution_allowed": False,
        },
        "execution_allowed": False,
        "target_modification": "NONE",
        "rule": (
            "Snapshot is created before repair application. "
            "The target remains unchanged. "
            "Snapshot does not authorize execution."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "phase": 8,
        "status": "SNAPSHOT_CREATED",
        "target": "بلبل-الجديد",
        "file_count": len(files),
        "project_sha256": project_sha,
        "archive_sha256": archive_sha,
        "archive": str(archive),
        "execution_allowed": False,
        "target_modification": "NONE",
        "created_at": now(),
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 38)
    print(f"SNAPSHOT: CREATED")
    print(f"FILES: {len(files)}")
    print(f"PROJECT SHA256: {project_sha}")
    print(f"ARCHIVE SHA256: {archive_sha}")
    print(f"ARCHIVE: {archive}")
    print(f"MANIFEST: {OUT}")
    print(f"REPORT: {REPORT}")
    print("TARGET MODIFICATION: NONE")
    print("EXECUTION_ALLOWED: False")
    print("=" * 38)


if __name__ == "__main__":
    main()
