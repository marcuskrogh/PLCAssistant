# Research: Packaging shape (SWD-84)

**Tracker:** [SWD-84](https://marcusknielsen.atlassian.net/browse/SWD-84)  
**Parent:** [SWD-81](https://marcusknielsen.atlassian.net/browse/SWD-81) · Roadmap theme 5  
**Date:** 2026-07-27  
**Tooling:** `scripts/arxiv_research.py` + WebSearch / WebFetch

## Question

What do external sources say about **packaging / deployment shape** for a lab / hobby soft-PLC that uses Home Assistant as I/O and HMI — especially:

1. What packaging options exist in the **HA ecosystem** (integrations, Apps/add-ons, containers beside HA, external host)
2. Which **constraints** (lifecycle, isolation, UX, updates, install-method availability) change which shapes are viable
3. How peer soft-PLC / industrial edge practice packages a **cyclic runtime** relative to an I/O / HMI platform

Scope: inform `/define SWD-84` with evidence. This brief does **not** choose a packaging shape. In-repo preliminary sketch (`docs/wedge/08-packaging-sketch.md`) is background, not a research conclusion.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered | Soft-PLC / IEC 61499 / Docker+industrial hits are sparse for HA-specific packaging; best hits are distributed IEC 61499, security/availability, low-code factory automation |
| Formal written | covered | HA developer docs (integrations, Apps), HA installation/deprecation blog; IEEE INDIN OpenPLC container study (via DOI); CODESYS Virtual Control product sheet |
| Web discovery | covered | HA Apps rename + install-method FAQ; OpenPLC Runtime architecture; CODESYS Virtual Control; Avassa softPLC containerization overview |
| Informal / practitioner | covered | HA community (add-on vs integration, MQTT vs companion integration); AppDaemon vs pyscript packaging; honeytreelabs soft-PLC beside MQTT/HA |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | `soft PLC` / OpenPLC / CODESYS / vPLC + architecture/deployment; IEC 61499 + container/edge; Home Assistant + packaging (mostly smart-home noise). Lookup: `2101.01856`, `1705.05367`, `2204.13499`, `2504.04224`. |
| Formal | [developers.home-assistant.io integration architecture](https://developers.home-assistant.io/docs/architecture_components/); [Apps (formerly add-ons)](https://developers.home-assistant.io/docs/apps/); [App communication](https://developers.home-assistant.io/docs/apps/communication/); [HA install methods FAQ](https://www.home-assistant.io/faq/ha-vs-hassio); [2025.5 Core/Supervised deprecation](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/); OpenPLC INDIN 2025 DOI `10.1109/indin64977.2025.11279472`; CODESYS Virtual Control SL datasheet |
| Web | SoftPLC containerization surveys; OpenPLC Runtime ARCHITECTURE.md; CODESYS Virtual Control product pages; HA Apps user docs |
| Informal | HA forum threads on add-on vs integration / MQTT vs registered integration; AppDaemon add-on docs; honeytreelabs architecture posts |

Raw JSON under `/tmp/swd84-research/` (not committed).

## Executive summary (what the sources say)

Sources converge on a **structural split**, not on a single packaging winner:

1. **Inside HA Core (integration / custom component)** is the path for entity state, config flows, services, and UI binding — Python modules in the Core event loop ([integration architecture](https://developers.home-assistant.io/docs/architecture_components/)). Long-running deterministic scan loops are a poor fit for that process model (practitioner consensus: AppDaemon-as-add-on vs pyscript-in-Core).
2. **Beside HA as a containerized App (formerly add-on)** is the supported Supervisor path for standalone services. Apps are OCI images managed by Supervisor; available on **Home Assistant OS** (and historically Supervised). They are **not** available on Home Assistant Container ([Apps docs](https://www.home-assistant.io/apps/), [FAQ](https://www.home-assistant.io/faq/ha-vs-hassio)).
3. **Beside HA as a plain Docker/compose service** is the Container-install escape hatch: same container image pattern as an App, without Supervisor store/lifecycle ([deprecation blog migration table](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/)).
4. **External / SBC soft-PLC** (native Linux or container, MQTT/Modbus I/O) is how hobby soft-PLCs often sit next to HA without living in HA at all ([honeytreelabs](https://honeytreelabs.com/posts/smart-home-architecture-and-impl/), OpenPLC Runtime).

Industrial soft-PLC practice is moving toward **containerized runtimes** (CODESYS Virtual Control SL; OpenPLC Runtime Docker; Avassa edge narrative) with separate authoring tools and I/O plugins — reinforcing “runtime container + I/O bridge,” not “all logic inside the HMI platform.”

HA install-method consolidation (OS + Container only; Core/Supervised deprecated) **raises the stakes** of App-only packaging: choosing Apps-only excludes Container users unless a twin Docker story exists.

Communication between App and Core is a first-class design axis: Supervisor proxy + `SUPERVISOR_TOKEN`, MQTT service discovery, or a **companion integration** that talks HTTP to the App ([App communication](https://developers.home-assistant.io/docs/apps/communication/); community MQTT-vs-integration thread).

## Key sources

| Title | Axis | ID/URL | Relevance |
|-------|------|--------|-----------|
| Developing an app (formerly add-on) | Formal / Web | https://developers.home-assistant.io/docs/apps/ | Apps = container images; Supervisor-managed |
| App communication | Formal | https://developers.home-assistant.io/docs/apps/communication/ | Core API proxy, Supervisor API, MQTT services |
| Integration architecture | Formal | https://developers.home-assistant.io/docs/architecture_components/ | Integrations live in Core; domains/entities/actions |
| HA OS vs Container FAQ | Formal | https://www.home-assistant.io/faq/ha-vs-hassio | Apps only on OS; Container has no Apps |
| Deprecating Core and Supervised (2025.5) | Formal | https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/ | Supported paths shrink to OS + Container |
| OpenPLC Runtime Architecture | Web / Informal | https://github.com/Autonomy-Logic/openplc-runtime/blob/main/docs/ARCHITECTURE.md | Dual-process soft-PLC; native + Docker |
| OpenPLC container benchmarking (INDIN 2025) | Formal | DOI 10.1109/indin64977.2025.11279472 | Native vs Docker vs K8s trade-offs |
| CODESYS Virtual Control SL | Formal / Web | https://us.codesys.com/products/runtime/virtual-control-sl/ | Containerized industrial softPLC product form |
| Sollfrank et al. Docker for time-sensitive industrial apps | Formal (cited) | DOI 10.1109/tii.2020.3022843 | Container overhead for time-sensitive control |
| Designing actively secure IACS apps | Preprint | arXiv:2101.01856 | IEC 61499 packaging of security at application layer |
| Evaluating XMPP in IEC 61499 | Preprint | arXiv:1705.05367 | Distributed FB apps need explicit protocol SIFBs |
| HA forum: integrations vs add-ons | Informal | https://community.home-assistant.io/t/integrations-add-ons-and-custom-integrations/710483 | Add-ons = services; integrations = clients |
| HA forum: MQTT vs registered integration | Informal | https://community.home-assistant.io/t/communicating-from-addon-to-home-assistant-mqtt-vs-registered-integration/997238 | Bridge patterns and trade-offs |
| AppDaemon add-on docs | Informal | https://appdaemon.readthedocs.io/en/latest/ADDON.html | Long-running Python as App + Supervisor token |
| honeytreelabs soft-PLC architecture | Informal | https://honeytreelabs.com/posts/smart-home-architecture-and-impl/ | Cyclic PLC beside MQTT/HA, not inside HA |

## Themes and trends

### T1 — Integration ≠ App (service vs client)

Across HA docs and forums: **integrations** extend Core (entities, actions, config); **Apps** (add-ons) are separate containers for long-running software. Patterns that need both (Mosquitto App + MQTT integration; NUT; Z-Wave) are common. A soft-PLC that owns a scan loop maps naturally to the **App/container** side; entity↔tag bindings map to the **integration** side — matching the in-repo preliminary sketch, but as *evidence of ecosystem pattern*, not a lock.

### T2 — Install method gates App availability

Official support converges on **HA OS** (Supervisor + Apps) and **HA Container** (no Apps). Deprecating Supervised/Core ([2025.5 blog](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/)) means an Apps-only Soft-PLC **does not cover Container users** unless the same image is documented for manual Docker. Migration guidance explicitly says Container users can run former add-ons as sidecar containers.

### T3 — Soft-PLC peers package as containers beside I/O

OpenPLC Runtime: dual process (API server + real-time scan), Docker with `SYS_NICE`/`SYS_RESOURCE`, persistent volume ([ARCHITECTURE.md](https://github.com/Autonomy-Logic/openplc-runtime/blob/main/docs/ARCHITECTURE.md)). CODESYS Virtual Control SL: SoftPLC as Docker/Podman image on Linux edge. INDIN 2025 OpenPLC study: native lowest latency; Docker balanced; Kubernetes stronger on recovery/throughput. Containerization is mainstream for softPLC **deployment**, with RT caveats.

### T4 — Bridge choice is a packaging decision

App↔HA options from docs/community:

| Bridge | Pros (sources) | Cons (sources) |
|--------|----------------|----------------|
| Supervisor Core API proxy | Built-in token; no broker | Requires App + Supervisor; App-only installs |
| MQTT | Works without Supervisor; portable to Container/external host | Extra broker; less native config flow |
| Companion integration → App HTTP | Native Devices & services UX | Needs integration install; App must be reachable |

Choosing “thin integration + App” implies committing to **at least one** of these bridges for production HA IPC (in-repo stub today is in-process only).

### T5 — In-Core Python is for event logic, not scan engines

AppDaemon (App/container, separate process) vs pyscript (custom integration, in-loop interpreter) debates show practitioners put **heavy / long-running / library-rich** Python **outside** Core. That aligns with keeping Soft-PLC scan + program editor out of `custom_components`.

### T6 — Academic axis is thin on HA packaging

arXiv hits for “Home Assistant + packaging” are mostly smart-home UX/security, not deployment topology. Useful scholarly signal is **IEC 61499 distribution / security** and **containerized industrial control**, not HA-specific packaging theory. Gap: little peer-reviewed work on soft-PLC-as-HA-App specifically.

## Gaps and limitations

- No single normative standard for “soft-PLC packaging beside home automation.”
- OpenPLC INDIN paper accessed via DOI/abstract synthesis from search — full PDF not deep-read in this pass.
- HA developer “Apps” rename is recent (2026 docs); older “add-on” literature still dominates forums.
- Real-time claims for containers (CODESYS, OpenPLC) depend on host RT kernel / privileges — not validated here.
- In-repo preliminary sketch and SWD-82 “App hosts editor” naming are **prior project artifacts**, not external evidence.

## Recommended reading order

1. [HA Apps intro](https://developers.home-assistant.io/docs/apps/) + [App communication](https://developers.home-assistant.io/docs/apps/communication/)
2. [Integration architecture](https://developers.home-assistant.io/docs/architecture_components/) + [OS vs Container FAQ](https://www.home-assistant.io/faq/ha-vs-hassio)
3. [2025.5 install-method deprecation](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/)
4. OpenPLC [ARCHITECTURE.md](https://github.com/Autonomy-Logic/openplc-runtime/blob/main/docs/ARCHITECTURE.md) (peer soft-PLC packaging)
5. Community: [MQTT vs companion integration](https://community.home-assistant.io/t/communicating-from-addon-to-home-assistant-mqtt-vs-registered-integration/997238)
6. CODESYS Virtual Control overview (industrial container softPLC form)

## Particulars left open for `/define`

Research does **not** decide:

- Primary packaging: Apps-only vs Apps+Docker twin vs external host vs integration-heavy
- Whether Container-install users are in-scope for v1
- Bridge: Supervisor API vs MQTT vs companion integration (or hybrid)
- Where program-of-record files live (App data, HA config share, git)
- How far to pursue RT privileges in container vs demo-grade Python scan
- Rename/docs cleanup of Add-on → App across historical wedge docs

## Role in pipeline

Supportive context for `/define SWD-84`. Does **not** settle user alignment. Preliminary sketch in `docs/wedge/08-packaging-sketch.md` remains a working hypothesis to probe, not a research verdict.

## Sources

### Preprints (arXiv)

- Tanveer et al., “Designing Actively Secure, Highly Available Industrial Automation Applications,” arXiv:2101.01856 (DOI 10.1109/INDIN41052.2019.8972262).
- Veichtlbauer et al., “Evaluating XMPP Communication in IEC 61499-based Distributed Energy Applications,” arXiv:1705.05367 (DOI 10.1109/ETFA.2016.7733744).
- FieldFuzz authors, “FieldFuzz: In Situ Blackbox Fuzzing of Proprietary Industrial Automation Runtimes via the Network,” arXiv:2204.13499.
- Siemens/Berkeley report, “Exploration of Approaches for Robustness and Safety in a Low Code Open Environment for Factory Automation,” arXiv:2504.04224.

### Formal written

- Home Assistant Developer Docs — Integration architecture: https://developers.home-assistant.io/docs/architecture_components/
- Home Assistant Developer Docs — Developing an app: https://developers.home-assistant.io/docs/apps/
- Home Assistant Developer Docs — App communication: https://developers.home-assistant.io/docs/apps/communication/
- Home Assistant Developer Docs — App configuration: https://developers.home-assistant.io/docs/apps/configuration/
- Home Assistant — OS vs Container FAQ: https://www.home-assistant.io/faq/ha-vs-hassio
- Home Assistant Blog — Deprecating Core and Supervised (2025-05-22): https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/
- Home Assistant Supervisor overview: https://developers.home-assistant.io/docs/supervisor/
- OpenPLC container benchmarking, IEEE INDIN 2025, DOI 10.1109/indin64977.2025.11279472
- Sollfrank et al., “Evaluating Docker for Lightweight Virtualization…,” IEEE TII 2020, DOI 10.1109/tii.2020.3022843 (cited by INDIN study)
- CODESYS Virtual Control SL product sheet / store pages

### Web discovery

- Home Assistant Apps (user): https://www.home-assistant.io/apps/
- OpenPLC Runtime ARCHITECTURE.md: https://github.com/Autonomy-Logic/openplc-runtime/blob/main/docs/ARCHITECTURE.md
- CODESYS Virtual Control SL: https://us.codesys.com/products/runtime/virtual-control-sl/
- Avassa — “Why Containerized softPLCs Will Transform the Industrial Edge”: https://avassa.io/articles/softplc-containerization-industrial-edge-automation/
- Developer blog — Migrating app builds to Docker BuildKit (2026-04-02): https://developers.home-assistant.io/blog/2026/04/02/builder-migration/

### Informal / practitioner

- HA Community — Integrations, add-ons, custom integrations: https://community.home-assistant.io/t/integrations-add-ons-and-custom-integrations/710483
- HA Community — MQTT vs registered integration from addon: https://community.home-assistant.io/t/communicating-from-addon-to-home-assistant-mqtt-vs-registered-integration/997238
- AppDaemon ADDON docs: https://appdaemon.readthedocs.io/en/latest/ADDON.html
- honeytreelabs — Architecture and Implementation of my Smart Home PLC: https://honeytreelabs.com/posts/smart-home-architecture-and-impl/
- honeytreelabs/homeautomation-plc: https://github.com/honeytreelabs/homeautomation-plc
- CODESYS Forge blog — Adventures with CODESYS Virtual Control (homelab containers)

## Tracker

- Task: SWD-84
- Artifact: `docs/RESEARCH.md`
- Prior sketch (not research): `docs/wedge/08-packaging-sketch.md`

## Next

`/define SWD-84` — Define packaging with the user; this brief is supportive context only
