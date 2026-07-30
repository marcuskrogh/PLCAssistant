# Iterate notes: Integration mock UI + preset selection (SWD-143)

**In progress** — define locked; implement App **0.1.24** on `cursor/swd-143-mock-ui-presets-33f4`

## Define lock
1. Options flow is the primary preset chooser (not Soft-PLC Ingress / custom panel)
2. Persist `dynamics_preset` + `dynamics_params` on config-entry options
3. Apply = rebuild plant simulator from initials (not mid-scan graph edit)
4. Service `set_dynamics_preset` shares the same options SoT
5. File/YAML remains unit-op authoring; UI selects presets + numeric overrides only

## Next
`/implement SWD-143` — or `/ship SWD-143` to finish remaining through Done
