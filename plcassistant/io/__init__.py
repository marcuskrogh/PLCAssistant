"""Soft-PLC scan-cycle I/O image, quality, bindings, thin-integration stub, MQTT bridge.

See docs/io/ and docs/packaging/. No Home Assistant dependency in this package.
"""

from plcassistant.io.binding import Binding, BindingTable, Direction, TagDecl
from plcassistant.io.image import IoImage, TagSnapshot
from plcassistant.io.integration import (
    EntitySample,
    MockEntityStore,
    ThinIntegrationStub,
)
from plcassistant.io.mqtt_bridge import InMemoryMqttBus, MqttIoBridge
from plcassistant.io.mqtt_entity_bridge import (
    MqttEntityBridge,
    default_wedge_binding_config,
)
from plcassistant.io.mqtt_topics import (
    DEFAULT_INSTANCE_ID,
    MQTT_QOS,
    TOPIC_ROOT,
    MqttTagPayload,
    cmd_topic,
    parse_tag_topic,
    status_topic,
    tag_in_topic,
    tag_out_topic,
)
from plcassistant.io.quality import (
    QualityStatus,
    ReasonCode,
    TagQuality,
    collapse_quality,
    is_good,
)

__all__ = [
    "Binding",
    "BindingTable",
    "DEFAULT_INSTANCE_ID",
    "Direction",
    "EntitySample",
    "InMemoryMqttBus",
    "IoImage",
    "MQTT_QOS",
    "MqttEntityBridge",
    "MqttIoBridge",
    "MqttTagPayload",
    "MockEntityStore",
    "TOPIC_ROOT",
    "TagDecl",
    "TagSnapshot",
    "ThinIntegrationStub",
    "QualityStatus",
    "ReasonCode",
    "TagQuality",
    "cmd_topic",
    "collapse_quality",
    "default_wedge_binding_config",
    "is_good",
    "parse_tag_topic",
    "status_topic",
    "tag_in_topic",
    "tag_out_topic",
]
