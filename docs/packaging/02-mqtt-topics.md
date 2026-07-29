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

**Direction (SWD-145):** plant PVs (`LT_TANK`, `LT_RES`, `FT_INLET`) are Soft-PLC **IN** (`…/tag/{tag}/in`); Soft-PLC CVs/status (`CMD_SPEED`, `SP_LEVEL`, `SP_FLOW`, `MODE`, `PERM_OK`, `TRIP_ACTIVE`) are **OUT** (`…/tag/{tag}/out`). Process ↔ Soft-PLC transport is MQTT (mock ≡ field).

### App status topic (SWD-135 / SWD-136 / SWD-145)

JSON object, QoS **1**, **retain true**:

```json
{"state": "stopped", "mode": "STOP", "scan_period_s": 0.1}
```

| Field | Notes |
|-------|-------|
| `state` | `running` / `stopped` / `fault` / `offline` (legacy `reset` → treat as `stopped`) |
| `scan_period_s` | Soft-PLC scan period in seconds (numeric). Integration may observe; Soft-PLC gets no mock identity back. |
| extras | Optional (e.g. `mode`, `error`) — informational for the HMI chip |

Soft-PLC republishes retained status on mode changes and on a ~2 s heartbeat so late HA listeners recover. Live App MQTT clients register a last-will of `{"state":"offline","scan_period_s":0.1}` (retain) on this topic so disconnect surfaces as offline while still exposing the scan period for observe.

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

QoS: **1** (at least once). Retain: **false** for most scan tags (image is refreshed each scan). Retain **true** on `status` (boot + heartbeat + LWT). Retain **true** on HMI state OUT tags `MODE`, `PERM_OK`, and `TRIP_ACTIVE` so the thin integration hydrates after subscribe (SWD-137).

## Code

- Topic helpers + payload codec: `plcassistant.io.mqtt_topics`
- App bridge: `plcassistant.io.mqtt_bridge.MqttIoBridge`
- In-memory transport for tests: `plcassistant.io.mqtt_bridge.InMemoryMqttBus`

## Non-HA CI

Unit tests use `InMemoryMqttBus` — **no live Mosquitto** required in pytest.
