#!/usr/bin/env bash
set -euo pipefail

APPLET_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$APPLET_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required to build the .plasmoid package." >&2
    exit 1
fi

read -r BASE_VERSION SOURCE_HASH < <(python3 - "$APPLET_DIR" <<'PY'
import hashlib
import json
import pathlib
import sys

applet_dir = pathlib.Path(sys.argv[1])
metadata = json.loads((applet_dir / "metadata.json").read_text(encoding="utf-8"))

digest = hashlib.sha256()
for path in sorted(applet_dir.rglob("*")):
    if not path.is_file():
        continue

    relative_path = path.relative_to(applet_dir).as_posix()
    digest.update(relative_path.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")

print(metadata["KPlugin"]["Version"], digest.hexdigest()[:12])
PY
)

PACKAGE_VERSION="${BASE_VERSION}+${SOURCE_HASH}"
PACKAGE_NAME="carelink-kdebar-${BASE_VERSION}-${SOURCE_HASH}.plasmoid"
PACKAGE_PATH="$DIST_DIR/$PACKAGE_NAME"
REINSTALL_SCRIPT_PATH="$DIST_DIR/reinstall-carelink-kdebar.sh"

mkdir -p "$DIST_DIR"
rm -f "$PACKAGE_PATH"
cp "$APPLET_DIR/reinstall-plasmoid.sh" "$REINSTALL_SCRIPT_PATH"

python3 - "$APPLET_DIR" "$PACKAGE_PATH" "$PACKAGE_VERSION" <<'PY'
import json
import pathlib
import sys
import zipfile

applet_dir = pathlib.Path(sys.argv[1])
package_path = pathlib.Path(sys.argv[2])
package_version = sys.argv[3]

include_roots = [
    applet_dir / "README.md",
    applet_dir / "contents",
]

metadata = json.loads((applet_dir / "metadata.json").read_text(encoding="utf-8"))
metadata["KPlugin"]["Version"] = package_version

with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("metadata.json", json.dumps(metadata, indent=4) + "\n")

    for root in include_roots:
        if root.is_file():
            archive.write(root, root.relative_to(applet_dir))
            continue

        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(applet_dir))
PY

echo "Created $PACKAGE_PATH"
echo "Created $REINSTALL_SCRIPT_PATH"
echo "Package version: $PACKAGE_VERSION"
echo "Source hash: $SOURCE_HASH"
echo "Copy this file to a KDE machine and open it, or install it with:"
echo "  kpackagetool6 --type Plasma/Applet --install \"$PACKAGE_PATH\""
echo "For a clean reinstall on the KDE machine, copy both dist files and run:"
echo "  bash reinstall-carelink-kdebar.sh"
