ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
# Supervisor passes BUILD_VERSION from config.yaml on every App build/update.
# Keep the default equal to plc_assistant/config.yaml version for local builds.
ARG BUILD_VERSION=0.1.39
ARG BUILD_ARCH=amd64
FROM ${BUILD_FROM}

# Re-declare so the values are available after FROM (Docker ARG scope).
ARG BUILD_VERSION
ARG BUILD_ARCH
# Changing BUILD_VERSION invalidates this layer and all following COPY/RUN layers,
# which defeats sticky containerd caches that otherwise keep stale App code.
RUN mkdir -p /usr/share/plcassistant \
    && printf '%s\n' "${BUILD_VERSION}" > /usr/share/plcassistant/APP_VERSION \
    && echo "Building PLCAssistant App ${BUILD_VERSION} (${BUILD_ARCH})"

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}" \
      io.hass.name="PLCAssistant"

# Install from the App build context (synced package + pyproject.toml).
# Avoids needing git / a second GitHub clone during docker build.
WORKDIR /usr/src/plcassistant
COPY pyproject.toml README.md ./
COPY plcassistant ./plcassistant
RUN pip3 install --no-cache-dir . "paho-mqtt>=1.6"

# Thin integration is auto-copied into HA /config on App start.
COPY custom_components /usr/share/plcassistant/custom_components
COPY migrate_legacy_mqtt_subscribe.py /usr/share/plcassistant/migrate_legacy_mqtt_subscribe.py

COPY run.sh /
RUN chmod a+x /run.sh /usr/share/plcassistant/migrate_legacy_mqtt_subscribe.py

WORKDIR /
CMD ["/run.sh"]
