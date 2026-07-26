# Research: HA-native sensors & actuators for process applications

**Project:** [PLCAssistant](https://github.com/marcuskrogh/PLCAssistant) (virtual PLC for Home Assistant)  
**Date:** 2026-07-26 (updated)  
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

**Bottom line:** Buy for ambient, safety, and domestic water. Use Modbus or ESPHome/KinCony/Shelly gateways for classical process instrumentation. Custom ESP is justified as an *I/O adapter*, not as a replacement for every sensor.

---

## 2. What “natively integrates with HA” means

| Integration path | Local? | Reference |
|---|---|---|
| [Works with Home Assistant](https://works-with.home-assistant.io/certified-products/) certified | Yes (required) | Tested by HA team |
| Core integrations (Shelly, Matter, ZHA, Z-Wave JS, Ecowitt, Flo, Modbus, ESPHome, …) | Usually local | First-class UI |
| [Zigbee2MQTT](https://www.zigbee2mqtt.io/supported-devices/) / ZHA supported | Local | Z2M often broader for Tuya/EFEKTA |
| ESPHome native API | Local | [Made for ESPHome](https://esphome.io/) commercial hardware |
| Official vendor cloud integration in core | Cloud | e.g. [Flo](https://www.home-assistant.io/integrations/flo) |

**Excluded as primary recommendations:** devices that only work via undocumented cloud APIs or unstable reverse-engineered HACS components (mentioned only when no better option exists).

---

## 3. Protocol landscape

| Protocol | HA path | Strength for process | Weakness |
|---|---|---|---|
| Wi‑Fi / Ethernet | [Shelly](https://www.home-assistant.io/integrations/shelly), [ESPHome](https://esphome.io/), [Ecowitt](https://www.home-assistant.io/integrations/ecowitt), [HomeWizard](https://www.home-assistant.io/integrations/homewizard) | Probes, ADC, Ethernet, power metering | Power / AP dependency |
| Zigbee | [ZHA](https://www.home-assistant.io/integrations/zha) / [Zigbee2MQTT](https://www.zigbee2mqtt.io/) | Huge sensor + valve catalog, mesh | Few industrial transducers |
| Z‑Wave | [Z-Wave JS](https://www.home-assistant.io/integrations/zwave_js/) | Reliable mesh, strong EU/US base | Thin process instrumentation catalog |
| Matter / Thread | [Matter](https://www.home-assistant.io/integrations/matter) | Valve/pump domains ready in HA | Few process instruments commercially |
| Bluetooth | [SwitchBot](https://www.home-assistant.io/integrations/switchbot), BTHome | Cheap meters | Range / polling |
| Modbus TCP/RTU | [Modbus](https://www.home-assistant.io/integrations/modbus) | *De facto* industrial bus | Config work, not “pair and play” |
| MQTT | [MQTT](https://www.home-assistant.io/integrations/mqtt) | Flexible for gateways | You own the schema |

---

## 4. Temperature sensors

### 4.1 Ambient air temperature & humidity

#### [SONOFF SNZB-02D](https://sonoff.tech/en-us/products/sonoff-snzb-02d-zigbee-lcd-smart-temperature-humidity-sensor) — Zigbee LCD climate sensor
- **Protocol:** Zigbee 3.0  
- **HA path:** [ZHA](https://www.home-assistant.io/integrations/zha) or [Zigbee2MQTT](https://www.zigbee2mqtt.io/) (local; no Sonoff hub required with a dongle)  
- **Docs:** [help.sonoff.tech/docs/snzb-02d](https://help.sonoff.tech/docs/snzb-02d)  
- **Exposes:** Temperature, humidity, battery; on-device LCD  
- **Specs (typical):** ±0.2 °C / ±2% RH; CR2450; ~5 s refresh when awake  
- **Process fit:** Room/cabinet ambient monitoring; good for HVAC interlocks, not media temperature  
- **Notes:** Prefer ZHA/Z2M over eWeLink cloud for local process control

#### [Aqara Climate Sensor W100](https://www.aqara.com/en/product/climate-sensor-w100/) — Matter/Thread climate
- **Protocol:** Matter over Thread (also Zigbee variants in Aqara line)  
- **HA path:** [Matter](https://www.home-assistant.io/integrations/matter) (WWHA certified)  
- **Catalog:** [Works with HA listing](https://works-with.home-assistant.io/certified-products/)  
- **Exposes:** Temperature, humidity; display; can act as HVAC remote in Aqara ecosystem  
- **Process fit:** Ambient only; Thread mesh is good for plant rooms with border routers

#### [Aqara Temperature and Humidity Sensor T1](https://www.aqara.com/en/product/temperature-humidity-sensor-t1/) (WSDCGQ12LM)
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA / [Zigbee2MQTT WSDCGQ12LM](https://www.zigbee2mqtt.io/devices/WSDCGQ12LM.html)  
- **Exposes:** Temperature, humidity, **atmospheric pressure**, battery  
- **Process fit:** Ambient + barometric; Z2M more reliable for pressure than ZHA historically  
- **Notes:** Also available via Aqara Matter bridge (pressure may not pass through Matter)

#### [Apollo Automation TEMP-1](https://apolloautomation.com/products/temp-1) — ESPHome temp/humidity
- **Protocol:** Wi‑Fi (ESPHome)  
- **HA path:** Native ESPHome API; [WWHA certified](https://works-with.home-assistant.io/certified-products/)  
- **Exposes:** Temperature, humidity (and device diagnostics)  
- **Process fit:** Local-first ambient; open firmware for customization  
- **Notes:** Open Home Foundation commercial partner; Made for ESPHome

#### [Shelly H&T Gen3](https://www.shelly.com/products/shelly-h-t-gen3) — Wi‑Fi climate
- **Protocol:** Wi‑Fi  
- **HA path:** [Shelly integration](https://www.home-assistant.io/integrations/shelly) (local, auto-discovery)  
- **Exposes:** Temperature, humidity; e-paper display on Gen3  
- **Process fit:** Ambient monitoring with local control; battery or USB depending on model

#### [SwitchBot Meter / Meter Pro](https://www.switch-bot.com/products/switchbot-meter) — Bluetooth climate
- **Protocol:** Bluetooth (Meter Pro CO2 adds CO₂)  
- **HA path:** [SwitchBot](https://www.home-assistant.io/integrations/switchbot); WWHA for several Meter SKUs  
- **Product links:** [Meter](https://www.switch-bot.com/products/switchbot-meter), [Meter Pro](https://www.switch-bot.com/products/switchbot-meter-pro), [Meter Pro CO2](https://www.switch-bot.com/products/switchbot-meter-pro-co2-monitor), [Indoor/Outdoor Thermo-Hygrometer](https://www.switch-bot.com/products/switchbot-indoor-outdoor-thermo-hygrometer)  
- **Process fit:** Retrofit ambient; limited for always-on plant control loops (BLE range/polling)

#### [Eve Weather](https://www.evehome.com/en/eve-weather) — Matter outdoor weather
- **Protocol:** Matter over Thread  
- **HA path:** Matter; WWHA  
- **Exposes:** Temperature, humidity, pressure (outdoor-rated)  
- **Process fit:** Outdoor ambient / weather compensation for irrigation

#### [frient Smart Humidity Sensor](https://www.frient.com/products/smart-humidity-sensor) (HMSZB-110)
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA; [frient WWHA](https://www.home-assistant.io/integrations/frient/); [frient WWHA announcement](https://www.home-assistant.io/blog/2025/09/02/frient-joins-works-with-home-assistant/)  
- **Exposes:** Humidity (and related climate entities per ZHA)  
- **Process fit:** Indoor climate / moisture-risk rooms

#### [Sensative Strips Comfort](https://sensative.com/sensors/strips-zwave/comfort/) — Z-Wave ultra-thin temp + lux
- **Protocol:** Z-Wave Plus  
- **HA path:** [Z-Wave JS](https://www.home-assistant.io/integrations/zwave_js/)  
- **Exposes:** Temperature, ambient light; optional temp alarms  
- **Specs:** ~3 mm thick; −20 °C to +60 °C; up to ~10 year battery (claimed)  
- **Process fit:** Discrete cabinet/door mounting; outdoor-capable enclosure rating for ambient

### 4.2 Probe / media temperature (pipe, tank, immersion)

#### [Shelly Plus Add-on](https://www.shelly.com/products/shelly-plus-add-on) (+ DS18B20 probes)
- **Protocol:** Host is Wi‑Fi Shelly Plus/Gen3/Gen4  
- **HA path:** Entities appear on the host Shelly via [Shelly integration](https://www.home-assistant.io/integrations/shelly)  
- **Docs:** [Knowledge base](https://kb.shelly.cloud/knowledge-base/shelly-plus-add-on), [product docs](https://www.shelly.com/blogs/documentation/shelly-plus-add-on)  
- **Bundle option:** [Plus AddOn +1DS](https://www.shelly.com/products/shelly-plus-addon-1x-sensor-ds)  
- **I/O:** Up to **5× DS18B20** *or* 1× DHT22; digital input; analog 0–100%; voltmeter 0–10 V  
- **Compatible hosts:** Plus 1/1PM/2PM/i4/…, Gen3 1/1PM/2PM/EM/…, Gen4 1/1PM/2PM (see Shelly list)  
- **Process fit:** **Best commercial non-DIY path** for multi-probe pipe/tank DS18B20 temps + light analog transducers  
- **Limits:** Not PT100/TC; analog accuracy ~±5%; not isolated process 4–20 mA without a transmitter

#### [SONOFF TH Elite](https://sonoff.tech/en-us/products/sonoff-th-elite-smart-temperature-and-humidity-monitoring-switch) (THR316D / THR320D) + probes
- **Protocol:** Wi‑Fi (ESP32)  
- **HA path:** [eWeLink HA add-on](https://sonoff.tech/en-us/blogs/news/how-sonoff-works-with-home-assistant) (LAN preferred) or flash alternative firmware where supported  
- **Docs:** [THR316D/THR320D help](https://help.sonoff.tech/docs/thr316-20d)  
- **Sensors:** [THS01](https://sonoff.tech/) temp/humidity, **WTS01** waterproof temp (DS18B20-class), **MS01** soil moisture — RJ9, one sensor at a time; [RL560](https://sonoff.tech/) extension up to ~60 m (temp) / ~10 m (MS01)  
- **Actuation:** 16 A / 20 A load + dry contact (5–30 V, 1 A) for boilers/contactors  
- **Process fit:** Combined probe temp + high-load / dry-contact control (heater, pump starter)  
- **Notes:** Prefer local LAN mode; cloud is a fallback

#### [SONOFF SNZB-02LD](https://sonoff.tech/product/gateway-and-sensors/rf-bridger2/) IP65 Zigbee probe thermometer
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA / Zigbee2MQTT  
- **Product focus:** External probe + LCD; IP65-oriented outdoor/wet sensing  
- **Process fit:** Single-point media/outdoor probe without Wi‑Fi at the sensor

#### ESPHome + DS18B20 / MAX31865 (PT100) — DIY / commercial boards
- **HA path:** [ESPHome Dallas/1-Wire](https://esphome.io/components/sensor/dallas_temp.html), [MAX31865](https://esphome.io/components/sensor/max31865.html)  
- **Hardware examples:** [KinCony KC868](https://www.kincony.com/esp32-all-in-one-board-home-assistant.html) 1-Wire headers; any ESP32  
- **Process fit:** Required for **PT100/PT1000** and multi-drop industrial-ish probe buses when Shelly/Sonoff accuracy is insufficient

---

## 5. Humidity, soil moisture & related

#### [Ecowitt WH51](https://shop.ecowitt.com/products/wh51) — wireless soil moisture
- **Protocol:** Proprietary RF → Ecowitt Wi‑Fi/Ethernet gateway → HA  
- **Gateway:** [GW1200](https://shop.ecowitt.com/) / [GW2000](https://oss.ecowitt.net/uploads/20250320/GW2000.pdf) / [GW3000](https://shop.ecowitt.com/)  
- **HA path:** [Ecowitt integration](https://www.home-assistant.io/integrations/ecowitt) (local push; HTTP required)  
- **Exposes:** Soil moisture %, soil AD, battery; up to **16** WH51/WH51L per GW2000-class gateway  
- **Specs:** 0–100% moisture; ~70 s update; AA battery; IP66-oriented probe use  
- **Process fit:** Gardens, greenhouses, field beds — not laboratory soil analysis  
- **Notes:** Sensor cannot run alone; calibrate 0%/100% AD for soil type

#### [Apollo PLT-1 / PLT-1B](https://apolloautomation.com/products/plt-1) — plant multisensor
- **Protocol:** Wi‑Fi ESPHome  
- **HA path:** ESPHome API; WWHA  
- **Exposes:** Capacitive soil moisture, air temp/humidity (AHT20), LUX/UV (LTR390); optional DS18B20 soil temp; RGB + buzzer  
- **Process fit:** Indoor plant / small greenhouse automation with [PUMP-1](https://apolloautomation.com/products/pump-1-fluid-pump)

#### [EFEKTA PWS Max Pro](https://www.zigbee2mqtt.io/devices/EFEKTA_PWS_MaxPro.html) / [zFlora ProMax](https://www.zigbee2mqtt.io/devices/zFlora_ProMax.html)
- **Protocol:** Zigbee  
- **HA path:** Prefer [Zigbee2MQTT](https://www.zigbee2mqtt.io/)  
- **Exposes:** Soil moisture %, temp, humidity, illuminance, battery; configurable intervals / offsets  
- **Process fit:** Battery Zigbee plant watering sensors; niche vendor, strong Z2M support

#### [SONOFF MS01](https://sonoff.tech/en-us/products/sonoff-th-elite-smart-temperature-and-humidity-monitoring-switch) (via TH Elite)
- **Protocol:** Wired to TH Elite (Wi‑Fi)  
- **HA path:** Same as TH Elite  
- **Process fit:** Single soil channel tied to a switched load (irrigation relay)

---

## 6. Leak / flood / binary water presence

#### [SONOFF SNZB-05P](https://sonoff.tech/en-us/products/sonoff-zigbee-water-leak-sensor-snzb-05p)
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA / Zigbee2MQTT; [docs](https://help.sonoff.tech/docs/snzb-05p)  
- **Features:** Detects ~0.5 mm liquid; concave drip design; optional leak cables in series; ~5 year battery claim  
- **Process fit:** Point leak detection under plant equipment, heaters, sumps  
- **Automation:** Pair with valve actuators for shutoff

#### [frient Water Leak Detector](https://www.frient.com/products/water-leak-detector) / [Probe version](https://www.frient.com/products/water-leak-detector)
- **Models:** FLSZB-110 / FLAPR-110  
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA; WWHA  
- **Process fit:** Certified local leak binary sensors for EU/US

#### [Zooz ZSE42](https://www.getzooz.com/zooz-zse42-water-leak-xs-sensor/) — Z-Wave XS leak
- **Protocol:** Z-Wave 800 / Long Range ready  
- **HA path:** Z-Wave JS  
- **Buy/docs:** [getzooz.com](https://www.getzooz.com/zooz-zse42-water-leak-xs-sensor/), [Smartest House](https://www.thesmartesthouse.com/products/zooz-z-wave-plus-700-series-xs-water-leak-sensor-zse42)  
- **Features:** Ultra-small; sealed cover (IP66 splash-oriented); CR2450  
- **Process fit:** Tight spaces under boilers / manifolds

#### [Aeotec Water Sensor 7 Pro](https://aeotec.com/) (ZWA019)
- **Protocol:** Z-Wave Plus V2 (700)  
- **HA path:** Z-Wave JS  
- **Retail/docs:** [Pi Hut](https://thepihut.com/products/aeotec-z-wave-water-sensor-7-pro), [manual overview](https://aeotec.freshdesk.com/support/solutions/articles/6000235950-water-sensor-7-pro-user-guide-zwa019-)  
- **Exposes:** Leak (probe), temperature (−10…65 °C typ.), humidity, battery  
- **Process fit:** Leak + local climate in one node; can also monitor “dry” (low level) use cases

#### [SwitchBot Leak Detector](https://www.switch-bot.com/products/switchbot-water-leak-detector)
- **Protocol:** Bluetooth  
- **HA path:** SwitchBot integration; WWHA  
- **Process fit:** Small residential leaks; not ideal as sole industrial safety sensor

#### [Heiman Water Leak Sensor](https://www.heimantech.com/product/smart-water-leakage-detector-l1-series) (L1-M Matter)
- **Protocol:** Matter over Thread  
- **HA path:** Matter; WWHA  
- **Process fit:** Matter-native leak binary for Thread fabrics

#### [Sensative Strips Drip](https://sensative.com/sensors/strips-zwave/)
- **Protocol:** Z-Wave  
- **HA path:** Z-Wave JS  
- **Process fit:** Ultra-thin leak + temperature under fixtures

#### [Shelly Flood](https://www.shelly.com/) (Wi‑Fi flood)
- **Protocol:** Wi‑Fi  
- **HA path:** Shelly integration  
- **Process fit:** Local Wi‑Fi flood binary; pair with Shelly relays/valves

#### Ecowitt WH55 leak (via Ecowitt gateway)
- **HA path:** [Ecowitt](https://www.home-assistant.io/integrations/ecowitt)  
- **Gateway PDF lists WH55:** [GW2000 manual](https://oss.ecowitt.net/uploads/20250320/GW2000.pdf)  
- **Process fit:** Multi-point outdoor/indoor leak via Ecowitt RF

---

## 7. Flow & water consumption

#### [Flo by Moen Smart Water Shutoff](https://shop.moen.com/pages/flo-smart-water-monitor)
- **Protocol:** Wi‑Fi (vendor cloud)  
- **HA path:** Core [Flo integration](https://www.home-assistant.io/integrations/flo) (cloud polling)  
- **Help:** [Moen Flo help center](https://solutions.moen.com/Smart_Water_Security_Products/Help_Center/Flo_Smart_Water_Monitor_and_Shutoff)  
- **Exposes in HA:** Flow rate, water pressure, temperature, daily consumption, alerts (binary), valve switch; actions for health test / home / away / sleep  
- **Process fit:** Whole-home / facility main line monitoring + shutoff  
- **Caveat:** **Not local-first** — unsuitable as sole safety path without a local backup valve

#### [HomeWizard Watermeter](https://www.homewizard.com/watermeter/) (HWE-WTR)
- **Protocol:** Wi‑Fi  
- **HA path:** [HomeWizard](https://www.home-assistant.io/integrations/homewizard); WWHA  
- **Function:** Optical reader for many mechanical meters (Zenner, Sensus, Itron, Elster, Diehl, …)  
- **Power:** USB-C for live readings; battery mode ≈ 4×/day  
- **Process fit:** Facility consumption accounting without cutting pipe  
- **Limits:** Reads existing meter; not an inline process flowmeter

#### [SONOFF SWV](https://sonoff.tech/en-us/products/sonoff-zigbee-smart-water-valve) (SWV-BSP / SWV-NH)
- **Protocol:** Zigbee 3.0  
- **HA path:** ZHA / [Zigbee2MQTT SWV](https://www.zigbee2mqtt.io/devices/SWV.html); [docs](https://help.sonoff.tech/docs/swv-bsp-nh)  
- **Exposes (Z2M):** Valve switch, **flow** (m³/h), irrigation cycles (timed/quantitative), battery, water shortage/leakage status, daily volume, work state  
- **Specs:** IP55; 0.06–0.8 MPa; 4×AA; hose-faucet install  
- **Process fit:** Garden/zone irrigation with flow telemetry — not industrial mag meters

#### [SONOFF Hydro ONE](https://sonoff.tech/en-eu/products/sonoff-hydro-series-hydro-one-zigbee-smart-water-valve-swv-zfu-swv-zfe) (SWV-ZFU/ZFE)
- **Protocol:** Zigbee 3.0 (+ proximity/local mode)  
- **HA path:** Zigbee coordinator (ZHA/Z2M); marketed for HA  
- **Features:** Built-in **flow meter**, brass inlet, schedules, weather skip, usage reports  
- **Process fit:** Next-gen Sonoff irrigation valve with flow; region threads NH vs BSP

#### [FrankEver FK-BV05](https://www.zigbee2mqtt.io/devices/FK-BV05.html)
- **Protocol:** Zigbee (Tuya family)  
- **HA path:** **Zigbee2MQTT recommended**  
- **Exposes:** Valve + position/threshold, **water temperature**, consumed last/total, leakage state, irrigation schedules, volume/temp alarms  
- **Process fit:** Softener/irrigation valve with richer telemetry than basic on/off valves

#### [Nous L14](https://www.zigbee2mqtt.io/devices/L14.html)
- **Protocol:** Zigbee  
- **HA path:** Zigbee2MQTT  
- **Exposes:** Valve, flow switch, water current/total, quantitative watering, faults, battery  
- **Process fit:** Similar garden/zone water valve class

#### [Tuya TS0601 ultrasonic water meter valve](https://www.zigbee2mqtt.io/devices/TS0601_water_valve.html)
- **Protocol:** Zigbee  
- **HA path:** Zigbee2MQTT  
- **Exposes:** Valve, flow_rate (L/h), water_consumed, daily/month consumption, temperature, faults  
- **Process fit:** Inline ultrasonic domestic meter+valve; verify thread/size before purchase

#### [SmartHomeShop WaterFlowKit](https://github.com/smarthomeshop/waterflowkit)
- **Protocol:** Wi‑Fi / Ethernet (ESP32 / ESP32-C6), ESPHome  
- **HA path:** ESPHome API  
- **Function:** Multi-channel **pulse flow** (YF-series) + optional water temp; calibration in HA  
- **Process fit:** Closest turnkey commercial kit for DIY pulse flowmeters into HA  
- **When to use:** Borehole, transfer lines, non-smart pulse meters

#### ESPHome `pulse_counter` (DIY)
- **Docs:** [pulse_counter](https://esphome.io/components/sensor/pulse_counter.html)  
- **Community example:** [HA community flow meter thread](https://community.home-assistant.io/t/using-esphome-to-build-a-water-flow-rate-meter/119380)  
- **Process fit:** Any hall/pulse flow sensor (YF-DN40, etc.)

#### Industrial flowmeters (Modbus)
- **HA path:** [Modbus](https://www.home-assistant.io/integrations/modbus)  
- **Pattern:** Mag/ultrasonic meter with Modbus TCP/RTU → HA sensors  
- **Process fit:** **Preferred** for accurate process flow; no HA-native wireless industrial flow SKU

---

## 8. Pressure sensors

#### Flo / Phyn (domestic supply pressure)
- **Flo:** see §7 — pressure entity via cloud integration  
- **Phyn Plus:** no core integration; community options  
  - Cloud HACS: [jordanruthe/homeassistant-phyn](https://github.com/jordanruthe/homeassistant-phyn)  
  - Local LAN: [rplankenhorn/ha-phyn-local](https://github.com/rplankenhorn/ha-phyn-local) (pressure, temp, flow, valve)  
- **Process fit:** Domestic main only; Phyn local path is better for LAN-only sites if maintained

#### [EFEKTA PST pressure monitors](https://www.zigbee2mqtt.io/devices/EFEKTA_PST_V1.html) (Zigbee)
- **Models (Z2M):**  
  - [EFEKTA_PST_V1](https://www.zigbee2mqtt.io/devices/EFEKTA_PST_V1.html)  
  - [EFEKTA_PST_V1_LR](https://www.zigbee2mqtt.io/devices/EFEKTA_PST_V1_LR.html)  
  - [EFEKTA_PST_POW_V2_LR](https://www.zigbee2mqtt.io/devices/EFEKTA_PST_POW_V2_LR.html)  
  - [EFEKTA_PST_POW_DUO_V2_LR](https://www.zigbee2mqtt.io/devices/EFEKTA_PST_POW_DUO_V2_LR.html)  
- **Protocol:** Zigbee (long-range variants available)  
- **HA path:** Zigbee2MQTT  
- **Exposes:** Pressure (kPa/bar/psi), temperature, offsets, battery/mains, configurable sensor ranges (e.g. 0–1 … 0–40 bar on POW V2)  
- **Process fit:** **Rare Zigbee line-pressure instrument** for water/gas — best off-the-shelf wireless option short of Modbus transmitters  
- **Vendor:** [EFEKTA](https://efektalab.com/) (verify current shop SKUs)

#### Shelly Plus Add-on + 0–10 V pressure transducer
- **Links:** [Plus Add-on](https://www.shelly.com/products/shelly-plus-add-on)  
- **Method:** Transducer voltage → Add-on voltmeter/analog % → template to bar/psi in HA  
- **Process fit:** Light commercial when transducer already outputs 0–5/0–10 V  
- **Limits:** Accuracy/isolation; community reports intermittent analog updates on some firmwares — validate before critical use

#### 4–20 mA / industrial pressure transmitters
- **HA path:** Modbus transmitter **or** ESP + current sense / signal conditioner  
- **Process fit:** Standard for plant pressure; **no** native Zigbee/Z-Wave/Matter industrial SKUs of note

---

## 9. Level (tanks, sumps, reservoirs)

**Finding:** There is essentially **no** strong turnkey WWHA/core product for continuous tank level. Practical paths:

#### Ecowitt LDS01 laser distance (via gateway)
- **Listed in** [GW2000 sensor table](https://oss.ecowitt.net/uploads/20250320/GW2000.pdf) (up to 4× LDS01)  
- **HA path:** Ecowitt integration (verify entity mapping for your HA version)  
- **Process fit:** Non-contact distance → template to %/volume; evaluate for your tank geometry

#### ESPHome ultrasonic (JSN-SR04T / AJ-SR04M)
- **Examples:** [Coroebus/HA-tank-level](https://github.com/Coroebus/HA-tank-level), [kane5432/ESP32-Water-Level-Sensor](https://github.com/kane5432/ESP32-Water-Level-Sensor)  
- **HA path:** ESPHome  
- **Process fit:** Rainwater / process tanks; PoE ESP32 helpful for buried pump houses

#### Hydrostatic pressure at tank bottom
- **Example write-up:** [Solar-powered tank monitor](https://jrattechworks.com/tank-level-pressure-sensor/)  
- **HA path:** ESPHome ADC  
- **Process fit:** Often more stable than ultrasonic in sealed tanks

#### Modbus ultrasonic level transmitters
- **Example pattern:** KinCony RS‑485 + Modbus distance sensor ([forum example](https://www.kincony.com/forum/showthread.php?tid=3514))  
- **HA path:** ESPHome `modbus_controller` or HA Modbus  
- **Process fit:** Preferred industrial approach

#### DIY Zigbee ultrasonic
- **Example:** [esp32c6_zigbee_ultrasonic_distance_sensor](https://github.com/Aralox/esp32c6_zigbee_ultrasonic_distance_sensor) + Z2M external converter  
- **Process fit:** When Wi‑Fi is unavailable at the tank

**Custom ESP / Modbus needed?** **Yes**, for almost all continuous level deployments.

---

## 10. Valves (actuators)

#### [Aqara Valve Controller T1](https://www.aqara.com/en/product/valve-controller-t1/) (VC-X01E/D)
- **Protocol:** Zigbee 3.0; Matter-over-bridge via Aqara hub  
- **HA path:** ZHA/Z2M direct Zigbee **or** Matter via bridge; [WWHA](https://works-with.home-assistant.io/certified-products/); [US page](https://www.aqara.com/us/product/valve-controller-t1/), [EU shop](https://eu.aqara.com/en-eu/products/aqara-valve-controller-t1)  
- **Function:** Motorizes existing **lever/butterfly** handles on DN15/DN20/DN25 valves (no pipe cut)  
- **Power:** 4×AA; ~2 year claim; torque ≤3.6 N·m; indoor only  
- **Process fit:** Main shutoff retrofit + leak-sensor automations  
- **Limits:** Not for round handwheels; not outdoor/IP-rated plant use

#### SONOFF SWV / Hydro ONE — see §7
- Inline/hose irrigation valves with optional flow

#### [Grimsholm Smart Irrigation Valve](https://www.grimsholm.com/grimsholm-smart-irrigation-valve?language=en)
- **Protocol:** Matter over Thread  
- **Claims:** Flow measurement, freeze/leak detection, compact outdoor valve  
- **HA path:** Matter (verify availability/region)  
- **Process fit:** Matter-native irrigation; early catalog product — validate before bulk buy

#### FrankEver / Nous / Tuya valves — see §7
- Prefer Zigbee2MQTT; good flow/temp telemetry on higher-end SKUs

#### Shelly Gas + Valve add-on
- **HA docs:** [Shelly Gas valve entities](https://www.home-assistant.io/integrations/shelly)  
- **Process fit:** Gas safety shutoff when using Shelly Gas with valve accessory

#### Flo / Phyn whole-home shutoff — see §7–8

#### Industrial actuated valves
- **Pattern:** 24 V/230 V actuator → [Shelly](https://www.shelly.com/products/shelly-1pm-gen3) / KinCony DO; limit switches → DI (frient IO / Shelly input / KinCony)  
- **HA path:** Switch/valve template entities  
- **Process fit:** Standard panel approach when smart valves don’t meet size/pressure ratings

---

## 11. Pumps & motor loads

#### [Apollo PUMP-1 Fluid Pump](https://apolloautomation.com/products/pump-1-fluid-pump)
- **Protocol:** Wi‑Fi ESP32-C6, ESPHome  
- **HA path:** ESPHome; WWHA (Irrigation)  
- **Specs (vendor):** ~900 ml/min; ~14 ft vertical / ~33 ft horizontal claim; food-safe materials  
- **Process fit:** Dosing / plant watering / aquarium top-off — **not** process transfer pumps  
- **Pairs with:** [PLT-1](https://apolloautomation.com/products/plt-1)

#### [Shelly 1PM Gen3](https://www.shelly.com/products/shelly-1pm-gen3) / [Plus 1PM](https://www.shelly.com/) / Pro relays
- **Protocol:** Wi‑Fi (Matter on some Gen3/4)  
- **HA path:** Shelly integration  
- **Function:** On/off control + **power metering** (run proof, dry-run detection heuristics)  
- **Add-on:** Combine with [Plus Add-on](https://www.shelly.com/products/shelly-plus-add-on) for water temp while controlling a heater/pump  
- **Process fit:** Single-phase pumps within device current rating; use contactors for larger motors  
- **DIN:** Shelly Pro 1/1PM/2 for panel mounts

#### [Shelly Wave / Wave Pro](https://www.shelly.com/products/shelly-wave-pro-1-pm) (Z-Wave)
- **HA path:** Z-Wave JS; several WWHA  
- **Process fit:** Same relay roles on Z-Wave mesh (useful where Wi‑Fi is poor)

#### [frient IO Module](https://www.frient.com/products/io-module) (IOMZB-110)
- **Protocol:** Zigbee 3.0 router  
- **HA path:** ZHA; WWHA — first certified Zigbee low-voltage I/O module in the program  
- **I/O:** **4×** dry-contact inputs; **2×** isolated NO/NC outputs (max 30 V / 1 A); 5–28 VDC or micro-USB  
- **Process fit:** Drive contactors/starters with external relays; read float switches, pressure switches, run contacts  
- **Limits:** Not for direct mains motor switching

#### VFD / variable-speed pumps
- **No turnkey HA wireless VFD**  
- **Pattern:** RS‑485 Modbus → ESPHome ([example pool VSD project](https://github.com/htilly/ha-esp32-variable-speed-drive-esphome)) or HA Modbus  
- **Shelly bridge:** [Pro Modbus Add-on RS485](https://www.shelly.com/products/shelly-pro-modbus-add-on-rs485) on Pro EM/1/2 as Modbus client  
- **Process fit:** Required for RPM/Hz/fault feedback and speed setpoints

---

## 12. Digital & analog I/O gateways (PLC-adjacent)

#### [frient IO Module](https://www.frient.com/products/io-module) — see §11
- Best **certified Zigbee** DI/DO brick for dry contacts

#### [Shelly Plus Add-on](https://www.shelly.com/products/shelly-plus-add-on) — see §4.2
- 1-Wire + DI + analog% + 0–10 V on existing Shelly hosts

#### [Shelly Pro Modbus Add-on RS485](https://www.shelly.com/products/shelly-pro-modbus-add-on-rs485)
- **Hosts:** Pro EM-50, Pro 3EM, Pro 1, Pro 2  
- **Docs:** [Pro Modbus documentation](https://www.shelly.com/blogs/documentation/shelly-pro-modbus-add-on)  
- **Modes:** Modbus **client** (read meters/HVAC/PLC) or **server** (expose Shelly data)  
- **Bus:** RS‑485, up to 32 nodes (vendor claim)  
- **HA path:** Data surfaces via Shelly integration / device MQTT/RPC as implemented  
- **Process fit:** Commercial bridge from Shelly panels into Modbus field devices without a custom ESP

#### [KinCony KC868 series](https://www.kincony.com/esp32-all-in-one-board-home-assistant.html)
- **Examples:** [KC868-A8v3](https://shop.kincony.com/products/kc868-a8v3-esp32-s3-8-channel-relay-module), [KC868-A16 ESPHome device page](https://github.com/esphome/esphome-devices/blob/main/src/docs/devices/KinCony-KC868-A16/index.md), [KC868-AIO](https://www.kincony.com/esp32-all-in-one-board-home-assistant.html)  
- **I/O:** Multi-channel relays, DI, AI, AO (AIO), RS‑485, Ethernet, Wi‑Fi  
- **HA path:** ESPHome (recommended) or KinCony KCS MQTT discovery  
- **Process fit:** DIN-rail “poor man’s PLC I/O” with native HA; pair AI with 0–10 V / 4–20 mA transmitters  
- **Notes:** Industrial-ish form factor, not SIL/ATEX; still ESP-class reliability expectations

#### HA core [Modbus](https://www.home-assistant.io/integrations/modbus)
- **Transports:** TCP, RTU-over-TCP, serial RS‑485  
- **Entities:** sensors, binary sensors, switches, climates, lights, fans, etc.  
- **Process fit:** Direct map of industrial registers; use Ethernet Modbus gateways (e.g. Waveshare) for remote panels  
- **UX helper:** Community [Modbus Wizard](https://github.com/partach/ha_modbus_wizard) (HACS) for UI register mapping

---

## 13. Chemistry (pH, ORP, EC) & water quality

#### [Atlas Scientific EZO circuits](https://atlas-scientific.com/) + ESPHome
- **Components:** [ESPHome EZO sensor](https://esphome.io/components/sensor/ezo.html)  
- **Kits:** [Wi‑Fi Pool Kit](https://atlas-scientific.com/kits/), [Wi‑Fi Hydroponics Kit](https://atlas-scientific.com/kits/wi-fi-hydroponics-kit/)  
- **Typical exposes:** pH (I²C addr 99), ORP (98), EC (100), RTD (102) — verify addresses  
- **Community:** [HA hydroponics YAML](https://community.home-assistant.io/t/atlas-scientific-wi-fi-hydroponics-kit-example-yaml/538083), [pool automation project](https://github.com/stefanh12/Atlas-Scientific-Pool-Automation)  
- **Process fit:** Pools, hydroponics, light process water — **only practical HA-native chemistry path**  
- **Custom ESP?** Flash ESPHome onto kit ESP or your own ESP32; no WWHA chemistry SKU exists

#### [Apollo AIR-1](https://apolloautomation.com/products/air-1) / AirGradient
- **AIR-1:** [apolloautomation.com/products/air-1](https://apolloautomation.com/products/air-1)  
- **AirGradient:** [Indoor](https://www.airgradient.com/indoor/), [Outdoor](https://www.airgradient.com/outdoor/); WWHA Wi‑Fi  
- **Process fit:** Ambient air quality (CO₂/PM), not liquid chemistry

---

## 14. Energy / soft sensors (pump & process proxies)

#### Shelly EM / Pro 3EM / 1PM families
- **Links:** [Shelly 1PM Gen3](https://www.shelly.com/products/shelly-1pm-gen3), Pro EM lines on [shelly.com](https://www.shelly.com/)  
- **HA path:** Shelly integration  
- **Process fit:** Infer pump run, detect seized loads, allocate energy to process trains

#### [HomeWizard](https://www.homewizard.com/) P1 / kWh meters
- **P1 Meter:** [homewizard.com/p1-meter](https://www.homewizard.com/p1-meter/)  
- **kWh Meter:** [homewizard.com/kwh-meter](https://www.homewizard.com/kwh-meter/)  
- **HA path:** HomeWizard; WWHA  
- **Process fit:** Facility energy context alongside water

#### [frient Electricity Meter Interface 2 LED](https://www.frient.com/products/electricity-meter-interface-2-led) (EMIZB-141)
- **Protocol:** Zigbee  
- **HA path:** ZHA; WWHA  
- **Process fit:** Pulse/LED meter interface for legacy meters

---

## 15. Capability matrix (summary)

| Signal / actuator | Strong buy options (linked above) | ESP/Modbus still needed? |
|---|---|---|
| Ambient T/H | Sonoff SNZB-02D, Aqara, Apollo TEMP-1, Shelly H&T, Eve, SwitchBot | No |
| Probe T (DS18B20) | Shelly Plus Add-on, Sonoff TH + WTS01, SNZB-02LD | PT100 → yes |
| Soil moisture | Ecowitt WH51, Apollo PLT-1, EFEKTA, Sonoff MS01 | Lab-grade → yes |
| Leak | Sonoff SNZB-05P, frient, Zooz, Aeotec, Heiman, SwitchBot | No |
| Flow (domestic) | Flo, HomeWizard, Sonoff SWV/Hydro, FrankEver, WaterFlowKit | Industrial mag → Modbus |
| Pressure | Flo/Phyn, EFEKTA PST, Shelly+0–10 V | 4–20 mA → yes |
| Level | Ecowitt LDS01 (limited), else DIY | **Yes** almost always |
| Valves | Aqara T1, Sonoff SWV, Grimsholm, Tuya/FrankEver, Flo | Industrial actuators → DO |
| Dosing pump | Apollo PUMP-1 | Process pumps → VFD/Modbus |
| DI/DO | frient IO, Shelly, KinCony | High density → KinCony/PLC |
| pH/ORP/EC | Atlas + ESPHome only | **Yes** |
| VFD / RPM | — | **Yes** (Modbus/ESP) |

---

## 16. Recommended architecture for PLCAssistant

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

| Layer | Prefer |
|---|---|
| Ambient + leak + garden valves | Zigbee/Z-Wave/Matter COTS (linked in §§4–7, 10) |
| Probe temp + light analog + relays | Shelly (+ Add-on) |
| Facility water main | Flo (cloud) **plus** local valve backup if safety-critical |
| Industrial instruments | Modbus TCP/RTU → HA or Shelly Pro Modbus / KinCony / ESP gateway |
| Level, chemistry, pulse flow, VFDs | ESPHome adapters or Modbus field devices |

---

## 17. Do we need to make our own ESP devices?

### Avoid designing ESP hardware when…
- Monitoring rooms/cabinets, leaks, soil, outdoor weather  
- Switching pumps/valves with metering (Shelly/Sonoff/frient)  
- Domestic shutoff / irrigation with commercial smart valves  
- DS18B20-class probes via Shelly Add-on or Sonoff TH  
- Field devices already speak **Modbus** (use HA Modbus or a bought gateway)

### Plan ESPHome or Modbus gateways when…
| Requirement | Why COTS wireless fails |
|---|---|
| Continuous tank level | No solid commercial HA product |
| 4–20 mA / PT100 / thermocouple | Almost no mesh transmitters |
| Industrial flowmeters | Speak Modbus/HART, not HA radio |
| VFD multi-register control | Needs RS‑485 client |
| pH/ORP/EC loops | Lab hardware + MCU only |
| Dense panel DI/DO | frient is 4/2; denser → KinCony |

**Practical rule:** If the sensor speaks Modbus or outputs pulse / 0–10 V / 1-Wire, **buy a gateway**. If it only has raw pins and no commercial HA host, **assemble an ESP node** (prefer KinCony/Olimex/Atlas kits over custom PCBs).

---

## 18. Reference index (integrations & catalogs)

| Resource | URL |
|---|---|
| Works with Home Assistant products | https://works-with.home-assistant.io/certified-products/ |
| Matter integration | https://www.home-assistant.io/integrations/matter |
| Shelly integration | https://www.home-assistant.io/integrations/shelly |
| ZHA | https://www.home-assistant.io/integrations/zha |
| Z-Wave JS | https://www.home-assistant.io/integrations/zwave_js |
| Zigbee2MQTT devices | https://www.zigbee2mqtt.io/supported-devices/ |
| Modbus | https://www.home-assistant.io/integrations/modbus |
| Ecowitt | https://www.home-assistant.io/integrations/ecowitt |
| Flo | https://www.home-assistant.io/integrations/flo |
| HomeWizard | https://www.home-assistant.io/integrations/homewizard |
| frient (WWHA) | https://www.home-assistant.io/integrations/frient |
| ESPHome | https://esphome.io/ |
| Apollo Automation | https://apolloautomation.com/ |
| Shelly Plus Add-on | https://www.shelly.com/products/shelly-plus-add-on |
| Shelly Pro Modbus Add-on | https://www.shelly.com/products/shelly-pro-modbus-add-on-rs485 |
| KinCony | https://www.kincony.com/ |
| Atlas Scientific | https://atlas-scientific.com/ |
| Ecowitt shop | https://shop.ecowitt.com/ |
| Moen Flo | https://shop.moen.com/pages/flo-smart-water-monitor |
| HomeWizard Watermeter | https://www.homewizard.com/watermeter/ |
| Aqara Valve Controller T1 | https://www.aqara.com/en/product/valve-controller-t1/ |
| SONOFF SWV | https://sonoff.tech/en-us/products/sonoff-zigbee-smart-water-valve |
| SONOFF SNZB-05P | https://sonoff.tech/en-us/products/sonoff-zigbee-water-leak-sensor-snzb-05p |
| SONOFF TH Elite | https://sonoff.tech/en-us/products/sonoff-th-elite-smart-temperature-and-humidity-monitoring-switch |
| frient IO Module | https://www.frient.com/products/io-module |
| Zooz ZSE42 | https://www.getzooz.com/zooz-zse42-water-leak-xs-sensor/ |
| Grimsholm irrigation valve | https://www.grimsholm.com/grimsholm-smart-irrigation-valve?language=en |
| WaterFlowKit | https://github.com/smarthomeshop/waterflowkit |
| EFEKTA PST (Z2M) | https://www.zigbee2mqtt.io/devices/EFEKTA_PST_V1.html |

---

## 19. Suggested follow-ups

1. Freeze a **BOM per signal** for the first PLCAssistant reference plant (ambient vs process).  
2. Prototype **one Modbus path** (meter or VFD) and **one ESPHome path** (pulse flow or tank level).  
3. Prefer **WWHA / core local** devices on any shutoff/safety automation; treat Flo cloud as optional telemetry.  
4. Re-check Matter **Pump/Valve** SKUs periodically — irrigation is moving faster than industrial process instruments.
