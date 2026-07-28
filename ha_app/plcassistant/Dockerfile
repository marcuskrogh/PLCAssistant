ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

# Alpine base images do not ship git; pip needs it for git+ URLs.
ARG PLCASSISTANT_PIP_REF=git+https://github.com/marcuskrogh/PLCAssistant.git#egg=plcassistant
RUN apk add --no-cache --virtual .build-deps git \
    && pip3 install --no-cache-dir "${PLCASSISTANT_PIP_REF}" paho-mqtt \
    && apk del .build-deps

COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
