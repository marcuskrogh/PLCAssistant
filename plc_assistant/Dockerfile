ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

# Install from the App build context (synced package + pyproject.toml).
# Avoids needing git / a second GitHub clone during docker build.
WORKDIR /usr/src/plcassistant
COPY pyproject.toml README.md ./
COPY plcassistant ./plcassistant
RUN pip3 install --no-cache-dir . "paho-mqtt>=1.6"

COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /
CMD ["/run.sh"]
