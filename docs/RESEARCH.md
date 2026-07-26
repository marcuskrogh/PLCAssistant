# Research: HA-native sensors & actuators for process applications

**Project:** PLCAssistant (virtual PLC for Home Assistant)  
**Date:** 2026-07-26  
**Scope:** Off-the-shelf products that natively integrate with Home Assistant over Wi‑Fi, Thread/Matter, Zigbee, Z‑Wave, Bluetooth, ESPHome, Modbus, or other typical HA protocols — for process-style I/O (temperature, flow, pressure, level, pumps, valves, etc.).  
**Question answered:** Do we need custom ESP devices, or do suitable products already exist?

---

## 1. Executive verdict

| Need class | Buy off-the-shelf? | Custom ESP / gateway? |
|---|---|---|
| Ambient temp/humidity, leak, simple on/off loads | **Yes** — large mature catalog | Rarely needed |
| Domestic water: shutoff valves, irrigation valves, consumption meters | **Yes** — good options (Zigbee/Matter/Wi‑Fi/cloud-native) | Optional |
| Probe temperature (pipe/tank DS18B20-class) | **Partially** — Shelly Add-on, Sonoff TH + probe, ESPHome kits | Often better via ESP/Shelly |
| Process pressure / flow / tank level (accurate, continuous) | **Sparse** — a few niche Zigbee/Wi‑Fi products; mostly DIY or Modbus | **Usually yes** |
| Chemistry (pH, ORP, EC/conductivity) | **No turnkey HA products** | **Yes** (ESPHome + Atlas Scientific EZO, etc.) |
| Industrial pumps / VSDs / 4–20 mA / PT100 RTD buses | **No HA-native wireless products** | **Yes** — Modbus TCP/RTU or ESP RS‑485 gateway |
| Dense digital I/O (DI/DO for PLC-like wiring) | **Limited** — frient IO Module, KinCony ESP boards, Shelly relays | **Yes** for DIN-rail density |

**Bottom line for PLCAssistant:**  
A large share of *home-scale* process monitoring can be covered with existing HA-native hardware. **True process / industrial I/O (transducers, RTDs, flowmeters, VFD pumps, analog 4–20 mA)** almost always needs either (a) Modbus-capable field devices + HA Modbus, or (b) ESPHome/KinCony-style gateways that expose those signals to HA. Building or buying ESP-class devices is still required for many process signals; it is *not* required for ambient sensors, leak protection, and many water valves.

---

## 2. What “natively integrates with HA” means here

Included when **at least one** of the following is true:

| Integration path | Local? | Notes |
|---|---|---|
| **Works with Home Assistant** certified | Yes (required for WWHA) | Tested by HA team; listed at [works-with.home-assistant.io](https://works-with.home-assistant.io/certified-products/) |
| Core integration (Shelly, Matter, ZHA, Z-Wave JS, Ecowitt, Flo, Modbus, ESPHome, …) | Usually local | First-class UI discovery / config |
| Zigbee2MQTT / ZHA supported device | Local | Z2M often has broader Tuya/EFEKTA coverage than ZHA |
| ESPHome native API (`api:`) | Local | “Made for ESPHome” commercial hardware counts |
| Official vendor cloud integration in core | Cloud | e.g. Flo by Moen — native but not local-first |

**Excluded / deprioritized:** devices that only work via undocumented cloud APIs, proprietary hubs with no HA path, or require reverse-engineered HACS components with no stable support (mentioned only when no better option exists).

---

## 3. Protocol landscape for process I/O

| Protocol | Strength for process apps | Weakness | HA path |
|---|---|---|---|
| **Wi‑Fi (Shelly, ESPHome, Ecowitt gateway)** | High bandwidth, easy probes/ADC, Ethernet options | Power, RF congestion, AP dependency | Shelly, ESPHome, Ecowitt, HomeWizard |
| **Zigbee (ZHA / Z2M)** | Huge sensor catalog, mesh, battery | Few industrial transducers; Tuya quirks | ZHA or Zigbee2MQTT |
| **Z‑Wave (Z-Wave JS)** | Reliable mesh, strong EU/US install base | Thin process catalog (mostly comfort/leak) | Z-Wave JS |
| **Matter over Thread / Wi‑Fi** | Future-proof; HA supports valve/pump domains | Consumer products dominate; few process instruments | Matter Server + Thread BR |
| **Bluetooth** | Cheap meters (SwitchBot) | Range, polling, not for plant floors | SwitchBot / BTHome |
| **Modbus TCP/RTU** | *De facto* industrial sensor/actuator bus | YAML/config work; not “pair and play” | Core `modbus` integration |
| **MQTT** | Flexible for custom gateways | You own the schema | MQTT + discovery |

Matter already exposes HA domains useful for process control (`valve`, `pump`, `sensor` including pressure/flow in the Matter stack). Commercial Matter *process instruments* remain rare; most Matter devices are climate/security/lighting.

---

## 4. Capability matrix (process signal → options)

### 4.1 Sensors

| Signal | Off-the-shelf HA-native examples | Typical accuracy / notes | DIY / ESP still needed? |
|---|---|---|---|
| **Air temperature / humidity** | Aqara Climate Sensor (Matter/Thread), Sonoff SNZB-02D (Zigbee), SwitchBot Meter, Eve Weather, Apollo TEMP-1 (ESPHome), Shelly H&T | Consumer ±0.2–0.5 °C | No |
| **Atmospheric pressure** | Aqara T1 (Zigbee; best via Z2M), Apollo multisensors | Ambient only | No |
| **Probe / media temperature** (pipe, tank, immersion) | Shelly Plus Add-on + DS18B20 (up to 5), Sonoff TH Elite + WTS01, ESPHome DS18B20/PT100 boards | DS18B20 ~±0.5 °C; not industrial RTD | Often for PT100/PT1000 |
| **Water leak / flood** | Sonoff SNZB-05P, Aqara, frient, Zooz ZSE42, Aeotec Water Sensor 7 Pro, SwitchBot Leak, Heiman Matter | Binary | No |
| **Soil moisture** | Ecowitt WH51 (+ gateway), Apollo PLT-1, EFEKTA PWS/zFlora (Z2M), Sonoff MS01 via TH Elite | Agricultural / garden grade | No for garden; yes for lab-grade |
| **Water flow rate / consumption** | Flo by Moen (cloud core), HomeWizard Watermeter (Wi‑Fi, optical on meter), Sonoff SWV (flow), Tuya ultrasonic valve meters (Z2M), FrankEver FK-BV05, SmartHomeShop WaterFlowKit (ESPHome) | Domestic water | Yes for industrial mag/ultrasonic meters |
| **Water / gas line pressure** | Flo/Phyn (domestic), EFEKTA PST Zigbee pressure monitors (Z2M), Shelly Add-on + 0–10 V transducer | Consumer / light commercial | Yes for 4–20 mA industrial |
| **Tank / vessel level** | Almost no turnkey HA product | Ultrasonic / hydrostatic DIY common | **Yes** (ESPHome or Zigbee custom) |
| **Filter / differential pressure** | Rare commercial | Pool DIY common | **Yes** |
| **pH / ORP / EC** | Atlas Scientific kits → flash ESPHome `ezo` | Lab/pool grade | **Yes** |
| **Energy / pump load proxy** | Shelly 1PM/Pro EM, HomeWizard, frient EMI | Good for inferring pump state | No |

### 4.2 Actuators

| Actuator | Off-the-shelf HA-native examples | Notes | DIY / ESP still needed? |
|---|---|---|---|
| **Mains relay / contactor drive** | Shelly 1/1PM/Pro, Sonoff, Wave (Z-Wave), KinCony KC868 | Use for pump contactors if properly rated | No for simple on/off |
| **Smart plug / outdoor plug** | Eve Energy, Shelly Plug, frient Smart Plug | Light pumps / dosing only | No |
| **Motorized ball / irrigation valve** | Aqara Valve Controller T1 (Zigbee/Matter bridge), Sonoff SWV, Tuya/FrankEver/Nous Zigbee valves, Grimsholm Matter irrigation valve | Garden / domestic | No for garden valves |
| **Whole-home water shutoff** | Flo by Moen (core), Phyn (HACS/local community), some Zigbee ball valves | Leak automation | Prefer certified local where possible |
| **Peristaltic / dosing pump** | Apollo PUMP-1 (ESPHome, WWHA) | ~900 ml/min plant dosing — not process transfer | Yes for industrial dosing |
| **Variable-speed pump / VFD** | None wireless turnkey | RS‑485 Modbus via ESPHome or HA Modbus | **Yes** |
| **Analog output 0–10 V / 4–20 mA** | Shelly 0–10 V dimmers (lighting-oriented), KinCony AO boards | Not process-certified | Usually yes |
| **Low-voltage DI/DO bridge** | frient IO Module (4 DI + 2 DO, Zigbee, WWHA) | Excellent for dry contacts / low-V loads | Dense I/O → KinCony/ESP |

---

## 5. Product catalog by protocol

### 5.1 Wi‑Fi / Ethernet — first-class local

#### Shelly (core integration, local, auto-discovery)

| Product | Process role |
|---|---|
| **Plus/Gen3/Gen4 1, 1PM, 2PM, Pro 1/2** | Pump/valve relays; power metering as soft sensor |
| **Plus Add-on** | Up to 5× DS18B20 **or** 1× DHT22; digital input; analog %; 0–10 V voltmeter — soil moisture, capacitive level, wind, pressure transducers (voltage out) |
| **H&T, Flood, Gas (+ valve add-on)** | Environment + safety + gas valve entity |
| **TRV** | Climate valve (HVAC, not process media) |
| **Pro EM / 3EM + Pro Modbus Add-on RS‑485** | Energy + **Modbus client/server** toward BMS/PLC/meters — important bridge into industrial gear |
| **Wave series (Z-Wave)** | Same relay roles on Z-Wave mesh; WWHA for several models |

Shelly is the strongest *commercial* non-DIY path for “relay + probe temperature + light analog I/O” without writing firmware.

#### Ecowitt (core, local push)

Gateway (GW1200/2000/3000) + sensors: **WH51 soil moisture**, outdoor temp/humidity/pressure, rain, wind, soil temperature. Excellent for outdoor/process-adjacent monitoring. Requires HTTP (not HTTPS-only) to HA.

#### HomeWizard (core / WWHA)

**Watermeter (HWE-WTR)** — clamps onto many mechanical water meters; live consumption when USB-powered. Strong for facility water accounting, not inline process flow.

#### Flo by Moen (core, cloud polling)

Whole-home shutoff with **flow, pressure, temperature, daily consumption**, valve switch, health test / home/away/sleep modes. Native but cloud-dependent.

#### Apollo Automation (ESPHome, WWHA, Open Home Foundation partner)

| Product | Role |
|---|---|
| TEMP-1 | Temp/humidity |
| PLT-1 | Soil moisture |
| PUMP-1 | Fluid dosing pump |
| AIR-1 / MTR-1 / MSR-2 / R PRO-1 | Air quality / presence (less process-critical) |

#### SmartHomeShop WaterFlowKit (ESPHome)

Commercial ESP32 / ESP32-C6 board for **YF-series pulse flow sensors** + optional water temp; multi-channel; local HA API. Closest turnkey “process flow” Wi‑Fi product in the hobby/prosumer space.

#### AirGradient (WWHA Wi‑Fi)

Indoor/outdoor AQ — useful for plant air, not fluid process.

---

### 5.2 Zigbee (ZHA / Zigbee2MQTT)

#### Strong HA ecosystem picks

| Vendor / model | Role | Integration notes |
|---|---|---|
| **Aqara** temp/humidity (e.g. T1 WSDCGQ12LM), leak sensors | Ambient + leak | ZHA/Z2M; pressure better on Z2M |
| **Aqara Valve Controller T1** | Motorized valve (existing handle) | Zigbee; Matter-over-bridge via Aqara hub; WWHA |
| **Sonoff SNZB-02D / SNZB-05P / SWV** | Temp/humidity, leak, smart water valve + flow | ZHA/Z2M; SWV exposes flow (m³/h) |
| **frient** humidity, leak, **IO Module**, plugs, EMI | Ambient + **wired DI/DO bridge** | WWHA / ZHA certified set |
| **Third Reality, Heiman** | Temp, leak (also Matter variants) | ZHA/Z2M/Matter |
| **Tuya / FrankEver / Nous water valves** | Valve + flow/consumption/temp | Prefer **Zigbee2MQTT**; ZHA quirks common |
| **EFEKTA PST\* pressure monitors** | Water/gas **line pressure** (0–1 … 0–40 bar sensor types) + temp | Z2M; rare Zigbee process-ish instrument |
| **EFEKTA soil sensors** | Soil moisture plants | Z2M |

#### Zigbee gaps for process

- Almost no calibrated industrial flow/mag meters.
- Almost no PT100/thermocouple transmitters as Zigbee end devices.
- AnalogInput / Flow Measurement clusters exist in ZCL and ZHA codepaths, but commercial devices rarely implement them cleanly.

---

### 5.3 Z‑Wave (Z-Wave JS)

| Vendor / model | Role |
|---|---|
| **Aeotec Water Sensor 7 Pro** | Leak + temp + humidity |
| **Zooz ZSE42 / ZSE44** | Leak; temp/humidity |
| **Sensative Strips Comfort / Drip** | Ultra-thin temp/light; leak+temp |
| **Heatit** wall controllers / floor thermostats | HVAC-oriented |
| **Shelly Wave / Leviton** switches | Load control |
| **Zooz / Aeotec sticks** | Controllers |

Z‑Wave is excellent for **reliability of binary safety and comfort sensors**, weak for continuous process instrumentation.

---

### 5.4 Matter / Thread

| Product | Role |
|---|---|
| **Aqara Climate Sensor, Valve Controller T1** (bridge/Matter paths) | Climate + valve |
| **Eve Weather / Thermo** | Outdoor weather / TRV |
| **Heiman** Matter leak / temp / CO | Safety |
| **Grimsholm Smart Irrigation Valve** | Matter-over-Thread irrigation + flow/leak/freeze claims |
| **ELTAKO** Matter actuators | DIN building automation (EU) — switching, not instrumentation |

HA Matter integration lists **Pump** and **Valve** platforms — the *software* side is ready; the *hardware* catalog for process pumps/valves is still thin.

---

### 5.5 Bluetooth

| Product | Role |
|---|---|
| **SwitchBot Meter / Meter Pro / Leak / Indoor-Outdoor** | Ambient; WWHA | 
Useful for retrofit monitoring; poor fit for plant rooms needing always-on control loops.

---

### 5.6 Modbus (industrial bridge — native HA, not wireless)

The core **[Modbus](https://www.home-assistant.io/integrations/modbus)** integration speaks TCP, RTU-over-TCP, and serial RS‑485.

**This is the primary path for real process gear:**

- Ultrasonic / magnetic flowmeters with Modbus
- Pressure transmitters with Modbus
- PT100 transmitters / multi-channel RTD modules
- VFDs / soft-starters / heat pumps
- DIN energy meters, PLC data maps

Patterns that work well with HA:

1. **Native Modbus TCP device** → HA `modbus:` sensors/switches/climates  
2. **RS‑485 instrument** → USB-RS485 or Ethernet Modbus gateway (e.g. Waveshare) → HA  
3. **RS‑485 instrument** → **ESP32 + ESPHome `modbus_controller`** → HA API (Wi‑Fi or Thread on C6)  
4. **Shelly Pro + Modbus Add-on** as Modbus client reading meters into Shelly/HA  

Community tooling (e.g. HACS Modbus Wizard) reduces YAML friction but is not required.

---

### 5.7 ESPHome commercial & semi-commercial I/O (when “buy ESP board” ≠ “design PCB”)

| Platform | Why it matters for process |
|---|---|
| **KinCony KC868 series (A8/A16/AIO, …)** | DIN-rail ESP32: many relays, DI, AI, RS‑485, Ethernet; ESPHome YAML well documented; Modbus master for ultrasonic level etc. |
| **Apollo / IoTorero / Athom “Made for ESPHome”** | Certified local devices; limited process depth |
| **Atlas Scientific Wi‑Fi Pool / Hydroponics kits** | pH/ORP/EC/RTD on ESP — flash ESPHome `ezo` |
| **Olimex ESP32-PoE + industrial sensors** | Tank level / remote plant rooms over Ethernet |

These are still “ESP devices,” but **you do not have to design hardware** — buy boards, attach transducers, ship ESPHome configs.

---

## 6. Deep dive by process application

### 6.1 Temperature

| Use case | Recommended HA-native approach |
|---|---|
| Room / cabinet ambient | Zigbee/Matter/Z-Wave/SwitchBot sensors |
| Pipe / tank surface or immersion (non-critical) | Shelly Add-on + DS18B20 **or** Sonoff TH + WTS01 **or** ESPHome |
| Process RTD PT100/PT1000, thermocouple | Modbus RTD module **or** ESP + MAX31865/analog transmitter (4–20 mA → ADC) |
| Multi-zone plant monitoring | Ecowitt outdoor + many Zigbee nodes; or KinCony + 1-Wire bus |

**Custom ESP needed?** Only when you need RTD/TC class accuracy, hazardous ratings, or long sensor runs with industrial transmitters.

### 6.2 Flow

| Use case | Approach |
|---|---|
| Whole-building water | Flo (cloud) or HomeWizard optical meter |
| Garden / softener / zone valve with meter | Sonoff SWV, FrankEver, Tuya ultrasonic valves (Z2M) |
| Inline pulse (YF-S201/DN40…) | WaterFlowKit or ESPHome `pulse_counter` |
| Industrial mag/ultrasonic meter | Modbus (preferred) |

**Custom ESP needed?** For most *inline process* pulse or industrial protocols, yes (or Modbus gateway). Domestic shutoff/irrigation often no.

### 6.3 Pressure

| Use case | Approach |
|---|---|
| Domestic supply monitoring | Flo / Phyn |
| Light commercial water/gas line | EFEKTA Zigbee PST series (Z2M) |
| 0–10 V / 0–5 V transducer | Shelly Plus Add-on voltmeter/analog **or** ESP ADC |
| 4–20 mA loop | ESP + current sense / industrial Modbus transmitter |

**Custom ESP needed?** Frequently yes beyond domestic.

### 6.4 Level (tanks, sumps, reservoirs)

Commercial HA-native tank level products are essentially **absent**. Established patterns:

- Ultrasonic JSN-SR04T / AJ-SR04M → ESPHome (Wi‑Fi/PoE) or custom Zigbee ESP32-C6  
- Hydrostatic pressure transducer at tank bottom → ESPHome ADC  
- Modbus ultrasonic (e.g. A02-style) via KinCony RS‑485  

**Custom ESP (or Modbus) needed?** **Yes**, for practical deployments.

### 6.5 Pumps

| Pump type | Approach |
|---|---|
| On/off AC pump | Shelly/Sonoff relay sized for load + optional 1PM current as run proof |
| Dosing / irrigation micro pump | Apollo PUMP-1 |
| Contactor / starter with dry contact | frient IO Module outputs **or** Shelly dry contact |
| VFD / variable speed | Modbus RS‑485 via ESPHome (community examples for pool VSDs) or HA Modbus |

**Custom ESP needed?** For speed control and feedback (RPM, Hz, fault bits), yes.

### 6.6 Valves

| Valve type | Approach |
|---|---|
| Existing quarter-turn handle | Aqara Valve Controller T1 |
| Inline irrigation / DN15–25 smart valve | Sonoff SWV, Tuya/FrankEver/Nous, Grimsholm Matter |
| Whole-home motorized | Flo / Phyn |
| Industrial actuated ball/butterfly | Usually 24 V / 230 V actuator → Shelly/KinCony DO; position feedback → DI |

### 6.7 Chemistry & water quality

No meaningful WWHA / core catalog. Standard path: **Atlas Scientific EZO (pH/ORP/EC/RTD) + ESPHome**, optionally dosing pumps on GPIO/relays. Pool/hydroponics communities have mature YAML.

---

## 7. “Do we need to make our own ESP devices?”

### 7.1 You can avoid designing ESP hardware when…

- Monitoring rooms, cabinets, leaks, soil, outdoor weather  
- Switching pumps/valves on/off with power metering  
- Domestic water shutoff / irrigation valves with flow  
- Probe temps with DS18B20-class sensors (Shelly Add-on / Sonoff TH)  
- Reading **Modbus** instruments (use HA Modbus or a bought ESP/KinCony/Shelly Pro gateway — no custom PCB)

### 7.2 You should plan ESPHome (or Modbus gateway) devices when…

| Requirement | Why COTS HA wireless fails |
|---|---|
| Continuous tank level | No solid commercial HA product |
| 4–20 mA / PT100 / thermocouple | Almost no Zigbee/Z-Wave/Matter transmitters |
| Inline process flowmeters (non-pulse DIY) | Industrial meters speak Modbus/HART, not HA radio |
| VFD / multi-register pump drives | Need RS‑485 client logic |
| pH/ORP/EC control loops | Lab hardware + MCU only |
| High DI/DO count in a panel | frient is 4/2; denser → KinCony/PLC |
| Deterministic scan times / PLC semantics | Consumer mesh is event-driven, not scan-cycle |

### 7.3 Recommended architecture for PLCAssistant

```text
                    ┌─────────────────────────┐
                    │     Home Assistant      │
                    │  (+ PLCAssistant logic) │
                    └───────────┬─────────────┘
           ┌────────────┬───────┼────────┬──────────────┐
           │            │       │        │              │
      Zigbee/ZWave   Matter  Shelly/   Modbus TCP    ESPHome
      ambient/leak   valves  Wi‑Fi I/O  industrial    custom I/O
      irrigation             probes     meters/VFDs   level/pH/
                             relays                   RS‑485 edge
```

**Buy** for ambient, safety, and domestic water.  
**Gateway** (Shelly Pro Modbus / KinCony / ESP32) for industrial buses.  
**Build ESP nodes** only where no Modbus instrument and no Shelly-class I/O covers the signal.

---

## 8. Notable references

| Resource | URL |
|---|---|
| Works with Home Assistant catalog | https://works-with.home-assistant.io/certified-products/ |
| Matter integration (valve/pump platforms) | https://www.home-assistant.io/integrations/matter |
| Shelly integration | https://www.home-assistant.io/integrations/shelly |
| Modbus integration | https://www.home-assistant.io/integrations/modbus |
| Ecowitt integration | https://www.home-assistant.io/integrations/ecowitt |
| Flo integration | https://www.home-assistant.io/integrations/flo |
| Zigbee2MQTT device DB (valves, EFEKTA, …) | https://www.zigbee2mqtt.io/supported-devices/ |
| Apollo Automation | https://apolloautomation.com/ |
| Shelly Plus Add-on | https://www.shelly.com/products/shelly-plus-add-on |
| Shelly Pro Modbus Add-on | https://www.shelly.com/products/shelly-pro-modbus-add-on-rs485 |
| frient IO Module | https://www.frient.com/products/io-module |
| ESPHome EZO (Atlas) | https://esphome.io/components/sensor/ezo.html |
| KinCony ESP32 HA boards | https://www.kincony.com/ |

---

## 9. Conclusions for PLCAssistant

1. **Options already exist** for a large fraction of “process-adjacent” HA work: temperature/humidity, leaks, relays, irrigation/shutoff valves, soil moisture, domestic flow/pressure (Flo), optical water meters, light probe temps.  
2. **The catalog collapses** for classical process instrumentation (level, 4–20 mA, RTD, industrial flow, VFD). Those signals are not missing from HA *software* — they are missing as *wireless consumer SKUs*.  
3. **You do not need to invent a new radio stack.** Prefer: Shelly/ESPHome/KinCony edge + Modbus field devices + Zigbee/Matter for ambient/valves.  
4. **Custom ESP devices are justified** as *I/O adapters* (pulse flow, ultrasonic level, EZO chemistry, RS‑485 masters), not as replacements for every sensor. Buying ESP-ready commercial boards often beats designing PCBs.  
5. **Practical buy-vs-build rule:** if the physical sensor already speaks **Modbus** or outputs **pulse / 0–10 V / 1-Wire**, buy a gateway (HA Modbus, Shelly, KinCony, ESPHome). If it only has raw analog/digital pins and no commercial HA host, design or assemble an ESP node.

---

## 10. Suggested follow-ups

- Maintain a short **approved BOM** per signal type (ambient vs process) once target plant scenarios are fixed.  
- Prototype one **Modbus path** and one **ESPHome pulse/level path** as reference designs for PLCAssistant docs.  
- Track Matter **Pump/Valve** device availability — likely to improve for irrigation/water, not industrial process, in the near term.  
- Prefer **WWHA / core local** products for anything in safety shutoff loops; treat cloud-only (Flo) as optional convenience, not sole control path.
