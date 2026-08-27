#!/usr/bin/env python3
"""Create a clean Locaweb-ready ZIP and hash manifest for manual FTP deploys."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import json


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "deploy.zip"
MANIFEST_PATH = ROOT / "deploy-manifest.json"
ROOT_FILES = {".htaccess", "robots.txt", "sitemap.xml", "submit.php"}
PUBLIC_DIRS = {"assets", "css", "js", "produto"}


def public_files() -> list[Path]:
    files = [path for path in ROOT.glob("*.html") if path.is_file()]
    files.extend(ROOT / name for name in sorted(ROOT_FILES) if (ROOT / name).is_file())
    for directory in sorted(PUBLIC_DIRS):
        files.extend(path for path in (ROOT / directory).rglob("*") if path.is_file())
    return sorted(set(files), key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    files = public_files()
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": {},
    }
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            archive.writestr(relative, data)
            manifest["files"][relative] = {
                "bytes": len(data),
                "sha256": sha256(data).hexdigest(),
            }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Created {ZIP_PATH.name} with {len(files)} public files.")
    print(f"Created {MANIFEST_PATH.name} for upload verification.")


if __name__ == "__main__":
    main()
