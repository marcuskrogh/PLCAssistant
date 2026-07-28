# 02 — MQTT topics & payloads

**Tracker:** [SWD-122](https://marcusknielsen.atlassian.net/browse/SWD-122) / [SWD-125](https://marcusknielsen.atlassian.net/browse/SWD-125)  
**Parent:** [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)

## Broker

Users **must install the Mosquitto App** (or another MQTT broker App) on HA OS. PLCAssistant does **not** embed a broker.

Default broker (Supervisor DNS): `core-mosquitto` (official Mosquitto App hostname). Configurable via App options / integration config.

## Instance prefix

All topics are under:

```text
plcassistant/{instance_id}/…
```

Default `instance_id` = `default`.

## Topic map

| Direction | Topic | Publisher | Subscriber |
|-----------|-------|-----------|------------|
| Entity → Soft-PLC (scan IN) | `plcassistant/{id}/tag/{tag}/in` | Thin integration | App (`MqttIoBridge`) |
| Soft-PLC → Entity (scan OUT) | `plcassistant/{id}/tag/{tag}/out` | App | Thin integration |
| Operator pulse (optional) | `plcassistant/{id}/cmd/{name}` | Thin integration | App |
| App status (optional) | `plcassistant/{id}/status` | App | Integration / diagnostics |

Tag names match the Soft-PLC image / binding table (e.g. `LT_TANK`, `CMD_SPEED`, `SP_LEVEL_REQ`).

## Payload (JSON)

```json
{
  "value": 0.15,
  "status": "GOOD",
  "reason": null,
  "ts": 1710000000.0
}
```

| Field | Type | Notes |
|-------|------|-------|
| `value` | number / bool / string / null | Engineering units on the wire (units applied in integration bindings) |
| `status` | string | `GOOD`, `BAD`, `UNCERTAIN` (matches `QualityStatus` names) |
| `reason` | string / null | `ReasonCode` name when not GOOD (e.g. `unavailable`, `fault`) |
| `ts` | number / null | Optional Unix time (seconds); informational |

QoS: **1** (at least once). Retain: **false** for scan tags (image is refreshed each scan). Optional retain on `status`.

## Code

- Topic helpers + payload codec: `plcassistant.io.mqtt_topics`
- App bridge: `plcassistant.io.mqtt_bridge.MqttIoBridge`
- In-memory transport for tests: `plcassistant.io.mqtt_bridge.InMemoryMqttBus`

## Non-HA CI

Unit tests use `InMemoryMqttBus` — **no live Mosquitto** required in pytest.
