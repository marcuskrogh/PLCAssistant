ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

# pip needs git for git+https installs; HA Supervisor build context is only
# this App folder, so the Python package is pulled from GitHub (not COPY'd).
ARG PLCASSISTANT_PIP_REF=git+https://github.com/marcuskrogh/PLCAssistant.git#egg=plcassistant
RUN apk add --no-cache --virtual .build-deps git \
    && pip3 install --no-cache-dir "${PLCASSISTANT_PIP_REF}" paho-mqtt \
    && apk del .build-deps

COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
