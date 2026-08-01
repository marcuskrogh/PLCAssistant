# Research brief: Industrial PLC program organization & engineering UI capabilities

**Tracker:** [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179)  
**Story:** [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)  
**Prior context:** [SWD-173](https://marcusknielsen.atlassian.net/browse/SWD-173) (control recovered; App still shows empty program)  
**Date:** 2026-08-01  
**Tooling:** `scripts/arxiv_research.py` + WebSearch / WebFetch

## Question

What do **industrial PLC systems** expose for:

1. **Program organization** — how logic is structured (programs, tasks, blocks)
2. **Multiple concurrent programs / tasks** — how several runnable units coexist on one controller
3. **Engineering UI** — what the IDE shows for defined vs running logic, libraries, and equations
4. **Online / runtime capabilities** — monitoring, force/write, download/compare, active application

Scope: supportive evidence for `/explore` / `/define` on Soft-PLC App parity. This brief does **not** decide PLCAssistant product scope, UX, or acceptance.

## Axes covered

| Axis | Status | Notes |
|------|--------|-------|
| Preprints (arXiv) | covered | Strong on IEC 61131-3 languages / verification / complexity; weak on vendor IDE UX. Queries returned ~41–48 unique papers; few SoftPLC packaging hits. |
| Formal written | covered | IEC 61131-3 software model (via PLCopen / OPC UA mapping / ABB overview); Siemens S7 block docs; Rockwell Logix tasks PM; CODESYS Application/Task docs; Beckhoff TwinCAT monitoring docs |
| Web discovery | covered | IronPLC IEC model explainer; vendor help hubs; OpenPLC Runtime architecture |
| Informal / practitioner | covered | Automation.com IEC model; SolisPLC / Industrial Monitor Direct tutorials; OpenPLC forum multi-program setup; labeled informal |

## Search strategy

| Axis | Queries / targets |
|------|-------------------|
| Preprints | `IEC 61131` + program/task/POU/FB; soft-PLC / IEC 61499 programming; PLC + IDE/engineering; software-model / OpenPLC / PID cascade. Raw JSON: `/tmp/plc-ui-research/arxiv.json`, `arxiv2.json` (not committed). |
| Formal | [OPC UA PLC Info Model §4.1.1.3](https://reference.opcfoundation.org/specs/OPC-30000/4.1.1.3); [ABB IEC 61131 overview PDF](https://library.e.abb.com/public/c8e8874bd8bf42b78a685f86eb967588/DS_2101127-EN_AE_WEB.pdf); [Siemens code blocks](https://docs.tia.siemens.cloud/r/simatic_s7_1200_manual_collection_enus_20/plc-concepts/execution-of-the-user-program/code-blocks-for-structuring-your-program); [Rockwell Studio 5000 Tasks/Programs/Routines](https://www.rockwellautomation.com/en-us/docs/studio-5000-logix-designer/37-00/contents-ditamap/studio-5000-logix-designer/controller-organizer/use-the-controller-organizer/use-tasks--programs--and-routines.html) + [1756-PM005](https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm005_-en-p.pdf); [CODESYS Application](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_obj_application.html) / [Task Configuration](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_f_task_configuration.html); [TwinCAT monitoring](https://infosys.beckhoff.com/content/1033/tc3_plc_intro/2527669643.html); [CODESYS PID FB](https://content.helpme-codesys.com/en/libs/Util/Current/Controller/PID.html) |
| Web | IronPLC program organization; OpenPLC Runtime README / debug protocol; PLCopen FAQs |
| Informal | OpenPLC forum “two programs”; TIA online/force/cross-ref practitioner guides; TwinCAT task POU order notes |

## Executive summary (what the sources say)

Industrial controllers converge on a **hierarchical software model**, not a single flat diagram:

```text
Configuration / Project / Device
  └── Resource / CPU / Application(s)
        └── Task(s)  — cyclic | continuous/freewheeling | event
              └── Program instance(s) / scheduled programs
                    └── Function Blocks + Functions (+ data)
```

**Multiple programs (or program instances) running “at the same time”** is normal: they are scheduled by **tasks** with intervals and priorities. Concurrent execution is **scheduled / preemptive**, not “independent apps with no shared schedule.” Vendor UIs always expose a **project tree** (organizer) listing tasks → programs → routines/blocks, plus which application is **active** on the device.

**Library practice for PID:** vendor libraries ship a **generic PID/PI function block** (tunable gains, clamps, manual/reset). Application-specific loops (level vs flow) are **instances** of that FB with different parameters and wiring — not separate opaque library types with empty bodies. PI is typically PID with derivative term disabled (`TV=0` in CODESYS Util).

**Engineering UIs expose far more than offline edit:**

| Capability | What sources describe |
|------------|------------------------|
| Project / device tree | Tasks, programs, POUs, libraries, GVLs |
| Defined vs loaded | Download/login; compare offline project to PLC; list applications on device |
| Active application | Explicit “active application” (CODESYS); scheduled vs unscheduled programs (Logix) |
| Block / instance view | Open program / FB instance; pins, params, instance data |
| Algorithm visibility | ST/LD/FBD source or library docs with equations; not empty placeholders |
| Online monitoring | Inline values in editors; watch tables; Boolean line coloring |
| Write / force | Prepare & force values; force tables (with safety caveats) |
| Cross-reference | Where tags/blocks are used |
| Debug protocol (open) | OpenPLC: WebSocket variable poll + program hash identity |

Relative to that baseline, a Soft-PLC App that shows only a **library list** and an **empty program JSON** while control is running is **missing the primary industrial surface**: the **scheduled program(s)** that are actually defined/loaded/running, with inspectable block instances and configuration.

## Key sources

| Title | Axis | ID/URL | Relevance |
|-------|------|--------|-----------|
| IronPLC — Program Organization | Web | https://www.ironplc.com/explanation/program-organization.html | Clear CONFIGURATION→RESOURCE→TASK→PROGRAM layering |
| OPC UA for PLCs (IEC 61131-3) §4.1.1.3 | Formal | https://reference.opcfoundation.org/specs/OPC-30000/4.1.1.3 | Normative mapping of Ctrl Configuration/Resource/Task/Program |
| PLCopen / IEC Common Elements excerpt | Formal | PLCopen Common Elements (via plcopen.org download) | Configurations/resources start-stop; programs under tasks; global vars / access paths |
| ABB — Overview of IEC 61131 | Formal | ABB DS_2101127 PDF | Multi-resource, multi-task vs “one loop” conventional PLC |
| Siemens — Code blocks | Formal | Siemens TIA S7-1200 docs | OB / FC / FB / DB structuring; instance DBs |
| Rockwell — Tasks, Programs, Routines | Formal | Studio 5000 docs + 1756-PM005 | Continuous/periodic/event tasks; many programs per task |
| CODESYS — Application object | Formal | helpme-codesys.com Application | Multiple applications per device; active application; task config required |
| CODESYS — Task Configuration | Formal | helpme-codesys.com Task Configuration | Task types, priority, call list of programs |
| TwinCAT — Monitoring in Programming Objects | Formal | infosys.beckhoff.com | Inline monitoring, force/write, instance vs type view |
| CODESYS Util — PID FB | Formal | helpme-codesys.com PID | Generic PID; PI via `TV=0`; equation documented |
| OpenPLC Runtime architecture / DEBUG_PROTOCOL | Informal/Web | github.com/Autonomy-Logic/openplc-runtime | Editor↔runtime: load, start/stop, WebSocket monitor/force |
| OpenPLC forum — two programs | Informal | openplc.discussion.community | Same resource: multiple tasks + instances + globals |
| arXiv 2212.05918 | Preprints | arXiv:2212.05918 | Complexity of graphical+textual IEC software (structure matters) |
| arXiv 2410.15200 | Preprints | arXiv:2410.15200 | Graphic IEC languages still dominant in practice |

## Themes and trends

### 1. Software model: configuration → resource → task → program

Sources agree (IEC model, OPC UA Ctrl* types, IronPLC, ABB): **programs are scheduled by tasks**; tasks live under a resource/CPU; a configuration/device binds hardware. Conventional “one cyclic scan of one main” is a **degenerate** case of this model (PLCopen FAQ notes tools may hide the layers and auto-create one resource/one task/one program).

### 2. Multi-program is first-class

- **CODESYS:** multiple **Applications** under a device; each has Task Configuration; one is **active** for online work; device editor lists applications **on the PLC**.
- **Logix:** up to many **Tasks**; each schedules ordered **Programs**; programs contain **Routines**; unscheduled programs folder exists.
- **Siemens:** multiple **OBs** (cyclic, interrupt, startup) call FCs/FBs; structure is block-centric rather than “Application” named, but still multi-entry-point.
- **TwinCAT / OpenPLC:** multiple Program POUs assigned to tasks; OpenPLC: multiple instances/tasks under one resource.

### 3. What the engineering UI must show

Across vendors, the operator/engineer surface always includes:

1. **Navigator** of the runnable hierarchy (not only a block library)
2. Editors for **selected program / block instance** with **parameters and logic**
3. **Online connection** that overlays **live values** on that structure
4. **Identity of what is on the controller** (download, compare, application list, program hash)

Library browsers exist, but they are **not** the running system.

### 4. Library blocks vs instances

Industrial practice: **one generic controller FB** (PID/PI/P) in a library, **documented algorithm**, instantiated N times (level loop, flow loop) with different gains/clamps and wiring. Vendor docs publish the equation (e.g. CODESYS PID). Opaque builtins with empty body fields diverge from that expectation.

### 5. Online capabilities beyond “edit YAML”

Recurring feature set: monitor, write, force, breakpoints/step (where supported), watch lists, cross-reference, offline↔online compare. OpenPLC’s debug WebSocket is a concrete open-source analogue for Soft-PLC↔editor live identity.

### 6. Scholarly axis gap

arXiv material emphasizes **language semantics, verification, LLM codegen, complexity metrics** — useful for “structure and inspectability matter,” weak for product UX parity. Vendor docs + practitioner material carry the UI capability list.

## Gaps and limitations

- Full IEC 61131-3 standard text is paywalled; synthesis uses secondary normative mappings (OPC UA, PLCopen excerpts, reputable explainers).
- Vendor docs emphasize **their** metaphors (OB vs Task vs Application); absolute feature parity is impossible without choosing a reference model.
- Safety / SIL engineering surfaces and motion-specific tasks are out of depth here.
- Preprints do not document Soft-PLC App UX; do not treat arXiv as product guidance.
- This brief does **not** claim PLCAssistant must implement every vendor feature; it maps what “industrial systems expose.”

## Recommended reading order

1. IronPLC program organization (quick mental model)
2. OPC UA PLC Info Model §4.1.1.3 (formal hierarchy)
3. CODESYS Application + Task Configuration (multi-application + active app)
4. Rockwell Tasks/Programs/Routines (multi-program scheduling language)
5. Siemens OB/FC/FB/DB (alternate vendor structuring)
6. TwinCAT online monitoring (what “running” looks like in the editor)
7. CODESYS PID FB (generic library + equation)
8. OpenPLC Runtime + DEBUG_PROTOCOL (open Soft-PLC editor↔runtime pattern)

## Role in pipeline

Supportive context for `/explore SWD-178` and later `/define` on Soft-PLC App program surface. Does **not** settle user alignment. Particulars still open: which industrial reference to emulate first, how many concurrent programs in v1, online monitoring depth, PID library consolidation vs keep wedge-named wrappers, etc.

## Sources

### Preprints (arXiv)

- Zhang & de Sousa, *Exploring LLM Support for Generating IEC 61131-3 Graphic Language Programs*, arXiv:2410.15200
- Fischer et al., *Measuring the Overall Complexity of Graphical and Textual IEC 61131-3 Control Software*, arXiv:2212.05918
- Additional IEC 61131 verification / ST semantics papers in search dumps (`/tmp/plc-ui-research/`)

### Formal written

- OPC Foundation, *OPC UA for Programmable Logic Controllers based on IEC 61131-3*, §4.1.1.3 Ctrl Configuration/Resources/Tasks — https://reference.opcfoundation.org/specs/OPC-30000/4.1.1.3
- ABB, *Overview of the IEC 61131 standard* — DS_2101127-EN PDF
- Siemens, *Code blocks for structuring your program* (S7-1200) — docs.tia.siemens.cloud
- Rockwell Automation, *Use Tasks, Programs, and Routines* (Studio 5000) + *Logix 5000 Controllers Tasks, Programs, and Routines* (1756-PM005)
- CODESYS Help, *Object: Application*; *Task Configuration*; *PID (FB)* (Util library)
- Beckhoff Infosys, *Monitoring in Programming Objects* (TwinCAT 3)

### Web discovery

- IronPLC, *Program Organization* — https://www.ironplc.com/explanation/program-organization.html
- PLCopen FAQs / Common Elements materials — plcopen.org
- Autonomy Logic, OpenPLC Runtime README + `docs/DEBUG_PROTOCOL.md`

### Informal / practitioner

- Automation.com, *Coder's Corner: The IEC 61131-3 Software Model*
- SolisPLC / Industrial Monitor Direct — Logix tasks; TIA online/force/cross-ref guides
- OpenPLC Discussion Community — multi-program / task / global variable setup
- Industrial Monitor Direct — TwinCAT Program POU order under PlcTask

## Tracker

- Story: [SWD-178](https://marcusknielsen.atlassian.net/browse/SWD-178)
- Task: [SWD-179](https://marcusknielsen.atlassian.net/browse/SWD-179)
- Artifact: `docs/RESEARCH.md`
- Branch: `cursor/swd-179-plc-program-surface-research-a52c`
- PR: *(opened with this commit)*

## Next

`/explore SWD-178` — Chart destination and route Tasks for industrial-parity Soft-PLC programming surface; research brief is supportive context only (does not lock scope).
