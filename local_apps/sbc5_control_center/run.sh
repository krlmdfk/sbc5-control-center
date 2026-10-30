#!/bin/bash
set -u

# SBC5 Control Center 3.1.23 native runtime bootstrap.
# These constants are intentionally retained in the package entrypoint because the
# SBC5 package validator verifies them before accepting local/update packages.
APP_VERSION="3.1.23"
REQUIRED_PACKAGE_VERSION="3.1.23"
export SBC5CC_APP_VERSION="$APP_VERSION"

# The Rust core owns lightweight host telemetry and health state. The proven 2.8.x
# control plane remains the compatibility layer during the stable 3.0 migration.
RUST_CORE="/usr/local/bin/sbc5-core"
RUST_STATUS="/data/rust_core_status.json"
RUST_MIRROR="/homeassistant/sbc5_control_center/rust_core_status.json"
ETHERNET_GUARD="/ethernet_guard.py"

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

# Ethernet Stability Guard is deliberately isolated from fan/thermal control. It is
# read-only by default (EEE=auto); config.txt is touched only after the user selects
# EEE=off in App Configuration. The guard also publishes lightweight end0 health.
if [ -x "$ETHERNET_GUARD" ]; then
  "$ETHERNET_GUARD" > >(tee -a /tmp/sbc5_ethernet_guard.log) 2>&1 &
  echo "[SBC5 ${APP_VERSION}] Ethernet Stability Guard: enabled (persistent EEE state + end0 health)."
else
  echo "[SBC5 ${APP_VERSION}] Ethernet Stability Guard: unavailable; continuing fail-open."
fi

# Stable migration rule: fan safety/control remains authoritative in the proven
# compatibility control plane until native controller parity tests are complete.
# The Local -> Store profile safety functions migration_profile_guard_active and
# migration_profile_guard_sync remain implemented and executed by run_legacy.sh.
exec /run_legacy.sh "$@"
