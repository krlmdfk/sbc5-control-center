# Third-party notices

This file documents **direct external components** used by the SBC5 Control Center application build as audited on **2026-10-22**. The SBC5 Control Center source code is licensed under Apache-2.0; the components below are **not relicensed** and remain under their own terms.

## Container base

- **Home Assistant Base Images** — `ghcr.io/home-assistant/base:3.24` — upstream repository licensed under **Apache-2.0**. The image itself contains Alpine Linux and additional components (including S6 Overlay, Bashio and TempIO) under their respective upstream licenses.
  - Source: https://github.com/home-assistant/docker-base

The Dockerfile is intentionally pinned to the Home Assistant `3.24` base-image line so this audit is not silently invalidated by a moving `latest` tag. Security rebuilds within the `3.24` line may still update package revisions.

## Direct packages installed by the application Dockerfile

| Component | Audited Alpine 3.24 version | License reported by Alpine/upstream | Use in SBC5 Control Center |
|---|---:|---|---|
| `jq` | 1.8.2-r0 | MIT | JSON processing from shell |
| `curl` | 8.22.0-r0 | curl license | Supervisor / Home Assistant HTTP API calls |
| `dtc` | 1.7.2-r1 | GPL-2.0-or-later | Compiles Device Tree overlays as a separate executable |
| `coreutils` | 9.11-r0 | GPL-3.0-or-later | Standard command-line utilities |
| `util-linux` | 2.42.3-r1 | mixed GPL/LGPL/BSD/MIT/Public-Domain by utility | `nsenter`, block/mount/host inspection tools |
| `unzip` | 6.0-r16 | Info-ZIP | Local update archive extraction |
| `python3` | 3.14.x (3.14.8-r0 observed) | PSF-2.0 | Local helper processes |
| `py3-websockets` | 16.0-r1 | BSD-3-Clause | Lovelace/dashboard WebSocket synchronization |
| `raspberrypi-utils-vcgencmd` | 0.20260602-r0 observed | BSD-3-Clause | Raspberry Pi firmware/telemetry queries |

Package versions above are observations from Alpine Linux v3.24 package metadata at audit time. The repository intentionally does not pin every APK revision so security fixes can flow in during rebuilds.

### Source / license references

- Alpine package index: https://pkgs.alpinelinux.org/
- jq: https://github.com/jqlang/jq
- curl: https://curl.se/
- Device Tree Compiler: https://git.kernel.org/pub/scm/utils/dtc/dtc.git/
- GNU coreutils: https://www.gnu.org/software/coreutils/
- util-linux: https://github.com/util-linux/util-linux
- Info-ZIP UnZip: https://infozip.sourceforge.net/UnZip.html
- Python: https://www.python.org/
- websockets: https://github.com/python-websockets/websockets
- Raspberry Pi utils: https://github.com/raspberrypi/utils

## Copyleft boundary

The project does **not** copy or link GPL source code into the SBC5 Control Center application source. `dtc`, GNU coreutils and util-linux utilities are invoked as separate command-line programs/processes. Their inclusion in the distributed container does not change the license of the project's original source code; however, distribution of the container must still satisfy each third-party component's redistribution obligations.

In particular, publication of a binary container containing GPL components must preserve the applicable notices and provide the required access to corresponding source in a GPL-compliant manner. The release process should therefore publish or otherwise provide durable, version-matched source availability for the GPL packages used in each released image.

## Home Assistant bridge

The HACS bridge declares `requirements: []`. It imports Home Assistant and `voluptuous` from the Home Assistant runtime; those libraries are **not vendored** into the bridge repository.

## CI-only dependencies

GitHub Actions such as `actions/checkout`, Home Assistant Builder, HACS Action and Hassfest execute in CI and are not copied into the distributed project source or bridge package. Their own licenses remain applicable to those upstream projects.

## Trademarks and branding

Raspberry Pi is a trademark of Raspberry Pi Ltd. SBC5 Control Center uses “for Raspberry Pi 5” only as a compatibility statement and does not reproduce the official Raspberry Pi raspberry logo as part of the project brand. See `TRADEMARKS.md`.

This notice is a technical open-source compliance inventory, not legal advice.
