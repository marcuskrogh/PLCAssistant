# Iterate notes: Soft-PLC ↔ integration mock ownership (SWD-145)

**In Review** — App **0.1.21** review-fix follow-up (PR #59 shipped 0.1.20 prematurely)

## review-fix iter1 findings → fixed
1. **BLOCKING:** Real plant LOS (`BAD`/`unavailable` after a GOOD sample) was forced GOOD — now only suppress never-sampled declare defaults; LOS trips after sample.
2. **SHOULD-FIX:** Offline LWT now includes `scan_period_s`.
3. **SHOULD-FIX:** Plant Numbers no longer write `inputs.json` (SP_LEVEL_REQ only).
4. **SHOULD-FIX:** Lovelace README updated for plant IN / static until SWD-146.
5. **SHOULD-FIX:** Test comment no longer claims plant motion.

## Next
Re-verify CLEAN → `/ship SWD-145` (0.1.21 follow-up PR)
