# Iterate notes: Integration mock UI + preset selection (SWD-143)

**Done** — App **0.1.24**; shipped PR [#66](https://github.com/marcuskrogh/PLCAssistant/pull/66)

## Shipped
1. Options flow for `dynamics_preset` + JSON `dynamics_params`
2. Config-entry options persistence; reload rebuilds plant from initials
3. `HassPlantSimulator` / `for_preset` honor selected preset + overrides (default `skid`)
4. Service `plcassistant.set_dynamics_preset` (same SoT; independent registration)
5. `sensor.plcassistant_dynamics_preset` + Lovelace v12 operator copy
6. review-fix CLEAN after 1 iter (service register + options merge)

## Operator note
Update App to **0.1.24+**. Choose preset under **Settings → Devices → PLCAssistant → Configure**, or call `plcassistant.set_dynamics_preset`. Default remains `skid`.

## Next
Done — SWD-142 phase closed (all theme Tasks Done).
