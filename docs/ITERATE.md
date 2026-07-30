# Iterate: Sidebar dynamics block editor + toy setup guide (SWD-166)

## Prior work
- Task: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/66 (App 0.1.24)
- Spec context: `docs/PLAN.md` (SWD-143) deferred full unit-op graph UI

## Problem
Options flow + `set_dynamics_preset` is not a usable configuration surface. Operators need a **proper HA sidebar UI** with a **block-like editor** to add unit-op / ODE blocks and associate Soft-PLC tags with block variables. The Lovelace Operate HMI can share the same sidebar product. README lacks a clear end-to-end **toy example setup guide**.

## Clarifications
- Soft-PLC App Ingress remains the Soft-PLC **program** editor (not plant math).
- Plant dynamics editor lives in the **thin integration** / HA sidebar.
- Apply = validate + persist model document + select preset + reload plant (existing ownership).

## Acceptance criteria
1. PLCAssistant sidebar includes **Operate** (existing skid HMI) and **Dynamics** (block editor) views.
2. Block editor supports add/remove of `tank` / `pump` / `orifice` / `lag` / `custom_ode`; edit bind maps (variables ↔ signals) and params/ODE expressions; edit Soft-PLC **output tag** map.
3. Validate / Save / Apply persist under `config/plcassistant/models/` and reload the plant simulator; Soft-PLC stays mock-unaware.
4. README has a dedicated **Toy example setup** guide (install → mock mode → Operate → Dynamics → Start).
5. App + integration version bumped (**0.1.25**); dual trees synced; automated tests for store/API contracts + dashboard.

## Out of scope
- Soft-PLC program canvas changes
- Mid-scan live graph rewiring without apply/reload
- Full chem-eng catalog beyond existing unit ops
- Field I/O / mock-off commissioning

## Work packages
1. Model store + HTTP API (catalog/get/validate/save/apply) + registry extra model dirs
2. Dynamics block editor UI (static SPA) + Lovelace Dynamics view
3. README toy guide + version/docs/tests

## Tracker
- Task: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166)
- Relates: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Branch: `cursor/swd-166-dynamics-sidebar-editor-33f4`
- Implement: App **0.1.25**

## Next
`/review-fix SWD-166`
