# Iterate: Lovelace PID cards ISA look and highlighting

## Prior work
- Task: [SWD-360](https://marcusknielsen.atlassian.net/browse/SWD-360)
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/101 (App 0.1.55)
- Spec context: docs/PLAN.md, docs/RESEARCH.md, docs/io/06-pid-faceplate.md

## Problem
Shipped ISA-5.1 Diagram glyph and ISA-TR5.9 PID structure, but Lovelace PID cards still look like a climate card:

- Man / Auto / Rem are colour-coded (amber / teal / blue)
- Active SP is always accent-coloured
- CO bar uses the same mode hue
- Error is a subtitle (`err ±…`) under SP, not a first-class KPI
- No ISA-5.1 three-mode chrome (ε / P / I / D)
- Level CO bar still scales to max 6 instead of cascade 8 L/min

## Clarifications
- Invoke was rich; no further clarifying questions.
- ISA-5.1 supplies the **look** (three-mode glyph names and PV / SP / ε / CO).
- ISA-101 high-performance HMI supplies **colour highlighting**: grayscale in normal operation; colour only for caution / abnormal. Not ISA-5.1 P&ID line colours.
- Man / Auto / Rem remain **SP-source** modes (not Bauer output Manual).

## Acceptance criteria
- [x] Lovelace PID card shows a compact ISA-5.1 chrome strip (ε / P / I / D) matching the Diagram glyph
- [x] Hero KPIs are PV / SP / ε / CO at 2dp; ε is first-class (not a subtitle)
- [x] Normal operation uses grayscale / Home Assistant tokens; mode is an outlined badge and inverted grayscale active button — no `--pid-man` / `--pid-auto` / `--pid-rem`
- [x] Colour only for attention: caution → `--warning-color`; abnormal → `--error-color`
- [x] Exported `pidHighlightSeverity(err, sp, pv)`: `|err| / max(|sp|, |pv|, floor)` &lt; 2% normal, &lt; 10% caution, else abnormal
- [x] CO bar highlights at clamp (~0% or ~100% of scale); level scale max is 8 L/min; flow remains 100%
- [x] Regression tests (Python + Node contract) + dual-tree sync + App **0.1.56**

## Out of scope
- Full ISA-101 rewrite of Operate
- Bauer output Manual (`auto` / `uman`)
- Series form / ERF / percent-of-range scaling
- Changing pin name `cv` (label stays CO)

## Work packages
1. Faceplate look + highlighting helpers in `pid-loop-card.js` — done
2. Docs (`06-pid-faceplate.md`) + tests + version 0.1.56 + dual-tree sync — done

## Tracker
- Task: [SWD-366](https://marcusknielsen.atlassian.net/browse/SWD-366)
- Relates: SWD-360
- Branch: `cursor/swd-366-isa-pid-cards-25fc`
- PR: https://github.com/marcuskrogh/PLCAssistant/pull/102
- App: **0.1.56**

## Next
`/review-fix SWD-366` — Review and auto-fix (single pass)
