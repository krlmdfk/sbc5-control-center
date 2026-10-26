FROM ghcr.io/home-assistant/base:3.24

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache jq curl dtc coreutils util-linux unzip python3 py3-websockets raspberrypi-utils-vcgencmd

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

COPY run.sh /
COPY release.json /
COPY config_txt_catalog.json /config_txt_catalog.json
COPY logo.png /logo.png
COPY rpi5-stable50-10step-overlay.dts /
COPY rpi5-stable50-15step-overlay.dts /
COPY bridge /bridge
COPY config_ui.py /config_ui.py
COPY ai_cooling.py /ai_cooling.py
COPY dashboard_sync.py /dashboard_sync.py
COPY dashboard_card.json /dashboard_card.json
COPY update_status_card.json /update_status_card.json
COPY config_ui /config_ui
COPY legacy_bridge /legacy_bridge
COPY bridge-package.yaml /bridge-package.yaml
COPY migration_assets /migration_assets
COPY namespace_native_guard.sh /namespace_native_guard.sh
COPY migration_manager.py /migration_manager.py

RUN mkdir -p /usr/share/licenses/sbc5-control-center
COPY LICENSE /usr/share/licenses/sbc5-control-center/LICENSE
COPY NOTICE /usr/share/licenses/sbc5-control-center/NOTICE
COPY THIRD_PARTY_NOTICES.md /usr/share/licenses/sbc5-control-center/THIRD_PARTY_NOTICES.md
COPY TRADEMARKS.md /usr/share/licenses/sbc5-control-center/TRADEMARKS.md
COPY LEGAL.md /usr/share/licenses/sbc5-control-center/LEGAL.md
COPY LICENSE_AUDIT.md /usr/share/licenses/sbc5-control-center/LICENSE_AUDIT.md

RUN chmod a+x /run.sh /config_ui.py /ai_cooling.py /dashboard_sync.py /namespace_native_guard.sh /migration_manager.py

ENTRYPOINT ["/run.sh"]
CMD []
