# Acceptance criteria (SWD-84 / SWD-124)

Automated tests live under `tests/` and must pass without a live Home Assistant or Mosquitto instance. Human checklist items below are verified on a real HA OS install before ship.

## Automated (CI)

| ID | Criterion | How verified |
|----|-----------|--------------|
| A1 | MQTT topic helpers build and parse the locked path shape | `tests/test_mqtt_topics.py` |
| A2 | Bridge publishes OUT and receives IN via injectable bus | `tests/test_mqtt_bridge.py` |
| A3 | Packaged App layout contains required files and Ingress/port config | `tests/test_ha_app_scaffold.py` (root `plc_assistant/`) |
| A4 | Bundled thin integration layout contains required files and MQTT config keys | `tests/test_bundled_integration.py` |
| A5 | Repository metadata for custom GitHub App install exists at repo root | `tests/test_github_app_repo.py` |
| A6 | Existing soft-PLC + surface regression suite still green | full `pytest` |
| A7 | App + integration MQTT adapters round-trip over in-memory bus | `tests/test_mqtt_entity_bridge.py`, `tests/test_swd84_acceptance.py` |

## Human (HA OS)

| ID | Criterion |
|----|-----------|
| H1 | Custom App installs from the GitHub repository URL |
| H2 | App starts; Ingress opens the programming surface |
| H3 | Exposed port reaches the same editor when Ingress is unavailable |
| H4 | With Mosquitto installed and configured, a bound tag updates an HA entity via the thin integration |
| H5 | Mock path still works when MQTT/bindings are not configured |
| H6 | Program-of-record survives App restart (persistent `/data`) |

## Out of scope for this acceptance set

- Official store submission
- HA Container install path
- Supervisor / REST entity bridges
- Live Mosquitto in CI
