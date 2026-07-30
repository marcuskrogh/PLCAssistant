# Iterate: Sidebar dynamics block editor + toy setup guide (SWD-166)

**Done** — App **0.1.25**; shipped PR [#68](https://github.com/marcuskrogh/PLCAssistant/pull/68)

## Prior work
- Task: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/66 (App 0.1.24)

## Shipped
1. Lovelace v13 sidebar: **Operate** + **Dynamics** (`iframe` → `/api/plcassistant/dynamics/ui`)
2. Block editor SPA: add/remove `tank` / `pump` / `orifice` / `lag` / `custom_ode`; bind tags ↔ variables; Soft-PLC output map
3. HTTP API + model store under `config/plcassistant/models/`; Validate / Save / Apply → plant reload
4. Registry extra model dirs; Soft-PLC stays mock-unaware
5. README **Toy example setup** guide
6. review-fix CLEAN after 1 iter (apply reload + iframe `callApi` auth + dual-tree sync)

## Operator note
Update App to **0.1.25+**. Open **PLCAssistant → Dynamics** to edit/apply models. Options flow / `set_dynamics_preset` still work for preset selection.

## Tracker
- Task: [SWD-166](https://marcusknielsen.atlassian.net/browse/SWD-166)
- Relates: [SWD-143](https://marcusknielsen.atlassian.net/browse/SWD-143)
- Branch: `cursor/swd-166-dynamics-sidebar-editor-33f4`

## Next
Done — phase closed.
