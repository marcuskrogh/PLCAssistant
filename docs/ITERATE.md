# Iterate notes: Integration mock UI + preset selection (SWD-143)

**In Review** — App **0.1.24** on `cursor/swd-143-mock-ui-presets-33f4`

## Delivered
1. Options flow for `dynamics_preset` + JSON `dynamics_params`
2. Config-entry options persistence; reload rebuilds plant from initials
3. `HassPlantSimulator` / `for_preset` honor selected preset + overrides (default `skid`)
4. Service `plcassistant.set_dynamics_preset` (same SoT)
5. `sensor.plcassistant_dynamics_preset` + Lovelace v12 operator copy

## Next
`/review-fix SWD-143`
