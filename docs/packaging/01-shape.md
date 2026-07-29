# 01 — Packaging shape (locked)

**Tracker:** [SWD-122](https://marcusknielsen.atlassian.net/browse/SWD-122) · Parent [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)  
**Plan:** [`docs/PLAN.md`](../PLAN.md) · Research: [`docs/RESEARCH.md`](../RESEARCH.md)

## Locked shape

```
┌──────────────────────────────────────────────────────┐
│              Home Assistant OS                       │
│  Lovelace · Recorder · Apps panel                    │
│                                                      │
│  ┌────────────────────┐   ┌───────────────────────┐  │
│  │ Mosquitto (App)    │   │ Thin integration      │  │
│  │ MQTT broker        │◄──│ (bundled with our App)│  │
│  └─────────▲──────────┘   │ · bindings / units    │  │
│            │              │ · mock entities       │  │
│            │ MQTT         │ · start/stop/reset    │  │
│  ┌─────────┴──────────┐   └───────────────────────┘  │
│  │ PLCAssistant App   │                              │
│  │ · Soft-PLC scan    │                              │
│  │ · live IoImage     │                              │
│  │ · block editor     │  Ingress + optional port     │
│  │ · program data vol │                              │
│  └────────────────────┘                              │
└──────────────────────────────────────────────────────┘
```

| Concern | HA App (PLCAssistant) | Thin integration (bundled) | Mosquitto |
|---------|----------------------|----------------------------|-----------|
| Scan / control / safety | **Owns** | No | No |
| Live I/O image (SoT) | **Owns** | Feeds/sinks via MQTT | Transport |
| Bindings / units / mock entities | Consumes MQTT samples | **Owns** | No |
| Stand-alone process simulator | No (mock-unaware) | **Owns** (SWD-146 skid preset) | Transport |
| Operator services | Implements on tags | Exposes HA services | No |
| Program-of-record | **App persistent data** | No | No |
| Block editor UI | Ingress + exposed port | No | No |

**Invariant:** mock path ≡ field path. The Soft-PLC does not branch on “mock mode.”

**Ownership (SWD-145/146):** The thin integration owns the stand-alone process simulator (`custom_components/plcassistant/dynamics/`). Soft-PLC treats plant PVs (`LT_TANK`, `LT_RES`, `FT_INLET`, …) as MQTT **IN** like field signals and stays on `HeldProcess`. The integration observes Soft-PLC MQTT status (`scan_period_s`, state), consumes `CMD_SPEED` OUT, and publishes plant IN for the default **skid** preset. Soft-PLC receives no mock/plant identity back. Preset chooser / unit-op authoring → SWD-143/144.

## Install target (v1)

- **In:** Home Assistant **OS** (Supervisor Apps)
- **Out:** HA Container / Core / Supervised as first-class targets

## Publication (v1)

- **Custom App from GitHub** — add the App repository URL under Settings → Apps
- **Not** the official Home Assistant Apps store (yet)

## Naming

Home Assistant renamed **add-ons → Apps**. This repo uses **App** in packaging docs. Historical wedge text may still say “Add-on”; treat those as synonyms pointing at the same Supervisor container role. The frozen contract is this document.

## Bundle mechanism (v1+)

The App maps `homeassistant_config` (rw) and, on start, syncs the bundled
`custom_components/plcassistant/` into Home Assistant’s
`/config/custom_components/plcassistant`. Core still needs **one restart**
after first install or integration updates so it loads the files; then add
the integration under **Devices & services**. See root [`README.md`](../../README.md).

## Related

- MQTT map: [`02-mqtt-topics.md`](02-mqtt-topics.md)
- Acceptance: [`03-acceptance.md`](03-acceptance.md)
- Updates: [`04-updates.md`](04-updates.md)
- Prior sketch (superseded for freeze): [`../wedge/08-packaging-sketch.md`](../wedge/08-packaging-sketch.md)
- I/O stub (non-HA CI): [`../io/03-thin-integration-stub.md`](../io/03-thin-integration-stub.md)
- App tree: `plc_assistant/` (HA Apps folder; slug `plcassistant`) · Integration: `custom_components/plcassistant/` · Install pointer: `ha_app/INSTALL.md`
