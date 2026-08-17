# Implementation plan: Standardised PID visualisation and structure (SWD-360)

## Summary
- Give the built-in **PID** block an ISA-5.1 three-mode Diagram glyph and an
  ISA-TR5.9 named structure (Parallel form, 2DoF weights, PV / SP / CO labels).
- Implement the Bauer hybrid algorithm (incremental when `ki ≠ 0`, positional
  when `ki = 0`) so anti-windup and bumpless transfer are intrinsic.
- Keep the existing setpoint-source Manual / Automatic / Remote mux as HMI
  outside the function block. Do not treat it as Bauer output Manual.

## Scope
### In
- App Diagram: ISA-5.1 Table 15 automatic three-mode controller glyph for
  `template_id == "PID"` (error/difference + P, I, D compartments)
- Builtin PID pin/param contract: ISA-TR5.9 names + Bauer optional pins
- Hybrid incremental / positional equation (or native builtin) with default
  derivative on PV (`gamma = 0`)
- Faceplate / Datablock **labels** PV, SP, CO (existing `pv` / `sp` / `cv` pins stay)
- Migration: existing `level_pi` / `flow_pi` copies keep cascade PI behaviour
- Tests + surface/control/faceplate docs + App version if runtime/UI ships

### Out
- ISA-TR5.9 Series form and external-reset feedback
- Classic output Manual on the Lovelace card (Bauer `auto` / `uman`)
- Forcing internal percent-of-range scaling
- ISA-5.5 equipment symbols; ISA-101 HMI rewrite
- Vendoring github.com/copybit/pid
- Autotune

## Decisions
| Topic | Decision |
|-------|----------|
| Visualisation | ANSI/ISA-5.1-2024 Table 15 three-mode glyph + Table 16 P/I/D symbols. Generic rectangle remains for non-PID blocks. |
| Identification | Optional instance param `isa_tag` (e.g. LIC, FIC) drawn on the glyph. P&ID bubbles are not the programming-surface default. |
| Algorithm form | ISA-TR5.9 **Parallel** (independent `kp`, `ki`, `kd`) — matches today’s template. Declare `form: parallel` on the instance. Standard/Series conversion is later. |
| 2DoF structure | Params `beta` (P setpoint weight) and `gamma` (D setpoint weight). Defaults `beta=1`, `gamma=0` (D on PV). |
| Action | Reverse acting (`SP − PV`) remains default for the wedge; optional `direct_acting` param. |
| Implementation | Bauer hybrid: incremental when `ki ≠ 0`; positional + bias `u0` when `ki = 0`. Reimplement in Soft-PLC; do not copy GitHub listings. |
| Pins (required) | Keep `pv`, `sp`, `running`, `cv` so existing wires and tags stay valid. |
| Pins (optional, defaulted) | `uff` (feed-forward, default 0), `track` (bool, default false), `utrack` (default 0). Unwired = Bauer defaults. |
| `running` vs `auto` | `running` stays the permit/enable pin (wedge Start). When false: today’s hold-or-zero CV behaviour. Do not overload it as output Manual. |
| SP-source Man/Auto/Rem | Unchanged HMI mux **outside** the FB (`docs/io/06-pid-faceplate.md`). |
| Scaling | Keep engineering units for the lab wedge. Document ISA-TR5.9 % of range as a later option. |
| Faceplate | Relabel hero strip to PV / SP / CO; keep climate-inspired Man/Auto/Rem colours. |

## Classification
- Class: feature
- Confidence: high
- Why: new ISA glyph, named PID structure, and hybrid algorithm are a buildable product slice, not a defect fix

## Workflow
- Template: feature-heavy
- Parameters:
  - implement.mode: single
  - implement.verify: tests
  - implement.iteration: one-shot
  - review.mode: multiagent
  - review.depth: full
  - side_paths: none
- Chain: implement → review-fix → ship
- Rationale: schema/migration of the public PID template plus Diagram and faceplate; research already done on this Task; sequential implement, full review

## Inputs
- Research: [`docs/RESEARCH.md`](RESEARCH.md)
- Model: —

## Constraints
- Dual trees (`plcassistant/` and `custom_components/plcassistant/`) stay in sync when the faceplate or builtin contract ships
- Wedge cascade must still settle: level CV → flow SP, flow CV → `CMD_SPEED`
- Conditional-integration PI behaviour at `kd=0` must remain acceptable for the demo (incremental clamp is the intended replacement, with a cascade settle test)
- copybit/pid has no license — reimplement from the papers, do not paste listings
- Default `pytest` stays fast (no live marker on new tests unless they need the stack)

## Acceptance criteria
- [ ] PID instances on the App Diagram use the ISA-5.1 three-mode glyph (P, I, D compartments visible; generic `block-rect` is not the PID chrome)
- [ ] Builtin PID declares ISA-TR5.9 Parallel form and 2DoF `beta` / `gamma` (defaults 1 / 0)
- [ ] Required pins remain `pv`, `sp`, `running`, `cv`; optional Bauer pins default safe
- [ ] Hybrid algorithm: `ki ≠ 0` uses incremental updates; `ki = 0` uses positional + `u0`; derivative uses PV (`gamma=0`) so a setpoint step does not spike D
- [ ] Existing `level_pi` / `flow_pi` programs migrate without retuning for the PI (`kd=0`) case
- [ ] Lovelace PID card labels PV, SP, CO; Man/Auto/Rem SP-source behaviour unchanged
- [ ] Unit tests cover form/pins/glyph contract, incremental clamp, D-on-PV, and migration; default `pytest` still excludes `live`

## Work packages
1. **ISA-5.1 three-mode PID glyph on App Diagram** — [SWD-361](https://marcusknielsen.atlassian.net/browse/SWD-361)
2. **ISA-TR5.9 / Bauer PID pin and parameter contract** — [SWD-362](https://marcusknielsen.atlassian.net/browse/SWD-362)
3. **Hybrid incremental/positional PID algorithm** — [SWD-363](https://marcusknielsen.atlassian.net/browse/SWD-363)
4. **Faceplate and Datablock PV/SP/CO alignment** — [SWD-364](https://marcusknielsen.atlassian.net/browse/SWD-364)
5. **Tests, docs, and App version** — [SWD-365](https://marcusknielsen.atlassian.net/browse/SWD-365)

## Open items
- Output Manual (`auto` / `uman`) on the Lovelace card — later iterate, not this slice
- Series form and external-reset feedback — later
- Percent-of-range internal scaling — later, after the lab wedge still uses engineering units

## Tracker
- Provider: jira
- Story: [SWD-359](https://marcusknielsen.atlassian.net/browse/SWD-359)
- Task: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360)
- Sub-tasks: SWD-361, SWD-362, SWD-363, SWD-364, SWD-365
- Branch: `cursor/swd-360-isa-pid-blocks-25fc`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/101
- Classification: feature
- Workflow: feature-heavy

## Next
`/implement SWD-360` — Build per PLAN.md workflow binding (same branch/PR)
