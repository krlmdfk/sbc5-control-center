#!/bin/bash
set -u

# SBC5 Control Center 3.0.0 native runtime bootstrap.
# These constants are intentionally retained in the package entrypoint because the
# SBC5 package validator verifies them before accepting local/update packages.
APP_VERSION="3.0.0"
REQUIRED_PACKAGE_VERSION="3.0.0"

# The Rust core owns lightweight host telemetry and health state. The proven 2.8.x
# control plane remains the compatibility layer during the stable 3.0 migration.
RUST_CORE="/usr/local/bin/sbc5-core"
RUST_STATUS="/data/rust_core_status.json"
RUST_MIRROR="/homeassistant/sbc5_control_center/rust_core_status.json"

mkdir -p /tmp /data /homeassistant/sbc5_control_center 2>/dev/null || true

if [ -x "$RUST_CORE" ] && "$RUST_CORE" self-test >/tmp/sbc5_rust_core_self_test.json 2>/tmp/sbc5_rust_core_self_test.err; then
  "$RUST_CORE" daemon --status "$RUST_STATUS" --mirror "$RUST_MIRROR" --interval 2 >/tmp/sbc5_rust_core.log 2>&1 &
  export SBC5_RUST_CORE_ENABLED=true
  export SBC5_RUST_CORE_VERSION="$APP_VERSION"
  echo "[SBC5 ${APP_VERSION}] Rust Core: enabled (native telemetry/runtime health)."
else
  export SBC5_RUST_CORE_ENABLED=false
  echo "[SBC5 ${APP_VERSION}] Rust Core: self-test failed; starting compatibility control plane."
  [ -s /tmp/sbc5_rust_core_self_test.err ] && cat /tmp/sbc5_rust_core_self_test.err || true
fi

# Stable migration rule: fan safety/control remains authoritative in the proven
# compatibility control plane until native controller parity tests are complete.
exec /run_legacy.sh "$@"
