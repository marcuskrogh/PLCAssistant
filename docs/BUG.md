# Bug: PID diagram clipping + wrong CV max; model settings hard to edit

## Summary
- Soft-PLC App **Programs → Diagram**: PID blocks are visible again but **clipped** (bottom pins / right edge cut off), so it is hard to trust layout and wiring.
- Both cascade PIDs show **CV max = 6**. Level (`level_pi`) should stay ~6 (outer loop → flow SP units); **flow (`flow_pi`) should be 100** (CMD_SPEED %). Same limit on both is wrong for cascade and for pump command scaling.
- Integration **Dynamics / model settings**: changing pump maximum flow (`q_pump_max`) requires hand-editing a raw **Global params** JSON object. Modelling should be structured and simple to engage with (labeled fields, not only JSON textareas).

## Repro
1. Open PLCAssistant App → one-tank / main program → **Diagram**.
2. Observe `level_pi` and `flow_pi` blocks: bottoms and/or right edge clipped; inspect instance params / live behaviour — **CV max is 6 for both**.
3. Open the Dynamics / model block editor (integration modelling UI).
4. Try to change maximum pump flow: only path is editing `"q_pump_max"` inside the Global params JSON textarea (same pattern for other globals / initial state).

## Expected
- Diagram renders each PID block **fully** (title, pins, labels) without clipping inside the canvas viewport; scroll/pan or auto-size as needed so blocks and wires remain usable on mobile and desktop.
- Demo / cascade program params: `level_pi.params.cv_max` ≈ **6**, `flow_pi.params.cv_max` = **100**; runtime clamps CVs accordingly (level CV → flow SP range; flow CV → 0–100% speed).
- Model settings expose **structured, labeled controls** for known global params (at least **max pump flow** / `q_pump_max`, and the other skid globals such as `h_res_max`, `k_drain`, `pump_tau`) and for initial state keys — without requiring valid JSON editing for the common path. Advanced JSON may remain as an optional escape hatch.

## Actual
- PID blocks are partially clipped on the Diagram.
- Both PIDs appear to use CV max **6** (flow should be **100**).
- Model engagement for pump max flow is raw JSON only.

## Impact
- Cascade tuning / trust in the programming surface is undermined (wrong clamp on flow loop → CMD_SPEED stuck in a tiny band if both are 6).
- Operators cannot confidently inspect or edit the Diagram on typical viewports.
- Changing plant capacity (`q_pump_max`) is error-prone and opaque for non-JSON users.

## Suspected area
- App Diagram canvas (`plcassistant/app/_canvas.py` / diagram layout sizing, overflow, pin geometry) — follow-on to **SWD-249** / **SWD-237**.
- Cascade program seed / migrate / repair path for instance `params.cv_max` (`plcassistant/surface/builtin.py` — `sp_flow_max` vs `cmd_speed_max`; project YAML / heal after empty-diagram repair).
- Integration Dynamics editor UI (`custom_components/plcassistant/www/dynamics_editor.html`) — Global params / Initial state as JSON textareas.

## Acceptance criteria
- [x] On the one-tank (and equivalent cascade) Diagram, PID blocks render fully: all pins and labels visible without being cut off by the canvas or panel edges under normal mobile and desktop layouts. — dynamic SVG `viewBox` + pointer mapping
- [x] `flow_pi` (or equivalent flow PID instance) has `cv_max` = **100**; `level_pi` retains `cv_max` ≈ **6** (or the documented SP_FLOW max). Persisted program JSON and live params agree. — `repair_cascade_pid_limits` on load
- [x] Soft-PLC / cascade behaviour clamps flow CV to 0–100 and level CV to the flow-SP max — not both to 6.
- [x] Dynamics model settings provide labeled numeric (or equivalent structured) fields for skid global params including **maximum pump flow** (`q_pump_max`); changing that value and saving updates the model without hand-editing JSON for the happy path.
- [x] Initial state is editable in a structured way consistent with globals (not JSON-only for the common path).
- [x] Regression tests cover correct per-instance `cv_max` on the demo cascade and the structured model-settings persistence path where testable.

## Out of scope
- Full redesign of the Dynamics equation / unit-op authoring surface beyond structured globals + initial state (and light Model I/O clarity).
- Lovelace PID faceplate / HMI card changes.
- Unrelated library “+ Program Block” editor behaviour.
- Changing the physics defaults of `q_pump_max` itself (default may stay 8.0 L/min); this bug is about **editability** and **correct PID limits**, not mandating a new default capacity.

## Work packages
1. Diagram: fix PID block clipping / layout so blocks fully render. — done (`updateCanvasViewBox` / `clientToSvg`)
2. Params: ensure cascade seed/repair assigns distinct `cv_max` (level ≈ 6, flow = 100) and runtime uses them. — done (`repair_cascade_pid_limits`)
3. Modelling UI: structured globals + initial-state editors (esp. `q_pump_max`) in `dynamics_editor.html` (+ mirrored tree); keep JSON advanced/optional if useful. — done
4. Tests + version bump as needed for App/integration. — done (App **0.1.53**, `tests/test_swd250_acceptance.py`)

## Tracker
- Task: [SWD-250](https://marcusknielsen.atlassian.net/browse/SWD-250)
- Sub-tasks: _(none)_
- Branch: `cursor/swd-250-pid-cvmax-model-9910`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/98
- Relates: [SWD-249](https://marcusknielsen.atlassian.net/browse/SWD-249)
- App: **0.1.53**

## Next
`/review-fix SWD-250` — multi-axis review ↔ fix-forward on PR #98
