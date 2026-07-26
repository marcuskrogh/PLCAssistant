# Research brief: Soft-PLC architectures for IEC 61131-style control over entity/IoT I/O

## Question

For **PLCAssistant** (Task [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)), which architecture best matches “virtual PLC” behaviour when **Home Assistant entities** are the field I/O?

Candidate approaches from the roadmap:

1. **Soft-PLC sidecar** (OpenPLC-class runtime + HA entity I/O driver)
2. **In-HA soft runtime** (scan cycle inside Home Assistant / addon process)
3. **ST→automation transpile** (IEC language → event-driven HA automations)
4. **Hybrid** (scan-cycle runtime + HA as cyber/IoT fabric)

Secondary questions: how literature treats **cyclic scan vs event-driven** execution (IEC 61131 vs 61499), and what that implies for determinism and packaging.

## Search strategy

**Corpus:** arXiv Atom API via `scripts/arxiv_research.py` (primary host used: `https://arxiv.org/api/query`; `export.arxiv.org` returned persistent 503 during this run).

**Planned complementary queries:**

| # | Intent | Query |
|---|--------|-------|
| 1 | Broad IEC 61131 | `all:"IEC 61131"` |
| 2 | Soft/virtual PLC | `all:"soft PLC" OR all:"software PLC" OR all:"virtual PLC" OR all:softPLC` |
| 3 | OpenPLC / Modbus runtime | `all:OpenPLC OR (all:PLC AND all:Modbus AND all:runtime)` |
| 4 | PLC + IoT / CPS / SCADA (2018–2026) | `all:(PLC AND (IoT OR "home automation" OR "smart home" OR "cyber-physical" OR SCADA)) AND submittedDate:[201801010000 TO 202612312359]` |

**Executed successfully:** Query 1 — `total_results=42`, fetched 25 (`docs/research/arxiv_swd70_iec61131_search.json`).

**Blocked by arXiv rate limits (429/503) after the first successful page:** Queries 2–4 and follow-up `lookup`/`snowball` calls. Soft-PLC / OpenPLC coverage in this brief is therefore limited to papers that also matched the IEC 61131 query (notably OpenPLC appears in [2607.08550](https://arxiv.org/abs/2607.08550)).

**Coverage honesty:** arXiv is preprint-heavy; industrial automation also lives in IEEE/IFAC venues underrepresented here. No retrieved paper discusses Home Assistant specifically.

**Complement (this revision):** Home Assistant–specific offerings and packaging models were surveyed from official HA docs, HACS/community projects, and addon ecosystems (see [Home Assistant technology landscape](#home-assistant-technology-landscape)). That fills the HA gap the arXiv corpus could not.

## Executive summary

arXiv literature on PLC software strongly anchors on **IEC 61131-3** languages and an **abstract scan-cycle** execution model (inputs → logic → outputs). Formal semantics, verification, and code synthesis work all assume that cyclic PLC behaviour ([1009.0817](https://arxiv.org/abs/1009.0817), [1301.3047](https://arxiv.org/abs/1301.3047), [1912.10629](https://arxiv.org/abs/1912.10629), [2607.08550](https://arxiv.org/abs/2607.08550)).

The main **paradigm fork** in the literature is **IEC 61131 (cyclic / widely deployed)** vs **IEC 61499 (event-driven / academically promoted)**. Thramboulidis ([1303.4761](https://arxiv.org/abs/1303.4761)) argues that 61499’s claimed advantages (including event-driven execution) are oversold and that 61131 remains the industrial baseline—directly relevant to whether PLCAssistant should emulate a scan cycle or transpile to HA’s event automations.

A second theme is **PLCs as one layer in a cyber-physical / IoT system**, not the whole stack: SysML/UML + IoT as the glue for cyber interfaces ([1402.3920](https://arxiv.org/abs/1402.3920), [1407.2077](https://arxiv.org/abs/1407.2077)). That maps cleanly to “HA owns devices/entities; soft-PLC owns control logic.”

**Open soft-PLCs** (OpenPLC and related open-hardware controllers) are treated as real IEC 61131-3 targets in recent verification work ([2607.08550](https://arxiv.org/abs/2607.08550)), which also stresses that **scan-cycle models diverge from physical I/O** (ADC resolution, word width)—a warning for binding non-real-time HA entities as “inputs.”

**Home Assistant landscape (complement):** HA’s native automation engine, helpers, and most “advanced automation” tools (**pyscript**, **AppDaemon**, **Node-RED**, **C.A.F.E.**, **ST for HA**) are **event-driven or transpile-to-event**. Official **Modbus** / **MQTT** and community **S7/TwinCAT** integrations usually make HA a *client of* a PLC, not a soft-PLC I/O fabric. **FUXA** is SCADA/HMI (addon), not a PLC runtime. **InfluxDB** + **Grafana** and **Lovelace/kiosk** already cover historian and HMI. Packaging-wise, a scan-cycle soft-PLC fits the established **Supervisor addon (+ thin Core integration)** pattern used by AppDaemon/Node-RED better than stuffing a cyclic runtime inside Core.

**Competitive evaluation (complement):** Detailed review of similar offerings (OpenPLC+Modbus, redPlc+Node-RED, ST_HA_Automation, S7/TwinCAT bridges, FUXA, PiPLC, ESP soft-PLCs) shows a clear **white space**: no turnkey product combines scan-cycle soft-PLC + first-class HA entity I/O + HA packaging. Closest pieces are *compose* (OpenPLC) or *language-only* (ST_HA) or *opposite direction* (physical PLC integrations).

**Implication for SWD-70:** Prefer an architecture that **preserves IEC 61131 scan semantics** (HAOS **addon** soft-PLC or equivalent sidecar + entity I/O bridge) over pure ST→HA-automation transpile if the goal is “all the capabilities of a PLC.” Reuse HA for **entity fabric, HMI, and historian**. Event-driven transpile (including [ST_HA_Automation](https://github.com/Auda29/ST_HA_Automation)) remains a lighter alternative but is a **different paradigm**.
## Key papers

### Core (architecture / semantics)

| arXiv | Why it matters for SWD-70 |
|-------|---------------------------|
| [1303.4761](https://arxiv.org/abs/1303.4761) | 61131 vs 61499: cyclic industrial baseline vs event-driven academic push; challenges “event-driven = next gen” claims |
| [1402.3920](https://arxiv.org/abs/1402.3920) | PLC (61131) + higher abstraction (SysML/UML) + **IoT as integration technology** for cyber/cyber-physical parts |
| [1407.2077](https://arxiv.org/abs/1407.2077) | CPS development: PLC **or** embedded board targets; IoT as cyber-interface glue—supports “HA entities as I/O” framing |
| [2607.08550](https://arxiv.org/abs/2607.08550) | **OpenPLC** and open-hardware PLCs as IEC 61131-3 platforms; verification over **scan-cycle** model vs hardware-faithful I/O |
| [1009.0817](https://arxiv.org/abs/1009.0817) | Formal SFC→BIP transform; invariant-preserving PLC semantics |
| [1301.3047](https://arxiv.org/abs/1301.3047) | Coq formalization of SFC/IL/LD/FBD and relations between languages |
| [1912.10629](https://arxiv.org/abs/1912.10629) | Ladder as I→logic→O; scan-oriented PLC program shape for verification |
| [2404.14030](https://arxiv.org/abs/2404.14030) | Behavior Trees for modular coordination **on** PLCs (61131 and 61499 strategies)—flexibility without abandoning controllers |
| [2202.10075](https://arxiv.org/abs/2202.10075) | Native IEC 61131-3 as the execution substrate (even for ML inference)—shows value of staying *on* the PLC language/runtime |
| [1405.2409](https://arxiv.org/abs/1405.2409) | Spec→**Structured Text** synthesis for real PLC targets—ST as portable textual PLC language |
| [2410.22159](https://arxiv.org/abs/2410.22159) | ST generation with compiler feedback—ST remains central engineering language |
| [2108.09753](https://arxiv.org/abs/2108.09753) | aPS controlled by PLC/61131 POUs; clone/variability realities of industrial control software |

### Supporting (from same search page)

LLM-assisted LD/ST/SFC work ([2410.15200](https://arxiv.org/abs/2410.15200), [2509.12593](https://arxiv.org/abs/2509.12593), [2311.10401](https://arxiv.org/abs/2311.10401)); verification tooling ([2606.23870](https://arxiv.org/abs/2606.23870), [2606.15461](https://arxiv.org/abs/2607.10499)); complexity metrics ([2212.05918](https://arxiv.org/abs/2212.05918)); MDE ([2212.06607](https://arxiv.org/abs/2212.06607)); smart-grid cyber ranges with PLC-like assets ([2404.00869](https://arxiv.org/abs/2404.00869), [2509.10568](https://arxiv.org/abs/2509.10568)).

## Themes and trends

1. **Scan cycle is the semantic heart of “PLC.”** Verification and formalization papers repeatedly use an abstract scan-cycle model ([2607.08550](https://arxiv.org/abs/2607.08550), [1912.10629](https://arxiv.org/abs/1912.10629)). An architecture that only fires on HA state-change events is not the same object class.

2. **Event-driven ≠ drop-in upgrade.** IEC 61499’s event-driven story is contested ([1303.4761](https://arxiv.org/abs/1303.4761)). Mapping ST to HA automations inherits event-driven tradeoffs (ordering, timers, re-entrancy) rather than PLC scan guarantees.

3. **Separate concerns: devices/IoT fabric vs control runtime.** CPS papers place IoT at cyber interfaces and keep PLC (or embedded) for control ([1402.3920](https://arxiv.org/abs/1402.3920), [1407.2077](https://arxiv.org/abs/1407.2077))—aligns with HA entities as I/O + soft-PLC for logic.

4. **Open soft-PLCs are legitimate 61131 targets.** OpenPLC appears as a first-class open-hardware PLC platform in 2026 verification work ([2607.08550](https://arxiv.org/abs/2607.08550)), supporting a **sidecar soft-PLC** option for PLCAssistant.

5. **I/O fidelity matters.** Hardware-faithful input models discard unrealizable sensor values ([2607.08550](https://arxiv.org/abs/2607.08550)). HA entities (wireless, cloud, polling) need **availability/freshness/fail-safe** policies—not pretence of industrial I/O timing.

6. **ST (and LD) remain the engineering lingua franca** for generation and tooling ([1405.2409](https://arxiv.org/abs/1405.2409), [2410.22159](https://arxiv.org/abs/2410.22159)).

## Home Assistant technology landscape

Survey of HA-native and adjacent offerings that PLCAssistant can **reuse**, **compete with**, or **compose**. Sources are official HA docs and named community projects (not arXiv).

### Entity fabric (field I/O)

| Offering | Role for PLCAssistant |
|----------|------------------------|
| **Entities + states** | Natural PLC *inputs* (sensors, binary_sensors, availability) |
| **Services / actions** | Natural PLC *outputs* (`switch.turn_on`, `light.turn_on`, `number.set_value`, …) |
| **Helpers** (`input_boolean`, `input_number`, `input_select`, …) | Memory/%M-style tags, setpoints, operator overrides |
| **Timer helpers** | Building blocks for TON/TOF/TP-like behaviour ([timer integration](https://www.home-assistant.io/integrations/timer)); also used by ST_HA_Automation |
| **Template helpers** | Derived tags / scaling without a separate runtime |
| **WebSocket / REST Core API** | Preferred bridge for addon/sidecar runtimes to read state and call services |

HA is **state- and event-driven**: integrations push state changes; automations react. There is **no first-party scan cycle**.

### Control / logic layers (mostly event-driven)

| Offering | Packaging | Execution model | PLCAssistant relevance |
|----------|-----------|-----------------|------------------------|
| **Native automations / scripts** | Core | Event triggers → conditions → actions | Baseline HA control; not a soft-PLC |
| **[ST for Home Assistant](https://github.com/Auda29/ST_HA_Automation)** | HACS integration | ST **transpiled** to native HA automations; timers via helper entities | Concrete instance of roadmap option **#3** (language feel, event semantics) |
| **pyscript** | HACS custom integration | Python in Core process | Could implement a soft scan loop in-process (stability risk) |
| **AppDaemon** | Supervisor **addon** | External Python apps over HA API | Precedent for **sidecar logic engine** next to Core |
| **Node-RED** (+ companion) | Supervisor **addon** | Visual flows / optional ladder-ish community nodes | Precedent for addon soft-logic; still not IEC 61131 scan PLC |
| **C.A.F.E.** | HACS | Visual flows → **native YAML** | Authoring UX; same event runtime as Core |
| **NetDaemon** | Addon/external | C# automations | Same packaging family as AppDaemon |

**Gap:** none of the above is a first-class **IEC 61131 scan-cycle soft-PLC with HA entities as I/O**. Closest language-shaped option is ST_HA_Automation; closest packaging precedent for a real cyclic engine is an **addon** (AppDaemon/Node-RED pattern).

### Industrial protocol bridges (usually PLC → HA, not the reverse)

| Offering | Notes |
|----------|--------|
| **[Modbus](https://www.home-assistant.io/integrations/modbus)** (official) | HA as Modbus **client** to PLCs/RTUs; proven path to talk to **OpenPLC** coils/registers |
| **MQTT** (+ Mosquitto addon) | Common bus between HA, soft-PLCs, and SCADA tools |
| **Community S7 / TwinCAT / Logo** integrations | Expose **physical** PLC tags as HA entities (opposite ownership of I/O) |

These matter for a **sidecar OpenPLC** design: either map HA entities ↔ PLC tags over WebSocket, **or** expose the soft-PLC over Modbus and also mirror tags into HA for Lovelace/historian (or both).

### HMI and historian (reuse, do not reinvent)

| Offering | Role |
|----------|------|
| **Lovelace** + tablet **kiosk** mode | Equipment HMI panels against the same entities/tags |
| **[FUXA](https://github.com/SmartLiving-Rocks/FUXA)** addon | Industrial SCADA/HMI editor (Modbus/MQTT/S7/…); **not** a PLC runtime; optional richer HMI than Lovelace |
| **[InfluxDB integration](https://www.home-assistant.io/integrations/influxdb)** | Push entity state changes to time-series DB (historian) |
| **Grafana** addon | Trend/analysis dashboards; embeddable in Lovelace via iframe |
| Core **Recorder / History** | Short-term history; not a full industrial historian |

This validates roadmap phases 4–5: PLCAssistant should **emit/bind entities** that Influx/Grafana/Lovelace already understand.

### Packaging models (integration vs addon)

| Model | Runs where | Best for |
|-------|------------|----------|
| **Custom integration (HACS)** | Inside Home Assistant Core (Python) | Config UI, entity exposure, thin I/O bridge, optional light logic |
| **Supervisor addon / app** | Separate container next to Core; Core API via `http://supervisor/core/api` / `ws://supervisor/core/websocket` + `SUPERVISOR_TOKEN` ([app communication docs](https://developers.home-assistant.io/docs/apps/communication/)) | Heavy runtimes (OpenPLC, Node-RED, AppDaemon, Grafana, FUXA) |
| **Hybrid** | Addon runtime + thin HACS/Core integration | Soft-PLC scan engine isolated from Core; entities/config feel native in HA |

HA architecture discussions emphasize that addons are **standalone apps beside Core**, not plugins inside it—matching the CPS split from the literature (IoT fabric vs control runtime).

### How HA offerings map to SWD-70 candidates

```text
HA devices / Zigbee / ESPHome / …  →  entities (I/O fabric)
        │
        ├─► Native automations / ST_HA / pyscript / Node-RED   (event-driven control)
        │
        └─► PLCAssistant (proposed): scan soft-PLC addon
                 │  read states / call services (WebSocket)  and/or Modbus mirror
                 ▼
            Lovelace kiosk / FUXA (HMI)   +   InfluxDB → Grafana (historian)
```

| Candidate | Natural HA packaging | Closest existing HA tech |
|-----------|----------------------|---------------------------|
| Soft-PLC sidecar + HA I/O | **Addon** (+ thin integration for config/entities) | OpenPLC via Modbus **or** new WebSocket I/O driver; AppDaemon-style sidecar |
| In-HA soft runtime | Custom integration or pyscript scan loop | No mature product; Core-risk |
| ST→automation transpile | HACS integration | **ST_HA_Automation** |
| Hybrid | Addon soft-PLC + Core entity bridge + Lovelace/Influx | Compose OpenPLC/Modbus/MQTT + HA stack |

## Detailed evaluation of similar HA integrations and apps

Evaluation criteria (for PLCAssistant goals):

| Criterion | Question |
|-----------|----------|
| **I/O ownership** | Are HA entities the *field I/O* of the controller, or is HA only HMI/SCADA to an external PLC? |
| **PLC semantics** | Scan cycle? IEC 61131 languages (LD/ST/FBD)? Timers/counters as first-class? |
| **Packaging** | Core integration, HACS, Supervisor addon, or DIY compose? |
| **HMI / historian** | Built-in vs relies on Lovelace / Influx / Grafana / FUXA? |
| **Maturity** | Official / widely adopted / early community / alpha hardware |
| **Relation** | *Compete* (same job), *compose* (building block), *adjacent* (related UX), *opposite* (PLC owns I/O) |

Scores below are qualitative **fit to PLCAssistant’s product gap** (not overall product quality): ●●● strong, ●● partial, ● weak / wrong direction.

### Comparison matrix

| Offering | I/O ownership | PLC semantics | Packaging | Fit | Relation |
|----------|---------------|---------------|-----------|-----|----------|
| [ST_HA_Automation](https://github.com/Auda29/ST_HA_Automation) | HA entities | ST **language**, event runtime | HACS | ●● | Compete (authoring) |
| [OpenPLC Runtime](https://github.com/Autonomy-Logic/openplc-runtime) + HA Modbus | Usually OpenPLC I/O / Modbus tags; HA as client | Full IEC 61131 scan | DIY / possible addon | ●● | Compose |
| [HomeAssistant-OpenPLC](https://github.com/Epaminondaslage/HomeAssistant-OpenPLC) tutorial | Modbus bridge via Node-RED | OpenPLC scan | DIY docs | ●● | Compose / docs |
| [redPlc](https://github.com/redplc/redplc) + Node-RED + HA | Manual map NR context ↔ HA | Ladder-like soft-PLC in NR | Addon + palette | ●● | Compete / compose |
| AppDaemon / pyscript / NetDaemon | HA entities | General code, no IEC PLC | Addon / HACS | ● | Adjacent |
| Native HA automations / C.A.F.E. | HA entities | Event automations | Core / HACS | ● | Adjacent |
| Official [Modbus](https://www.home-assistant.io/integrations/modbus) | External PLC → HA entities | None (protocol client) | Core | ●● | Compose |
| [ha-s7plc](https://github.com/xtimmy86x/ha-s7plc) / [ha-s7](https://github.com/gijzelaerr/ha-s7) | Physical S7 → HA (+ optional entity→PLC sync) | External Siemens PLC | HACS | ● | Opposite (+ compose sync) |
| Official [ADS](https://www.home-assistant.io/integrations/ads) / TwinCAT IoT Communicator | TwinCAT → HA | External Beckhoff soft-PLC | Core / HACS | ● | Opposite |
| [FUXA](https://github.com/SmartLiving-Rocks/FUXA) HA addon | Industrial protocols / MQTT | HMI/SCADA only | Addon | ● | Adjacent (HMI) |
| InfluxDB + Grafana addons | Entity history | Historian/viz only | Core + Addon | ●●● (reuse) | Compose |
| Lovelace / kiosk | Entity UI | HMI only | Core | ●●● (reuse) | Compose |
| [PiPLC](https://github.com/Chrismettal/PiPLC) | Pi GPIO / Modbus hardware | Designed for OpenPLC + HA | Hardware + docs | ●● | Compose (hardware) |
| [PiLab ESP32-P4 PLC](https://github.com/OpenPiLab/pilab-esp32-p4-plc) | On-device I/O; REST/JSON | Scan + ladder/AngelScript (alpha) | External MCU | ● | Adjacent / future compose |

### A. Soft-PLC engines that can sit beside HA

#### OpenPLC Runtime (+ Modbus ↔ HA)

- **What it is:** Headless IEC 61131-3 soft-PLC (LD/ST/FBD, …) with deterministic scan cycles, editor upload API, I/O plugins ([OpenPLC Runtime v4](https://github.com/Autonomy-Logic/openplc-runtime)).
- **HA coupling today:** Not a first-party HA addon. Typical pattern: HA [Modbus](https://www.home-assistant.io/integrations/modbus) **client** reads/writes OpenPLC coils/registers; tutorials also route through Node-RED ([HomeAssistant-OpenPLC](https://github.com/Epaminondaslage/HomeAssistant-OpenPLC)). Community notes that the hard part is binding **HA variables into** the PLC IDE ([HA forum](https://community.home-assistant.io/t/integration-of-ladder-programming-or-functional-plan-similar-step7/620120)).
- **I/O ownership:** By default OpenPLC owns physical/Modbus I/O; HA is HMI/SCADA **client**. Making HA entities the field bus requires a custom I/O plugin or continuous entity↔register mirroring—the missing product piece.
- **Strengths:** Real PLC semantics; languages; editor ecosystem; academically recognized ([2607.08550](https://arxiv.org/abs/2607.08550)).
- **Weaknesses for PLCAssistant:** No turnkey “HA entity I/O driver”; dual systems to operate; Modbus mapping is manual and lossy for rich HA entity attributes.
- **Learn / reuse:** Strong candidate **runtime to wrap** as a Supervisor addon; use Modbus and/or WebSocket HAL for entity binding.

#### redPlc (Node-RED ladder soft-PLC)

- **What it is:** Node-RED palette implementing ladder contacts/coils/timers/counters/memory with I/Q/M-style arrays and first-scan hooks ([redplc](https://github.com/redplc/redplc), npm `@redplc/node-red-redplc`).
- **HA coupling:** Via Node-RED HA websocket nodes / MQTT; HAOS already has a Node-RED addon. Discussed on HA community as a ladder alternative to YAML ([forum thread](https://community.home-assistant.io/t/integration-of-ladder-programming-or-functional-plan-similar-step7/620120)).
- **I/O ownership:** Possible to treat HA entities as I/Q by flow glue—but not a first-class binding UX; logic lives in Node-RED context, not HA.
- **Strengths:** Ladder UX; soft-PLC vocabulary; runs in familiar HA addon; timers/counters present.
- **Weaknesses:** Tied to Node-RED (second engine); not a full IEC suite (no native ST/FBD IDE); scan timing is Node-RED’s event/message model, not a hard SCHED_FIFO PLC cycle; dual UI for operators (NR + Lovelace).
- **Learn / reuse:** Proves demand for ladder-on-HA; packaging path (addon) validated; PLCAssistant should aim for **tighter entity binding** and less glue than redPlc+HA.

### B. “Looks like PLC” but event-driven inside HA

#### ST for Home Assistant (ST_HA_Automation)

- **What it is:** HACS integration: write IEC 61131-3 **Structured Text**, transpile to **native HA automations**; entity bindings (`AT %I*` / `%Q*` / `%M*`); TON/TOF/TP via HA timer helpers; live editor ([ST_HA_Automation](https://github.com/Auda29/ST_HA_Automation)).
- **I/O ownership:** HA entities — **same direction as PLCAssistant**.
- **PLC semantics:** Language surface yes; **runtime no** (event triggers from entity dependencies, not cyclic scan).
- **Strengths:** Closest *in-HA* industrial authoring experience; no sidecar; transactional deploy story.
- **Weaknesses:** Early/low public adoption signals; inherits HA event semantics (ordering, interlocks, continuous evaluation differ from scan); no LD/FBD engineering suite; not suitable if “all capabilities of a PLC” means scan-cycle behaviour.
- **Relation:** Direct **competitor on language/UX**, not on runtime architecture. PLCAssistant can position as complementary (scan runtime) or absorb ST authoring later.

#### Native automations, C.A.F.E., pyscript, AppDaemon, NetDaemon

- **What they are:** General automation frameworks (YAML/UI, visual→YAML, Python/C#).
- **Fit:** Excellent for home logic; **poor** as PLC substitutes (no IEC scan model, no industrial tag HAL).
- **Relation:** Adjacent; AppDaemon/Node-RED packaging is the **precedent** for a PLCAssistant addon.

### C. Physical / commercial soft-PLC bridges (opposite I/O ownership)

#### Modbus (official), ha-s7plc / ha-s7, ADS / TwinCAT IoT Communicator

- **What they do:** Map **external PLC** memory to HA entities (sensors/switches/…). Some (e.g. ha-s7plc **Entity Sync**) can push HA entity state *into* PLC addresses—interesting but still assumes a real PLC owns control.
- **Fit to PLCAssistant:** Wrong primary direction (HA is SCADA to PLC). Useful **compose** pieces if PLCAssistant *is* the PLC and needs protocol exposure, or for hybrid sites with both.
- **Maturity:** Modbus and ADS are official; S7/TwinCAT community integrations are actively maintained relative to ST_HA.

### D. HMI / historian apps (not controllers)

#### FUXA addon

- Web SCADA/HMI with Modbus/MQTT/S7/… ([SmartLiving-Rocks/FUXA](https://github.com/SmartLiving-Rocks/FUXA)). Optional richer process graphics than Lovelace.
- **Not** a PLC. Compose for phase-4 HMI if Lovelace kiosk is insufficient.

#### InfluxDB + Grafana

- Standard HA historian path. PLCAssistant should expose entities/tags that these already consume—do not build a parallel historian.

### E. Hardware-oriented soft-PLCs near HA

#### PiPLC

- Pi breakout / DIN-rail hardware aimed at **OpenPLC + Home Assistant** ([Chrismettal/PiPLC](https://github.com/Chrismettal/PiPLC)). Documents Modbus between OpenPLC and HA; frames HA as UI/telemetry and OpenPLC as control.
- **Relation:** Hardware + architecture essay supporting **compose OpenPLC with HA**, not an HA integration that binds entities as I/O.

#### ESP32 / PiLab-class open PLCs

- Alpha edge PLCs with scan loops, ladder/AngelScript, REST/JSON (e.g. [OpenPiLab/pilab-esp32-p4-plc](https://github.com/OpenPiLab/pilab-esp32-p4-plc)); HA forum posters suggest REST/MQTT bridging interest.
- **Relation:** Adjacent external soft-PLCs; possible future peers via MQTT/REST, not turnkey HA entity I/O products.

### White space (what still does not exist)

No evaluated offering simultaneously provides:

1. **IEC-style (or equivalent) scan-cycle soft-PLC**, and  
2. **First-class bidirectional binding of arbitrary HA entities as field I/O**, and  
3. **HA-native packaging** (addon and/or HACS) with Lovelace + Influx/Grafana as default HMI/historian.

Closest approximations:

| Approximation | Missing piece |
|---------------|---------------|
| OpenPLC + Modbus + HA | Entity↔tag I/O driver & HA-centric packaging/UX |
| redPlc + Node-RED + HA | Tight entity HAL, non-NR engineering, true scan isolation |
| ST_HA_Automation | Scan-cycle runtime (not transpile-to-events) |
| S7/TwinCAT integrations | Soft-PLC *inside* HA stack; they need an external PLC |

**Implication:** PLCAssistant’s differentiation is the **entity I/O HAL + scan runtime + HA packaging**, not inventing HMI/historian or another Modbus client.

### Competitive positioning options (for `/define`)

| Strategy | Description | Pros | Cons |
|----------|-------------|------|------|
| **Wrap OpenPLC** | Addon shipping/runtime-managing OpenPLC + entity↔Modbus/WebSocket bridge | Real IEC stack; faster to “PLC-complete” | Upstream dependency; dual tooling (OpenPLC Editor + HA) |
| **Custom soft runtime** | Own scan engine in addon; ST/LD subset | Full UX control; HA-native tags | Larger build; language/editor cost |
| **redPlc-first** | Document/productize NR+redPlc+HA entity recipes | Fast demo | Locked to Node-RED; weak product identity |
| **ST_HA adjacency** | Ship scan runtime; optionally interop/import ST later | Clear differentiation from transpile | Must not confuse users with ST_HA |

Working lean remains: **wrap or embed a scan soft-PLC as an addon**, invest differentiation in **HA entity I/O binding UX**, reuse Lovelace/Influx/Grafana; treat ST_HA and redPlc as category proof and competitors on *language/ladder UX*, not as complete substitutes.

## Gaps and limitations

- **Rate limits** prevented soft-PLC / OpenPLC / PLC+IoT dedicated arXiv queries and snowball expansion; OpenPLC evidence is incidental via the IEC 61131 hit list.
- arXiv set has **no Home Assistant** papers; HA and competitive sections rely on product docs / community projects (preprint peer-review does not apply).
- **Little quantitative comparison** of soft-PLC scan latency vs HA event latency on commodity hosts.
- ST_HA_Automation and several ESP PLC projects show **early/low adoption** public signals — useful as paradigm samples, not maturity proofs.
- Competitive landscape moves quickly; maturity judgments are snapshots (as of research date).
- Preprint corpus for the academic half; peer-review status varies (`journal_ref` sparse in this sample).

## Architecture implications (for `/define SWD-70`)

| Approach | Literature fit | HA ecosystem fit | Fit to PLCAssistant goals |
|----------|----------------|------------------|---------------------------|
| Soft-PLC **addon** (OpenPLC-class) + HA I/O bridge | Strong: OpenPLC as 61131 target ([2607.08550](https://arxiv.org/abs/2607.08550)); CPS/IoT fabric ([1407.2077](https://arxiv.org/abs/1407.2077)) | Strong: matches AppDaemon/Node-RED/Grafana addon pattern; Modbus or WebSocket to Core | Strong for “real PLC” semantics; clear process boundary |
| Soft runtime **inside Core** (integration/pyscript) | Compatible with scan semantics | Possible but atypical; Core crash risk; harder real-time isolation | OK for prototype; weaker for production soft-PLC |
| ST→HA automation transpile | Weak as *PLC* substitute ([1303.4761](https://arxiv.org/abs/1303.4761)) | **ST_HA_Automation** already explores this | Fast language feel; weak scan/interlock semantics |
| Hybrid (scan addon + HA fabric + Lovelace/Influx; optional FUXA) | Supported ([2404.14030](https://arxiv.org/abs/2404.14030), [1402.3920](https://arxiv.org/abs/1402.3920)) | Reuses historian/HMI offerings instead of inventing them | Best long-term MVP shape |

**Working recommendation (evidence-based, not a final product decision):**  
Adopt **scan-cycle soft-PLC semantics** packaged primarily as a **Home Assistant OS/Supervised addon**, with a **thin Core integration** for config and entity exposure. Bind **HA entities as a constrained I/O HAL** (freshness, range, fail-safe) via WebSocket and/or Modbus. **Reuse** Lovelace/kiosk (+ optional FUXA) for HMI and InfluxDB/Grafana for historian. Treat **ST→automation transpile** (and pyscript/Node-RED) as optional *authoring or adjacent* paths, not the PLC runtime. Document non-goals: hard real-time, safety certification.

## Recommended reading order

1. [1303.4761](https://arxiv.org/abs/1303.4761) — 61131 vs 61499 paradigm stakes  
2. [2607.08550](https://arxiv.org/abs/2607.08550) — OpenPLC / scan-cycle / hardware I/O gap  
3. [1407.2077](https://arxiv.org/abs/1407.2077) / [1402.3920](https://arxiv.org/abs/1402.3920) — CPS + IoT fabric around PLCs  
4. [1301.3047](https://arxiv.org/abs/1301.3047) / [1009.0817](https://arxiv.org/abs/1009.0817) — what “PLC semantics” formally means  
5. [2404.14030](https://arxiv.org/abs/2404.14030) — modular coordination without abandoning PLC  
6. [1405.2409](https://arxiv.org/abs/1405.2409) / [2410.22159](https://arxiv.org/abs/2410.22159) — ST as portable engineering language  
7. HA [Modbus](https://www.home-assistant.io/integrations/modbus), [InfluxDB](https://www.home-assistant.io/integrations/influxdb), [timer](https://www.home-assistant.io/integrations/timer) docs — I/O / historian / timer primitives  
8. [App communication (addons)](https://developers.home-assistant.io/docs/apps/communication/) — how a soft-PLC addon talks to Core  
9. [ST_HA_Automation](https://github.com/Auda29/ST_HA_Automation) — transpile paradigm sample  
10. [OpenPLC Runtime](https://github.com/Autonomy-Logic/openplc-runtime) / [redPlc](https://github.com/redplc/redplc) — soft-PLC engines composed with HA today  
11. [ha-s7plc](https://github.com/xtimmy86x/ha-s7plc) — mature *opposite-direction* PLC↔HA bridge  
12. [FUXA HA addon](https://github.com/SmartLiving-Rocks/FUXA) — optional SCADA HMI beside Lovelace  

## Sources

### Academic (arXiv)

Raw search JSON: `docs/research/arxiv_swd70_iec61131_search.json`  
Triage split: `docs/research/arxiv_swd70_triage.json`  

Academic claims above trace to abstracts/metadata in those files (arXiv IDs as cited).

### Home Assistant / product / competitive

- Home Assistant Modbus, InfluxDB, Timer, ADS integrations (official docs)  
- Supervisor app/addon Core API proxy docs  
- Soft-PLC / ladder near HA: OpenPLC Runtime, HomeAssistant-OpenPLC tutorial, redPlc, ST_HA_Automation  
- Physical PLC bridges: ha-s7plc, ha-s7, TwinCAT IoT Communicator  
- HMI/hardware: FUXA HA addon, PiPLC, PiLab ESP32-P4 PLC  
- HA community thread on ladder/Step7-like programming  
- AppDaemon / Node-RED / pyscript packaging discussions  

HA and competitive-section claims trace to those named docs/repos (community maturity varies).
## Tracker

- Task: [SWD-70](https://marcusknielsen.atlassian.net/browse/SWD-70)
- Artifact: `docs/RESEARCH.md`
- Story: [SWD-66](https://marcusknielsen.atlassian.net/browse/SWD-66)

## Next

`/ship SWD-70` — Review-fix CLEAN; merge architecture artifacts.
