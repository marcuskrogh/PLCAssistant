# Iterate: Integration setup fails — No module named plcassistant.io

## Prior work
- Task: [SWD-183](https://marcusknielsen.atlassian.net/browse/SWD-183)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/81 (merged, App 0.1.38)
- Spec context: `docs/PLAN.md` (SWD-183/184 Datablock defaults), `docs/packaging/01-shape.md`

## Problem
HA Core fails to set up the thin integration after App 0.1.38:

```text
ModuleNotFoundError: No module named 'plcassistant.io'
  File ".../custom_components/plcassistant/__init__.py", line 106, in _default_bindings
    from plcassistant.io.datablock import (...)
```

Thin integration runs in HA Core (`/config/custom_components/…`). Soft-PLC
`plcassistant` is installed only inside the App container. SWD-184/183 wired
default bindings / Datablock store / HTTP API to Soft-PLC imports, so Core
setup crashes before entities load.

## Clarifications
- None — traceback + packaging shape are sufficient.

## Acceptance criteria
- [ ] `_default_bindings()` and Datablock store/API import only HA-local modules
- [ ] Integration setup path works with Soft-PLC absent from `sys.path`
- [ ] Default tank bindings stay parity-checked against Soft-PLC `default_tank_datablock_catalog`
- [ ] Regression test fails if thin-integration setup reintroduces `from plcassistant…` for datablocks
- [ ] App/integration version bumped; dual trees synced

## Out of scope
- Changing Soft-PLC Datablock ownership / MQTT contracts
- Classic PID output Manual
- Installing Soft-PLC into HA Core

## Work packages
1. Vendor HA-local Datablock binding types + catalog (no Soft-PLC deps)
2. Retarget `__init__` / `datablocks.store` / `datablocks.http_api` (+ number flip already has Soft-PLC fallback)
3. Tests + version bump + dual-tree sync

## Tracker
- Task: [SWD-219](https://marcusknielsen.atlassian.net/browse/SWD-219)
- Relates: SWD-183
- Branch: `cursor/swd-219-integration-plcassistant-io-a52c`

## Next
`/review-fix SWD-219` — Review and auto-fix until clean
