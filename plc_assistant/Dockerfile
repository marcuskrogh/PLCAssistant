ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
# Supervisor passes BUILD_VERSION from config.yaml on every App build/update.
ARG BUILD_VERSION=0.1.7
FROM ${BUILD_FROM}

# Re-declare so the value is available after FROM (Docker ARG scope).
ARG BUILD_VERSION
# Changing BUILD_VERSION invalidates this layer and all following COPY/RUN layers,
# which defeats sticky containerd caches that otherwise keep stale App code.
RUN mkdir -p /usr/share/plcassistant \
    && printf '%s\n' "${BUILD_VERSION}" > /usr/share/plcassistant/APP_VERSION \
    && echo "Building PLCAssistant App ${BUILD_VERSION}"

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="addon" \
      io.hass.name="PLCAssistant"

# Install from the App build context (synced package + pyproject.toml).
# Avoids needing git / a second GitHub clone during docker build.
WORKDIR /usr/src/plcassistant
COPY pyproject.toml README.md ./
COPY plcassistant ./plcassistant
RUN pip3 install --no-cache-dir . "paho-mqtt>=1.6"

# Thin integration is auto-copied into HA /config on App start.
COPY custom_components /usr/share/plcassistant/custom_components

COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /
CMD ["/run.sh"]
