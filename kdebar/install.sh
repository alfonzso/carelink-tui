#!/usr/bin/env bash
set -euo pipefail

APPLET_ID="net.lehel.carelink.kdebar"
APPLET_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RESTART_PLASMA=0
ACTION="install"

usage() {
    cat <<EOF
Usage: $(basename "$0") [options]

Install or update the CareLink KDE Bar Plasma widget.

Options:
  --restart-plasma   Restart Plasma Shell after install or upgrade
  --remove           Remove the installed widget
  -h, --help         Show this help

Examples:
  bash kdebar/install.sh
  bash kdebar/install.sh --restart-plasma
  bash kdebar/install.sh --remove
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
    echo "Install KDE Plasma development/package tools, then rerun this script." >&2
    exit 1
}

is_installed() {
    "$KPACKAGE_TOOL" --type Plasma/Applet --list 2>/dev/null | grep -Fq "$APPLET_ID"
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

while [[ $# -gt 0 ]]; do
    case "$1" in
        --restart-plasma)
            RESTART_PLASMA=1
            ;;
        --remove)
            ACTION="remove"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

KPACKAGE_TOOL="$(find_kpackagetool)"

if [[ "$ACTION" == "remove" ]]; then
    echo "Removing $APPLET_ID"
    "$KPACKAGE_TOOL" --type Plasma/Applet --remove "$APPLET_ID"
    echo "Removed. Restart Plasma Shell if the widget is still visible."
    exit 0
fi

if is_installed; then
    echo "Upgrading $APPLET_ID from $APPLET_DIR"
    "$KPACKAGE_TOOL" --type Plasma/Applet --upgrade "$APPLET_DIR"
else
    echo "Installing $APPLET_ID from $APPLET_DIR"
    "$KPACKAGE_TOOL" --type Plasma/Applet --install "$APPLET_DIR"
fi

if [[ "$RESTART_PLASMA" -eq 1 ]]; then
    echo "Restarting Plasma Shell"
    restart_plasma
fi

echo "Done. Add 'CareLink KDE Bar' to your panel from KDE's Add Widgets menu."
