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
| Operator services | Implements on tags | Exposes HA services | No |
| Program-of-record | **App persistent data** | No | No |
| Block editor UI | Ingress + exposed port | No | No |

**Invariant:** mock path ≡ field path. The Soft-PLC does not branch on “mock mode.”

## Install target (v1)

- **In:** Home Assistant **OS** (Supervisor Apps)
- **Out:** HA Container / Core / Supervised as first-class targets

## Publication (v1)

- **Custom App from GitHub** — add the App repository URL under Settings → Apps
- **Not** the official Home Assistant Apps store (yet)

## Naming

Home Assistant renamed **add-ons → Apps**. This repo uses **App** in packaging docs. Historical wedge text may still say “Add-on”; treat those as synonyms pointing at the same Supervisor container role. The frozen contract is this document.

## Bundle mechanism (v1)

**Documented one-time copy** of `custom_components/plcassistant/` into Home Assistant `config/custom_components/`. The App entrypoint does not auto-register the integration (avoids needing a writable Core config mount). See [`ha_app/INSTALL.md`](../../ha_app/INSTALL.md).

## Related

- MQTT map: [`02-mqtt-topics.md`](02-mqtt-topics.md)
- Acceptance: [`03-acceptance.md`](03-acceptance.md)
- Prior sketch (superseded for freeze): [`../wedge/08-packaging-sketch.md`](../wedge/08-packaging-sketch.md)
- I/O stub (non-HA CI): [`../io/03-thin-integration-stub.md`](../io/03-thin-integration-stub.md)
- App tree: `ha_app/` · Integration: `custom_components/plcassistant/`
