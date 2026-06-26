#!/usr/bin/env bash
set -euo pipefail

APPLET_ID="net.lehel.carelink.kdebar"
RESTART_PLASMA=1

usage() {
    cat <<EOF
Usage: $(basename "$0") [options] [package.plasmoid]

Remove, clean up, reinstall, and restart Plasma for the CareLink KDE Bar widget.

Options:
  --no-restart       Do not restart Plasma Shell after reinstall
  -h, --help         Show this help

If no package path is provided, the newest carelink-kdebar-*.plasmoid file in the
script directory is used.
EOF
}

find_kpackagetool() {
    if command -v kpackagetool6 >/dev/null 2>&1; then
        command -v kpackagetool6
        return
    fi

    if command -v kpackagetool5 >/dev/null 2>&1; then
        command -v kpackagetool5
        return
    fi

    echo "ERROR: kpackagetool6 or kpackagetool5 was not found." >&2
    exit 1
}

find_default_package() {
    local script_dir package
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    package="$(find "$script_dir" -maxdepth 1 -type f -name 'carelink-kdebar-*.plasmoid' -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"

    if [[ -z "$package" ]]; then
        echo "ERROR: no carelink-kdebar-*.plasmoid package found next to this script." >&2
        exit 1
    fi

    printf '%s\n' "$package"
}

restart_plasma() {
    if command -v systemctl >/dev/null 2>&1 \
        && systemctl --user list-unit-files plasma-plasmashell.service >/dev/null 2>&1; then
        systemctl --user restart plasma-plasmashell.service
        return
    fi

    if command -v kquitapp6 >/dev/null 2>&1 && command -v kstart6 >/dev/null 2>&1; then
        kquitapp6 plasmashell || true
        kstart6 plasmashell
        return
    fi

    if command -v kquitapp5 >/dev/null 2>&1 && command -v kstart5 >/dev/null 2>&1; then
        kquitapp5 plasmashell || true
        kstart5 plasmashell
        return
    fi

    echo "Could not restart Plasma Shell automatically."
    echo "Log out/in or restart plasmashell manually if the widget does not refresh."
}

PACKAGE_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-restart)
            RESTART_PLASMA=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -n "$PACKAGE_PATH" ]]; then
                echo "ERROR: only one package path can be provided." >&2
                exit 1
            fi
            PACKAGE_PATH="$1"
            ;;
    esac
    shift
done

KPACKAGE_TOOL="$(find_kpackagetool)"
PACKAGE_PATH="${PACKAGE_PATH:-$(find_default_package)}"

if [[ ! -f "$PACKAGE_PATH" ]]; then
    echo "ERROR: package not found: $PACKAGE_PATH" >&2
    exit 1
fi

echo "Removing installed applet package if present"
"$KPACKAGE_TOOL" --type Plasma/Applet --remove "$APPLET_ID" >/dev/null 2>&1 || true

echo "Cleaning local applet files and QML cache"
rm -rf "$HOME/.local/share/plasma/plasmoids/$APPLET_ID"
rm -rf "$HOME/.cache/plasmashell/qmlcache"

echo "Installing $PACKAGE_PATH"
"$KPACKAGE_TOOL" --type Plasma/Applet --install "$PACKAGE_PATH"

if [[ "$RESTART_PLASMA" -eq 1 ]]; then
    echo "Restarting Plasma Shell"
    restart_plasma
fi

echo "Done. Add 'CareLink KDE Bar' to your panel from KDE's Add Widgets menu if it is not already visible."
