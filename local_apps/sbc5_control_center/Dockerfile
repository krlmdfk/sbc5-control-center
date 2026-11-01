FROM rust:1.85-alpine3.21 AS rust-builder
WORKDIR /build
COPY rust-core/Cargo.toml ./Cargo.toml
COPY rust-core/src ./src
RUN cargo build --release

FROM ghcr.io/home-assistant/base:3.24

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache jq curl dtc coreutils util-linux unzip python3 py3-websockets raspberrypi-utils-vcgencmd
RUN install -d -m 1777 /tmp

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}" \
  io.sbc5.runtime="rust-hybrid" \
  io.sbc5.rust-core="${BUILD_VERSION}"

COPY --from=rust-builder /build/target/release/sbc5-core /usr/local/bin/sbc5-core
COPY run.sh /
COPY run_legacy.sh /
COPY ethernet_guard.py /ethernet_guard.py
COPY release.json /
COPY config_txt_catalog.json /config_txt_catalog.json
COPY logo.png /logo.png
COPY rpi5-stable50-10step-overlay.dts /
COPY rpi5-stable50-15step-overlay.dts /
COPY bridge /bridge
COPY config_ui.py /config_ui.py
# 3.1.29 thermal stability: normal Adaptive PWM control uses a conditioned
# temperature signal; raw CPU temperature remains authoritative for safety.
COPY thermal_control_filter.py /thermal_control_filter.py
COPY patch_thermal_stability_3_1_29.py /patch_thermal_stability_3_1_29.py
# 3.1.31 Adaptive Trim Recovery: fused 30/120 s trend plus trend-aware
# anti-windup and faster near-target trim release. AI/TP authority is unchanged.
COPY patch_adaptive_trim_3_1_31.py /patch_adaptive_trim_3_1_31.py
# 3.1.28 AI stack: every module imported by the public v5.2 runtime must be
# present in the container image. Keep each layer on a distinct runtime path.
COPY ai_cooling_legacy.py /ai_cooling_legacy.py
COPY thermal_predictor_v3.py /thermal_predictor_v3.py
COPY thermal_active_policy.py /thermal_active_policy.py
COPY thermal_effectiveness.py /thermal_effectiveness.py
COPY ai_cooling.py /ai_cooling_v4.py
COPY ai_cooling_v5.py /ai_cooling_v5.py
COPY ai_cooling_v5_1.py /ai_cooling_v5_1.py
COPY ai_cooling_v5_2.py /ai_cooling_v5_2.py
COPY ai_cooling_v5_2.py /ai_cooling.py
COPY dashboard_sync.py /dashboard_sync.py
COPY dashboard_card.json /dashboard_card.json
COPY update_status_card.json /update_status_card.json
COPY config_ui /config_ui
COPY legacy_bridge /legacy_bridge
COPY bridge-package.yaml /bridge-package.yaml
COPY migration_assets /migration_assets
COPY namespace_native_guard.sh /namespace_native_guard.sh
COPY migration_manager.py /migration_manager.py
COPY migration_manager_v2.py /migration_manager_v2.py

# The compatibility control plane still contains internal version constants.
# Align them at image-build time with the Supervisor App version, then apply the
# audited thermal-control patches to the image copy only.
RUN sed -i \
  -e "s/^APP_VERSION=\"[^\"]*\"$/APP_VERSION=\"${BUILD_VERSION}\"/" \
  -e "s/^REQUIRED_PACKAGE_VERSION=\"[^\"]*\"$/REQUIRED_PACKAGE_VERSION=\"${BUILD_VERSION}\"/" \
  /run_legacy.sh \
  && python3 /patch_thermal_stability_3_1_29.py /run_legacy.sh \
  && python3 /patch_adaptive_trim_3_1_31.py /run_legacy.sh \
  && rm -f /patch_thermal_stability_3_1_29.py /patch_adaptive_trim_3_1_31.py

RUN mkdir -p /usr/share/licenses/sbc5-control-center
COPY LICENSE /usr/share/licenses/sbc5-control-center/LICENSE
COPY NOTICE /usr/share/licenses/sbc5-control-center/NOTICE
COPY THIRD_PARTY_NOTICES.md /usr/share/licenses/sbc5-control-center/THIRD_PARTY_NOTICES.md
COPY TRADEMARKS.md /usr/share/licenses/sbc5-control-center/TRADEMARKS.md
COPY LEGAL.md /usr/share/licenses/sbc5-control-center/LEGAL.md
COPY LICENSE_AUDIT.md /usr/share/licenses/sbc5-control-center/LICENSE_AUDIT.md

RUN chmod a+x /run.sh /run_legacy.sh /ethernet_guard.py /usr/local/bin/sbc5-core /config_ui.py /thermal_control_filter.py /ai_cooling.py /ai_cooling_v4.py /ai_cooling_v5.py /ai_cooling_v5_1.py /ai_cooling_v5_2.py /ai_cooling_legacy.py /thermal_predictor_v3.py /thermal_active_policy.py /thermal_effectiveness.py /dashboard_sync.py /namespace_native_guard.sh /migration_manager.py /migration_manager_v2.py

ENTRYPOINT ["/run.sh"]
CMD []