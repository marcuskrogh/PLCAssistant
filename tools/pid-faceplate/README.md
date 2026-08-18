# PID faceplate sandbox

Iterate analog-controller chrome without deploying the Home Assistant App.

Source of truth: `custom_components/plcassistant/www/pid-faceplate-elements.js`.
The Lovelace card imports the same module.

## Open

From the repository root:

```bash
./tools/pid-faceplate/serve.sh
```

Then open http://127.0.0.1:8765/tools/pid-faceplate/

(A static server is required so the browser can load the ES module.)

## What you get

- Isolated elements: ISA-5.1 glyph, KPI row, PV/SP/CO bars, MAN/AUTO/REM
- Assembled Level and Flow mocks driven by the sliders
- Click a highlighted bar to type a value; nudge arrows (±0.1 / ±1.0); gear for Kp/Ki/Kd

Ship the App only when you want operators to receive chrome changes.
