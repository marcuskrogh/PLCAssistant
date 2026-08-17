# Standardised PID blocks

Initiative [SWD-359](https://marcusknielsen.atlassian.net/browse/SWD-359): one ISA-aligned
PID glyph on the Soft-PLC Diagram and one named PID structure in the builtin
library.

| Doc | Role |
|-----|------|
| [`docs/ROADMAP.md`](../ROADMAP.md) | Destination and route |
| [`docs/RESEARCH.md`](../RESEARCH.md) | ISA-5.1 / ISA-TR5.9 / IFAC 2024 evidence |
| [`docs/PLAN.md`](../PLAN.md) | Implementation plan (SWD-360) |
| [`docs/surface/03-builtin-library.md`](../surface/03-builtin-library.md) | Builtin PID (ISA-TR5.9 Parallel + IFAC 2024 incremental) |
| [`docs/io/06-pid-faceplate.md`](../io/06-pid-faceplate.md) | Operator faceplate (PV / SP / CO) |
| [`docs/control/02-fb-pid.md`](../control/02-fb-pid.md) | Wedge cascade PI on the PID template |

Delivery Task: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360) — shipped PR [#101](https://github.com/marcuskrogh/PLCAssistant/pull/101).
IFAC 2024 algorithm align: [SWD-367](https://marcusknielsen.atlassian.net/browse/SWD-367).
