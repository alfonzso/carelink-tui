# CareLink KDE Bar

Native KDE Plasma widget for showing CareLink blood sugar data in a panel.

The widget reads from the existing CareLink proxy and displays:

- Current blood sugar value.
- A compact long-history graph, defaulting to 45 readings.
- A compact short-history graph, defaulting to 15 readings.

It intentionally does not include the CPU, RAM, or clock widgets from `winbar/`.

## Requirements

- KDE Plasma 6.
- A reachable CareLink proxy, for example this repository's `carelink-lib/client_proxy.py`.
- Proxy endpoints:
  - `/carelink/get-current-bsd`
  - `/carelink/get-last-bsd?last-n=N`

## Install

From the repository root:

```bash
bash kdebar/install.sh
```

To restart Plasma Shell after install or upgrade:

```bash
bash kdebar/install.sh --restart-plasma
```

Then add **CareLink KDE Bar** to your bottom panel from KDE's **Add Widgets** menu.

Manual install/upgrade commands:

```bash
kpackagetool6 --type Plasma/Applet --install kdebar
kpackagetool6 --type Plasma/Applet --upgrade kdebar
```

## Build A Copyable Package

Create a `.plasmoid` package from the repository root:

```bash
bash kdebar/package.sh
```

This creates:

```text
dist/carelink-kdebar-0.1.0-<hash>.plasmoid
dist/reinstall-carelink-kdebar.sh
```

The hash is calculated from the full `kdebar/` source tree and is also written into the packaged widget metadata version as `0.1.0+<hash>`.

Copy that file to the KDE machine and open it. On many KDE systems, double-clicking the `.plasmoid` file opens the Plasma package installer or Discover.

If double-click install is not associated on that machine, install it from a terminal:

```bash
kpackagetool6 --type Plasma/Applet --install carelink-kdebar-0.1.0-<hash>.plasmoid
```

For fast testing on the KDE machine, copy both files from `dist/` to the same directory and run:

```bash
bash reinstall-carelink-kdebar.sh
```

The reinstall script removes the existing `net.lehel.carelink.kdebar` package, deletes the local applet directory, clears the Plasma QML cache, installs the newest `carelink-kdebar-*.plasmoid` next to the script, and restarts Plasma Shell.

If Plasma does not show the updated widget immediately, restart Plasma Shell:

```bash
systemctl --user restart plasma-plasmashell.service
```

On systems without the systemd user service:

```bash
kquitapp6 plasmashell
kstart6 plasmashell
```

## Configure

Open the widget settings and adjust:

- **Proxy base URL**: defaults to `http://carelink.lehel.net`.
- **Refresh interval**: defaults to 120 seconds.
- **Long graph readings**: defaults to 45.
- **Short graph readings**: defaults to 15.

For a local proxy, use:

```text
http://localhost:8081
```

## Development

The widget package id is:

```text
net.lehel.carelink.kdebar
```

Useful commands:

```bash
bash kdebar/package.sh
bash dist/reinstall-carelink-kdebar.sh dist/carelink-kdebar-0.1.0-<hash>.plasmoid
bash kdebar/install.sh --remove
kpackagetool6 --type Plasma/Applet --list | rg carelink
kpackagetool6 --type Plasma/Applet --remove net.lehel.carelink.kdebar
```

## Troubleshooting

If the widget shows `--`, check the proxy directly:

```bash
curl http://localhost:8081/carelink/get-current-bsd
curl 'http://localhost:8081/carelink/get-last-bsd?last-n=15'
```

The proxy returns `0` when it has no current reading, and the widget treats that as missing data.
