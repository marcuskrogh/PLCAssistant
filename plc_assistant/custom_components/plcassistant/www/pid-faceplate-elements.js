/**
 * Isolated PID faceplate elements — shared chrome for Lovelace and the
 * developer sandbox. Operator writes stay in pid-loop-card.js.
 *
 * Named elements: isa-glyph, kpi-row, analog-bars, mode-row.
 * Mount one-at-a-time via mountPidFaceplateElement, or assemble a full face.
 *
 * Writable analog uses a muted activity-green fill. Mode buttons stay
 * grayscale invert. Caution/abnormal colour stays on ε (and MV clamp),
 * not on the writable fill.
 */

/** Display precision for faceplate KPIs (PV / SP / CO / error) and SP editors. */
export const PID_DISPLAY_DIGITS = 2;

/** Relative |ε| vs max(|SP|, |PV|, floor) below this fraction is normal. */
export const PID_ERR_CAUTION_FRAC = 0.02;

/** Relative |ε| at or above this fraction is abnormal (between is caution). */
export const PID_ERR_ABNORMAL_FRAC = 0.1;

/** Floor so a zero SP/PV pair does not divide by zero. */
export const PID_ERR_SCALE_FLOOR = 1e-9;

/** Flow-loop CO scale (CMD_SPEED %). */
export const PID_CV_MAX_FLOW = 100;

/** Level-loop CO scale (cascade flow request, L/min). */
export const PID_CV_MAX_LEVEL = 8;

/** Bar fraction from 0% or 100% treated as clamp. */
export const PID_CV_CLAMP_FRAC = 0.005;

/** Standardised PID params shown in the settings gear (skip unused td/gamma). */
export const PID_TUNE_KEYS = [
  "kp",
  "ki",
  "kd",
  "u0",
  "beta",
  "direct_acting",
  "cv_min",
  "cv_max",
  "hold_when_stopped",
  "ts",
  "tf_ts",
];

export const PID_TUNE_BOOL_KEYS = ["direct_acting", "hold_when_stopped"];

export const PID_SETTINGS_PANES = ["gains", "structure", "output", "filter"];

/**
 * Format a numeric faceplate value to fixed decimal places, or em-dash.
 * Always uses ``toFixed`` so float noise never leaks into the HMI.
 * Keep digits in sync with DISPLAY_PRECISION in const.py.
 */
export function formatPidValue(value, digits = PID_DISPLAY_DIGITS) {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

/** Signed ε display: +0.15 / -0.02 / 0.00, or em-dash. */
export function formatPidError(value, digits = PID_DISPLAY_DIGITS) {
  const text = formatPidValue(value, digits);
  if (text === "—") return text;
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  if (Number.isFinite(n) && n > 0) return `+${text}`;
  return text;
}

/** True when value is present and finite (null/undefined/"" are not). */
export function isPresentFinite(value) {
  if (value === null || value === undefined || value === "") return false;
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  return Number.isFinite(n);
}

/** ε = SP − PV, or null when either is missing. */
export function pidError(sp, pv) {
  if (!isPresentFinite(sp) || !isPresentFinite(pv)) return null;
  return Number(sp) - Number(pv);
}

/**
 * ISA-101 severity for loop error.
 * ``|err| / max(|sp|, |pv|, floor)``: &lt; 2% normal, &lt; 10% caution, else abnormal.
 */
export function pidHighlightSeverity(err, sp, pv) {
  if (!isPresentFinite(err)) return "normal";
  const mag = Math.abs(Number(err));
  const spN = isPresentFinite(sp) ? Math.abs(Number(sp)) : 0;
  const pvN = isPresentFinite(pv) ? Math.abs(Number(pv)) : 0;
  const scale = Math.max(spN, pvN, PID_ERR_SCALE_FLOOR);
  const frac = mag / scale;
  if (frac < PID_ERR_CAUTION_FRAC) return "normal";
  if (frac < PID_ERR_ABNORMAL_FRAC) return "caution";
  return "abnormal";
}

/** CO bar scale max for a loop (flow % vs level L/min). */
export function pidCvScaleMax(loopId) {
  return loopId === "flow" ? PID_CV_MAX_FLOW : PID_CV_MAX_LEVEL;
}

/** CO bar width 0–100. Missing/non-finite CV → 0. */
export function pidCvBarPct(cv, loopId) {
  const n = Number(cv);
  if (!Number.isFinite(n)) return 0;
  const max = pidCvScaleMax(loopId);
  if (!(max > 0)) return 0;
  return Math.max(0, Math.min(100, (Math.abs(n) / max) * 100));
}

/** Clamp attention when the bar is at ~0% or ~100% of scale. */
export function pidCvHighlightSeverity(cv, loopId) {
  if (!isPresentFinite(cv)) return "normal";
  const pct = pidCvBarPct(cv, loopId);
  const band = PID_CV_CLAMP_FRAC * 100;
  if (pct <= band || pct >= 100 - band) return "caution";
  return "normal";
}

/** Worst of error vs CO-clamp for the card chrome. */
export function pidFaceplateHighlight(err, sp, pv, cv, loopId) {
  const errHi = pidHighlightSeverity(err, sp, pv);
  if (errHi === "abnormal") return "abnormal";
  const cvHi = pidCvHighlightSeverity(cv, loopId);
  if (errHi === "caution" || cvHi === "caution") return "caution";
  return "normal";
}

/** Level PV / SP engineering range (tank height, m). */
export const PID_PV_MAX_LEVEL = 0.4;

/** Flow PV / SP engineering range (pump capacity, L/min). */
export const PID_PV_MAX_FLOW = 8;

/** PV/SP bar scale max for a loop. */
export function pidPvScaleMax(loopId) {
  return loopId === "flow" ? PID_PV_MAX_FLOW : PID_PV_MAX_LEVEL;
}

/** Analog fill 0–100 from a value and scale max. */
export function pidBarPct(value, max) {
  const n = Number(value);
  if (!Number.isFinite(n) || !(max > 0)) return 0;
  return Math.max(0, Math.min(100, (n / max) * 100));
}

/**
 * DCS analog-controller write target.
 * MAN → CO; AUTO → SP when the Auto entity is a Number; REM → none.
 */
export function pidOperatorWriteTarget(mode, { spWritable = true, coWritable = true } = {}) {
  const m = String(mode ?? "").toLowerCase();
  if ((m === "manual" || m === "man" || m === "0") && coWritable) return "co";
  if ((m === "automatic" || m === "auto" || m === "1") && spWritable) return "sp";
  return null;
}

/**
 * Map a pointer position on a bar track to an engineering value.
 * Vertical bars: 0 at the bottom. Horizontal bars: 0 at the left.
 */
export function pidBarValueFromPointer(rect, clientX, clientY, min, max, orientation) {
  if (!rect || !(rect.width > 0) || !(rect.height > 0)) return null;
  const lo = Number(min);
  const hi = Number(max);
  if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi === lo) return null;
  let frac;
  if (orientation === "horizontal") {
    frac = (Number(clientX) - rect.left) / rect.width;
  } else {
    frac = 1 - (Number(clientY) - rect.top) / rect.height;
  }
  if (!Number.isFinite(frac)) return null;
  frac = Math.max(0, Math.min(1, frac));
  return lo + frac * (hi - lo);
}

/** Fine nudge step on the writable analog. */
export const PID_NUDGE_FINE = 0.1;

/** Coarse nudge step on the writable analog. */
export const PID_NUDGE_COARSE = 1;

/** Engineering range for a nudge of SP vs CO. */
export function pidNudgeRange(metric, loopId) {
  const key = String(metric ?? "");
  if (key === "co" || key === "cv") {
    return { min: 0, max: pidCvScaleMax(loopId) };
  }
  return { min: 0, max: pidPvScaleMax(loopId) };
}

/**
 * Add ``delta`` to a faceplate analog and clamp to ``[min, max]``.
 * Returns a 2dp commit, or null when the inputs are not finite.
 */
export function pidNudgeValue(value, delta, min, max) {
  if (!isPresentFinite(value) || !isPresentFinite(delta)) return null;
  let next = Number(value) + Number(delta);
  const lo = Number(min);
  const hi = Number(max);
  if (Number.isFinite(lo)) next = Math.max(lo, next);
  if (Number.isFinite(hi)) next = Math.min(hi, next);
  return commitSpValue(next);
}

/** Normalise a bar click to pv / sp / co. */
export function pidNormalizeBarKey(barKey) {
  const key = String(barKey ?? "");
  if (key === "sp") return "sp";
  if (key === "pv") return "pv";
  return "co";
}

/** Operator label for an analog. MV is the faceplate name for CO. */
export function pidBarFaceLabel(barKey) {
  const key = pidNormalizeBarKey(barKey);
  if (key === "sp") return "SP";
  if (key === "pv") return "PV";
  return "MV";
}

/** data-sp / data-apply key for a writable bar. PV has no editor. */
export function pidBarEditorKey(barKey) {
  const key = pidNormalizeBarKey(barKey);
  if (key === "sp") return "auto";
  if (key === "co") return "co";
  return null;
}

/** Engineering unit for a bar on a loop. */
export function pidBarUnit(barKey, loopId) {
  const key = String(barKey ?? "");
  if (key === "co" || key === "cv") {
    return loopId === "flow" ? "%" : "L/min";
  }
  return loopId === "flow" ? "L/min" : "m";
}

/**
 * Paint the focused numeric popup for one analog (label, min, max, unit, editor key).
 * Set is shown only when that analog is the operator write target.
 */
export function applyPidValueDialog(
  root,
  { barKey = "co", loopId = "level", value = null, writable = false } = {}
) {
  if (!root) return;
  const key = pidNormalizeBarKey(barKey);
  const editorKey = pidBarEditorKey(key);
  const label = pidBarFaceLabel(key);
  const range = pidNudgeRange(key, loopId);
  const unit = pidBarUnit(key, loopId);
  setText(root, "[data-value-title]", label);
  setText(root, "[data-value-label]", label);
  setText(root, "[data-value-min]", formatPidValue(range.min));
  setText(root, "[data-value-max]", formatPidValue(range.max));
  setText(root, "[data-value-unit]", unit);
  setText(root, "[data-value-current]", formatPidValue(value));
  const dialog = root.querySelector(".pid-value-dialog");
  const scope = dialog && typeof dialog.querySelector === "function" ? dialog : root;
  if (typeof scope.querySelector !== "function") return;
  const focus = scope.querySelector(".pid-value-focus");
  if (focus && typeof focus.setAttribute === "function") {
    focus.setAttribute("data-writable", writable ? "1" : "0");
  }
  const input = scope.querySelector("input[data-sp]");
  const apply = scope.querySelector("[data-apply]");
  const row = scope.querySelector("[data-source]");
  if (input) {
    if (editorKey) input.setAttribute("data-sp", editorKey);
    input.disabled = !writable;
  }
  if (apply) {
    if (editorKey) apply.setAttribute("data-apply", editorKey);
    apply.disabled = !writable;
  }
  if (row && editorKey) row.setAttribute("data-source", editorKey);
}

function setText(root, sel, value) {
  const el = root.querySelector(sel);
  if (el) el.textContent = value;
}

/**
 * Round a parsed SP to display precision for both UI commit and number.set_value.
 * Returns null when the input is not a finite number.
 */
export function commitSpValue(value, digits = PID_DISPLAY_DIGITS) {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return null;
  return Number(n.toFixed(digits));
}

/** Parse an SP draft string into a finite number, or null if incomplete/invalid. */
export function parseSpValue(raw) {
  const text = String(raw ?? "").trim().replace(",", ".");
  if (text === "" || text === "-" || text === "." || text === "-.") {
    return null;
  }
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

/**
 * Coerce a value for ``number.set_value``.
 * Returns a finite number, or null when the payload must not be sent (e.g. "man").
 */
export function numberServiceValue(value) {
  // Same gate as parseSpValue so Set and mode cannot diverge on drafts like "12abc".
  return parseSpValue(value);
}

/**
 * Resolve a faceplate click to a mode, apply, bar, nudge, settings, open, or
 * close action.
 *
 * Mode switches must use ``button[data-mode]`` only — never a bare
 * ``[data-mode]`` match — so a card-root accent attribute cannot hijack Set
 * (``data-mode="man"`` → Number("man") → NaN toast).
 *
 * Bar clicks are ``type: "bar"`` so the host can open a focused numeric
 * popup for that analog. Writability is painted separately; pointer-position
 * set is not part of this resolver.
 */
export function resolveFaceplateClick(target) {
  if (!target || typeof target.closest !== "function") return null;
  const closeBtn = target.closest("[data-close-editor]");
  if (closeBtn) {
    return { type: "close" };
  }
  const modeBtn = target.closest("button[data-mode]");
  if (modeBtn) {
    return { type: "mode", code: modeBtn.getAttribute("data-mode") };
  }
  const applyBtn = target.closest("[data-apply]");
  if (applyBtn) {
    if (applyBtn.disabled) return null;
    return { type: "apply", key: applyBtn.getAttribute("data-apply") };
  }
  const settingsApply = target.closest("[data-settings-apply]");
  if (settingsApply) {
    if (settingsApply.disabled) return null;
    return { type: "settings", action: "apply" };
  }
  const settingsCancel = target.closest("[data-settings-cancel]");
  if (settingsCancel) {
    return { type: "settings", action: "cancel" };
  }
  const paneBtn = target.closest("button[data-pane]");
  if (paneBtn) {
    return { type: "pane", id: paneBtn.getAttribute("data-pane") };
  }
  const nudgeBtn = target.closest("button[data-nudge]");
  if (nudgeBtn) {
    if (nudgeBtn.disabled) return null;
    const delta = Number(nudgeBtn.getAttribute("data-nudge"));
    if (!Number.isFinite(delta)) return null;
    return { type: "nudge", delta };
  }
  const barBtn = target.closest("[data-bar]");
  if (barBtn) {
    return { type: "bar", key: barBtn.getAttribute("data-bar") };
  }
  const settingsOpen = target.closest("[data-settings]");
  if (settingsOpen) {
    return { type: "settings", action: "open" };
  }
  // Dialog chrome (inputs/labels/panel) must not re-trigger open.
  if (
    target.closest(".pid-dialog-panel") ||
    target.closest("input[data-sp]") ||
    target.closest("input[data-tune]")
  ) {
    return null;
  }
  const openSurface = target.closest("[data-open-editor]");
  if (openSurface) {
    return { type: "open" };
  }
  return null;
}


/** CSS for every faceplate element (inject once per document/root). */
export function pidFaceplateStyles() {
  return PID_FACEPLATE_CSS;
}

const PID_FACEPLATE_CSS = `
.pid-shell {
  --pid-chrome: var(--primary-text-color);
  --pid-hi-caution: var(--warning-color, #f59e0b);
  --pid-hi-abnormal: var(--error-color, #dc2626);
  --pid-active: #5a8f6e;
  --pid-accent: var(--pid-chrome);
  --pid-focus: var(--primary-color, var(--pid-chrome));
  /* Match stock Lovelace cards (entities / glance) — HA design tokens. */
  --pid-font: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, inherit));
  --pid-title-size: var(--ha-card-header-font-size, var(--ha-font-size-l, 1.25rem));
  --pid-title-weight: var(--ha-card-header-font-weight, var(--ha-font-weight-medium, 500));
  --pid-label-size: var(--ha-font-size-xs, 0.75rem);
  --pid-value-size: var(--ha-font-size-l, 1.25rem);
  --pid-body-size: var(--ha-font-size-m, 1rem);
  --pid-secondary-size: var(--ha-font-size-s, 0.875rem);
  position: relative;
  padding: 0;
  font-family: var(--pid-font);
  color: var(--primary-text-color);
}
.pid-shell[data-pid-hi="caution"] { --pid-accent: var(--pid-hi-caution); }
.pid-shell[data-pid-hi="abnormal"] { --pid-accent: var(--pid-hi-abnormal); }
.pid-card {
  position: relative;
  overflow: hidden;
}
.pid-accent {
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--divider-color, #c8c8c8);
  transition: background 0.2s ease;
}
.pid-shell[data-pid-hi="caution"] .pid-accent,
.pid-shell[data-pid-hi="abnormal"] .pid-accent {
  background: var(--pid-accent);
}
.pid-face {
  display: block; width: 100%; border: 0; background: transparent;
  text-align: left; color: inherit; cursor: pointer; padding: 0;
  font: inherit;
}
.pid-face:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: -2px;
}
.pid-body { padding: 12px 16px 12px 18px; }
.pid-head {
  display: flex; justify-content: space-between; align-items: center;
  gap: 8px; margin-bottom: 10px;
}
.pid-settings-btn:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: 1px;
}
  flex: 0 0 auto;
  width: 32px; height: 32px;
  border: 0; background: transparent;
  color: var(--primary-text-color);
  cursor: pointer; border-radius: 4px; padding: 4px;
  display: inline-flex; align-items: center; justify-content: center;
}
.pid-settings-btn svg { width: 20px; height: 20px; fill: currentColor; }
.pid-settings-btn:hover { background: var(--secondary-background-color, #f0f0f0); }
.pid-settings-btn:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: 1px;
}
.pid-isa {
  flex: 0 0 auto;
}
.pid-isa-frame {
  width: 52px;
  border: 1.5px solid var(--divider-color, #c8c8c8);
  border-radius: 3px;
  background: #fffcf7;
  overflow: hidden;
  color: var(--primary-text-color);
  font-weight: 700;
  font-size: 9px;
  line-height: 1;
  text-align: center;
  font-family: var(--pid-font);
}
.pid-isa-eps {
  padding: 4px 0 3px;
  border-bottom: 1px solid var(--divider-color, #c8c8c8);
}
.pid-isa-terms {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
}
.pid-isa-terms span {
  padding: 4px 0 3px;
}
.pid-isa-terms span + span {
  border-left: 1px solid var(--divider-color, #c8c8c8);
}
.pid-title {
  font-family: var(--ha-card-header-font-family, var(--pid-font));
  font-size: var(--pid-title-size);
  font-weight: var(--pid-title-weight);
  line-height: var(--ha-line-height-normal, 1.4);
  color: var(--ha-card-header-color, var(--primary-text-color));
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  min-width: 0; flex: 1 1 auto;
}
.pid-badge {
  flex: 0 0 auto;
  font-family: var(--pid-font);
  font-size: var(--pid-label-size);
  font-weight: var(--ha-font-weight-medium, 500);
  letter-spacing: 0.04em;
  text-transform: uppercase; padding: 2px 8px; border-radius: 4px;
  color: var(--primary-text-color);
  background: transparent;
  border: 1px solid var(--divider-color, #c8c8c8);
}
.pid-hero {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  align-items: start;
}
.pid-metric {
  display: flex; flex-direction: column; gap: 2px; min-width: 0;
}
.pid-metric span {
  font-size: var(--pid-label-size);
  font-weight: var(--ha-font-weight-medium, 500);
  color: var(--secondary-text-color);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pid-metric strong {
  font-size: var(--pid-value-size);
  font-weight: var(--ha-font-weight-normal, 400);
  font-variant-numeric: tabular-nums;
  line-height: var(--ha-line-height-normal, 1.4);
  color: var(--primary-text-color);
  white-space: nowrap;
}
.pid-metric[data-hi="caution"] strong { color: var(--pid-hi-caution); }
.pid-metric[data-hi="abnormal"] strong { color: var(--pid-hi-abnormal); }
.pid-analog {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 8px 0 4px;
}
.pid-vbars {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: stretch;
  justify-items: center;
  gap: 8px;
  min-height: 148px;
}
.pid-err-between {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  align-self: center;
  min-width: 3.25rem;
  min-height: 4.5rem;
  padding: 8px 6px;
  text-align: center;
  border-left: 1px solid var(--divider-color, #ccc);
  border-right: 1px solid var(--divider-color, #ccc);
}
.pid-err-between span {
  font-size: var(--pid-label-size);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--secondary-text-color);
}
.pid-value-focus { display: grid; gap: 12px; }
.pid-value-focus[data-writable="0"] input,
.pid-value-focus[data-writable="0"] [data-apply] { display: none; }
.pid-value-focus[data-writable="1"] [data-value-current] { display: none; }
.pid-value-focus[data-writable="0"] [data-value-current] {
  font-size: var(--pid-value-size);
  font-variant-numeric: tabular-nums;
  font-weight: var(--ha-font-weight-medium, 500);
  justify-self: end;
}
.pid-value-bound {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  font-size: var(--pid-secondary-size);
  color: var(--secondary-text-color);
}
.pid-value-bound strong {
  font-variant-numeric: tabular-nums;
  color: var(--primary-text-color);
}
.pid-vbar,
.pid-hbar {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.pid-vbar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 56px;
}
.pid-vbar-track {
  flex: 1 1 auto;
  width: 14px;
  min-height: 120px;
  border-radius: 4px;
  background: var(--divider-color, #ccc);
  position: relative;
  overflow: hidden;
}
.pid-vbar-fill {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 0%;
  background: var(--primary-text-color);
  opacity: 0.45;
  transition: height 0.25s ease, background 0.2s ease, opacity 0.2s ease;
}
.pid-hbar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.pid-bar-caption,
.pid-vbar-lab,
.pid-cv-lab {
  font-size: var(--pid-label-size);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  text-align: center;
  color: var(--secondary-text-color);
}
.pid-bar-readout {
  font-size: var(--pid-secondary-size);
  font-variant-numeric: tabular-nums;
  font-weight: var(--ha-font-weight-medium, 500);
  color: var(--primary-text-color);
  min-width: 3.25rem;
  text-align: center;
}
.pid-hbar .pid-bar-readout { text-align: right; }
.pid-cv-track {
  height: 16px; border-radius: 4px;
  background: var(--divider-color, #ccc);
  overflow: hidden;
}
.pid-cv-fill {
  height: 100%; width: 0%; border-radius: 2px;
  background: var(--primary-text-color); opacity: 0.45;
  transition: width 0.25s ease, background 0.2s ease, opacity 0.2s ease;
}
.pid-vbar-fill[data-writable="1"],
.pid-cv-fill[data-writable="1"] {
  background: var(--pid-active, #5a8f6e);
  opacity: 1;
}
.pid-cv-fill[data-hi="caution"] {
  background: var(--pid-hi-caution); opacity: 1;
}
.pid-nudge {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  margin: 8px 0 6px;
}
.pid-nudge button {
  border: 1px solid var(--divider-color, #c8c8c8);
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color);
  border-radius: 4px;
  padding: 8px 4px;
  cursor: pointer;
  font-family: var(--pid-font);
  font-size: var(--pid-body-size);
  font-weight: var(--ha-font-weight-medium, 500);
}
.pid-nudge button:disabled { opacity: 0.4; cursor: default; }
.pid-nudge button:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: 1px;
}
.pid-dialog-actions {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px;
}
.pid-dialog-actions button {
  border: 1px solid var(--divider-color, #c8c8c8);
  background: var(--secondary-background-color, #f7f7f7);
  color: var(--primary-text-color);
  border-radius: 4px; padding: 8px 12px; cursor: pointer;
  font-family: var(--pid-font);
  font-size: var(--pid-secondary-size);
  font-weight: var(--ha-font-weight-medium, 500);
}
.pid-face-modes {
  margin-top: 6px;
  margin-bottom: 0;
}
.pid-hint {
  margin-top: 8px;
  font-size: var(--pid-label-size);
  color: var(--secondary-text-color);
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
  font-family: var(--pid-font);
  text-align: left;
  width: 100%;
}
.pid-hint:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: 2px;
}
.pid-dialog {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
  animation: pid-fade-in 0.15s ease;
}
.pid-dialog[hidden] { display: none !important; }
.pid-dialog-backdrop {
  position: absolute; inset: 0;
  background: rgba(0, 0, 0, 0.45);
  border: 0; padding: 0; cursor: pointer;
}
@keyframes pid-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.pid-dialog-panel {
  position: relative; z-index: 1;
  width: min(100%, 380px);
  max-height: min(90vh, 560px);
  overflow: auto;
  border-radius: 12px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.28);
  border: 1px solid var(--divider-color, #ddd);
  animation: pid-rise 0.18s ease;
}
.pid-settings-dialog .pid-dialog-panel {
  width: min(100%, 440px);
  max-height: min(90vh, 640px);
}
.pid-settings-tabs {
  display: flex;
  gap: 0;
  margin: 0 0 12px;
  border: 1px solid var(--divider-color, #c8c8c8);
  border-radius: var(--ha-card-border-radius, 8px);
  overflow: hidden;
}
.pid-settings-tabs button {
  flex: 1;
  border: 0;
  border-right: 1px solid var(--divider-color, #c8c8c8);
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color);
  padding: 8px 4px;
  cursor: pointer;
  font-family: var(--pid-font);
  font-size: var(--pid-label-size);
  font-weight: var(--ha-font-weight-medium, 500);
}
.pid-settings-tabs button:last-child { border-right: 0; }
.pid-settings-tabs button.is-active {
  background: var(--primary-text-color);
  color: var(--card-background-color, #fff);
}
.pid-settings-tabs button:focus-visible {
  outline: 2px solid var(--pid-focus);
  outline-offset: -2px;
}
.pid-tune-hint {
  display: block;
  font-size: var(--pid-label-size);
  opacity: 0.65;
  line-height: 1.3;
  margin: 0 0 10px;
}
.pid-row-check {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
.pid-row-check label {
  display: flex;
  align-items: center;
  gap: 8px;
  width: auto;
}
.pid-row-readonly strong {
  font-weight: var(--ha-font-weight-medium, 500);
}
@keyframes pid-rise {
  from { transform: translateY(8px); opacity: 0.85; }
  to { transform: translateY(0); opacity: 1; }
}
.pid-dialog-head {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; padding: 14px 16px 10px;
  border-bottom: 1px solid var(--divider-color, #e5e5e5);
}
.pid-dialog-title {
  font-family: var(--ha-card-header-font-family, var(--pid-font));
  font-size: var(--pid-title-size);
  font-weight: var(--pid-title-weight);
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pid-dialog-close {
  border: 0; background: transparent; color: var(--primary-text-color);
  opacity: 0.65; cursor: pointer;
  font-size: var(--ha-font-size-xl, 1.5rem); line-height: 1;
  font-family: var(--pid-font);
  padding: 4px 8px; border-radius: 4px;
}
.pid-dialog-close:hover { opacity: 1; background: var(--secondary-background-color, #f0f0f0); }
.pid-dialog-body { padding: 12px 16px 16px; font-family: var(--pid-font); }
.pid-dialog-summary {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px; margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: var(--ha-card-border-radius, 8px);
  background: var(--secondary-background-color, #f5f5f5);
  border: 1px solid var(--divider-color, #ddd);
}
.pid-modes {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 0; margin-bottom: 12px;
  border: 1px solid var(--divider-color, #c8c8c8);
  border-radius: var(--ha-card-border-radius, 8px); overflow: hidden;
}
.pid-modes button {
  border: 0; border-right: 1px solid var(--divider-color, #c8c8c8);
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color);
  padding: 10px 6px; cursor: pointer;
  font-family: var(--pid-font);
  font-size: var(--pid-body-size);
  font-weight: var(--ha-font-weight-medium, 500);
}
.pid-modes button:last-child { border-right: 0; }
.pid-modes button.active {
  background: var(--primary-text-color);
  color: var(--card-background-color, #fff);
}
.pid-editors { display: grid; gap: 8px; }
.pid-editors[hidden],
[data-pane-panel][hidden] { display: none !important; }
.pid-row {
  display: grid; grid-template-columns: 56px 1fr auto; gap: 8px;
  align-items: center; padding: 8px 10px;
  border-radius: var(--ha-card-border-radius, 8px);
  border: 1px solid transparent;
  background: var(--secondary-background-color, #f7f7f7);
}
.pid-row.active-source {
  border-color: var(--primary-text-color);
  background: var(--card-background-color, #fff);
  box-shadow: inset 3px 0 0 var(--primary-text-color);
}
.pid-row label {
  font-size: var(--pid-label-size);
  font-weight: var(--ha-font-weight-medium, 500);
  color: var(--secondary-text-color);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.pid-row input {
  border: 1px solid var(--divider-color, #c8c8c8);
  border-radius: 4px; padding: 8px 10px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color);
  font-family: var(--pid-font);
  font-size: var(--pid-body-size);
  font-variant-numeric: tabular-nums;
  min-width: 0;
}
.pid-row input:focus {
  outline: 2px solid var(--pid-focus);
  outline-offset: 1px; border-color: var(--pid-focus);
}
.pid-row input:disabled { opacity: 0.55; }
.pid-row button {
  border: 1px solid var(--divider-color, #c8c8c8);
  background: var(--secondary-background-color, #f7f7f7);
  color: var(--primary-text-color);
  border-radius: 4px; padding: 8px 12px; cursor: pointer;
  font-family: var(--pid-font);
  font-size: var(--pid-secondary-size);
  font-weight: var(--ha-font-weight-medium, 500);
}
.pid-row button:disabled { opacity: 0.45; cursor: default; }
.pid-note {
  margin-top: 10px;
  font-size: var(--pid-label-size);
  color: var(--secondary-text-color);
  line-height: var(--ha-line-height-normal, 1.4);
}
.pid-missing {
  padding: 16px;
  font-family: var(--pid-font);
  font-size: var(--pid-body-size);
  color: var(--secondary-text-color);
}
@supports (background: color-mix(in srgb, red 50%, blue)) {
  .pid-dialog-summary {
    background: var(--secondary-background-color, #f5f5f5);
    border: 1px solid var(--divider-color, #ddd);
  }
  .pid-row.active-source {
    border-color: color-mix(in srgb, var(--primary-text-color) 45%, transparent);
    background: color-mix(in srgb, var(--primary-text-color) 6%, var(--card-background-color, #fff));
  }
  .pid-row input:focus {
    outline: 2px solid color-mix(in srgb, var(--pid-focus) 45%, transparent);
  }
  .pid-cv-track {
    background: color-mix(in srgb, var(--divider-color, #ccc) 55%, transparent);
  }
}
`;

/** ISA-101 / DCS mode key used on data-pid-mode. */
export function pidModeKey(mode) {
  const m = String(mode ?? "").toLowerCase();
  if (m === "automatic" || m === "auto" || m === "1") return "auto";
  if (m === "remote" || m === "rem" || m === "2") return "rem";
  return "man";
}

export function pidIsaGlyphHtml() {
  return `<div class="pid-isa" aria-hidden="true">
                <div class="pid-isa-frame">
                  <div class="pid-isa-eps">ε</div>
                  <div class="pid-isa-terms">
                    <span class="pid-isa-p">P</span>
                    <span class="pid-isa-i">I</span>
                    <span class="pid-isa-d">D</span>
                  </div>
                </div>
              </div>`;
}

export function pidKpiRowHtml({ metricPrefix = "" } = {}) {
  const p = metricPrefix;
  return `<div class="pid-hero">
              <div class="pid-metric" data-role="pv">
                <span>PV</span>
                <strong data-metric="${p}pv"></strong>
              </div>
              <div class="pid-metric" data-role="sp">
                <span>SP</span>
                <strong data-metric="${p}sp"></strong>
              </div>
              <div class="pid-metric" data-role="err">
                <span>ε</span>
                <strong data-metric="${p}err"></strong>
              </div>
              <div class="pid-metric" data-role="cv">
                <span>MV</span>
                <strong data-metric="${p}cv"></strong>
              </div>
            </div>`;
}

export function pidSettingsButtonHtml() {
  return `<button type="button" class="pid-settings-btn" data-settings="open" aria-label="Controller settings" title="Controller settings">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96c-.5-.4-1.04-.71-1.63-.94l-.36-2.54A.5.5 0 0 0 13.9 2h-3.8a.5.5 0 0 0-.5.42l-.36 2.54c-.59.23-1.13.54-1.63.94l-2.39-.96a.5.5 0 0 0-.6.22L2.8 8.48a.5.5 0 0 0 .12.64l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94L2.92 14.1a.5.5 0 0 0-.12.64l1.92 3.32c.13.24.42.34.7.22l2.39-.96c.5.4 1.04.71 1.63.94l.36 2.54c.05.24.26.42.5.42h3.8c.24 0 .45-.18.5-.42l.36-2.54c.59-.23 1.13-.54 1.63-.94l2.39.96c.28.12.57.02.7-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z"/></svg>
              </button>`;
}

export function pidAnalogBarsHtml() {
  return `<div class="pid-analog">
              <div class="pid-vbars">
                <button type="button" class="pid-vbar" data-bar="pv" data-writable="0" aria-label="PV">
                  <span class="pid-bar-caption">PV</span>
                  <div class="pid-vbar-track"><div class="pid-vbar-fill" data-pv-bar></div></div>
                  <span class="pid-bar-readout" data-metric="pv">—</span>
                </button>
                <div class="pid-metric pid-err-between" data-role="err">
                  <span>ε</span>
                  <strong data-metric="err">—</strong>
                </div>
                <button type="button" class="pid-vbar" data-bar="sp" data-writable="0" aria-label="SP">
                  <span class="pid-bar-caption">SP</span>
                  <div class="pid-vbar-track"><div class="pid-vbar-fill" data-sp-bar></div></div>
                  <span class="pid-bar-readout" data-metric="sp">—</span>
                </button>
              </div>
              <button type="button" class="pid-hbar" data-bar="co" data-writable="0" aria-label="MV">
                <span class="pid-bar-caption">MV</span>
                <div class="pid-cv-track"><div class="pid-cv-fill" data-cv-bar></div></div>
                <span class="pid-bar-readout" data-metric="cv">—</span>
              </button>
            </div>`;
}

export function pidNudgeRowHtml() {
  return `<div class="pid-nudge" role="group" aria-label="Nudge writable analog">
              <button type="button" data-nudge="-1" title="Decrease by 1.0">&lt;&lt;</button>
              <button type="button" data-nudge="-0.1" title="Decrease by 0.1">&lt;</button>
              <button type="button" data-nudge="0.1" title="Increase by 0.1">&gt;</button>
              <button type="button" data-nudge="1" title="Increase by 1.0">&gt;&gt;</button>
            </div>`;
}

export function pidModeRowHtml({ className = "pid-modes pid-face-modes" } = {}) {
  return `<div class="${className}">
              <button type="button" data-mode="0">Man</button>
              <button type="button" data-mode="1">Auto</button>
              <button type="button" data-mode="2">Rem</button>
            </div>`;
}

export function pidAssembledFaceHtml({ includeHint = true } = {}) {
  const hint = includeHint
    ? `<button type="button" class="pid-hint" data-open-editor aria-haspopup="dialog">Tap to adjust</button>`
    : "";
  return `<div class="pid-head">
              ${pidIsaGlyphHtml()}
              <div class="pid-title"></div>
              ${pidSettingsButtonHtml()}
            </div>
            ${pidAnalogBarsHtml()}
            ${pidNudgeRowHtml()}
            ${pidModeRowHtml()}
            ${hint}`;
}

export function pidDialogHtml() {
  return `<div class="pid-dialog pid-value-dialog" hidden role="dialog" aria-modal="true">
          <button type="button" class="pid-dialog-backdrop" data-close-editor aria-label="Dismiss"></button>
          <div class="pid-dialog-panel" role="document">
            <div class="pid-dialog-head">
              <div class="pid-dialog-title" data-value-title>MV</div>
              <button type="button" class="pid-dialog-close" data-close-editor aria-label="Close">×</button>
            </div>
            <div class="pid-dialog-body">
              <div class="pid-value-focus">
                <div class="pid-value-bound">
                  <span>Min</span>
                  <strong data-value-min>—</strong>
                </div>
                <div class="pid-row" data-source="co">
                  <label data-value-label>MV</label>
                  <strong data-value-current>—</strong>
                  <input data-sp="co" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                  <button type="button" data-apply="co">Set</button>
                </div>
                <div class="pid-value-bound">
                  <span>Max</span>
                  <strong data-value-max>—</strong>
                </div>
                <div class="pid-value-bound">
                  <span>Unit</span>
                  <strong data-value-unit></strong>
                </div>
              </div>
              <div class="pid-note"></div>
            </div>
          </div>
        </div>`;
}

export function pidSettingsDialogHtml() {
  return `<div class="pid-dialog pid-settings-dialog" hidden role="dialog" aria-modal="true">
          <button type="button" class="pid-dialog-backdrop" data-close-editor aria-label="Dismiss"></button>
          <div class="pid-dialog-panel" role="document">
            <div class="pid-dialog-head">
              <div class="pid-dialog-title">Controller settings</div>
              <button type="button" class="pid-dialog-close" data-close-editor aria-label="Close">×</button>
            </div>
            <div class="pid-dialog-body">
              <div class="pid-settings-tabs" role="tablist">
                <button type="button" role="tab" data-pane="gains" class="is-active" aria-selected="true">Gains</button>
                <button type="button" role="tab" data-pane="structure" aria-selected="false">Structure</button>
                <button type="button" role="tab" data-pane="output" aria-selected="false">Output</button>
                <button type="button" role="tab" data-pane="filter" aria-selected="false">Filter</button>
              </div>
              <div class="pid-editors" data-pane-panel="gains">
                <div class="pid-row">
                  <label>Kp</label>
                  <input data-tune="kp" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Proportional gain</p>
                <div class="pid-row">
                  <label>Ki</label>
                  <input data-tune="ki" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Integral gain (1/s). 0 selects P / PD with bias u0</p>
                <div class="pid-row">
                  <label>Kd</label>
                  <input data-tune="kd" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Derivative gain</p>
                <div class="pid-row">
                  <label>u0</label>
                  <input data-tune="u0" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Bias applied when Ki is 0</p>
              </div>
              <div class="pid-editors" data-pane-panel="structure" hidden>
                <div class="pid-row">
                  <label>β</label>
                  <input data-tune="beta" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Setpoint weight on P (1 = full error)</p>
                <div class="pid-row pid-row-check">
                  <label>
                    <input data-tune="direct_acting" type="checkbox" />
                    Direct acting
                  </label>
                </div>
                <p class="pid-tune-hint">Off is reverse acting (SP − PV)</p>
                <div class="pid-row pid-row-readonly">
                  <label>Form</label>
                  <strong data-tune-readonly="form">Parallel</strong>
                </div>
                <p class="pid-tune-hint">Parallel is the implemented algorithm</p>
              </div>
              <div class="pid-editors" data-pane-panel="output" hidden>
                <div class="pid-row">
                  <label>CV min</label>
                  <input data-tune="cv_min" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <div class="pid-row">
                  <label>CV max</label>
                  <input data-tune="cv_max" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Output clamps for the manipulated variable</p>
                <div class="pid-row pid-row-check">
                  <label>
                    <input data-tune="hold_when_stopped" type="checkbox" />
                    Hold when stopped
                  </label>
                </div>
                <p class="pid-tune-hint">On holds last CV when the loop is not running; off forces 0</p>
              </div>
              <div class="pid-editors" data-pane-panel="filter" hidden>
                <div class="pid-row">
                  <label>Ts</label>
                  <input data-tune="ts" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Nominal sample time (s)</p>
                <div class="pid-row">
                  <label>Tf/Ts</label>
                  <input data-tune="tf_ts" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                </div>
                <p class="pid-tune-hint">Measurement filter. 0 bypasses the filter</p>
              </div>
              <div class="pid-dialog-actions">
                <button type="button" data-settings-cancel>Cancel</button>
                <button type="button" data-settings-apply>Apply</button>
              </div>
            </div>
          </div>
        </div>`;
}

export function applyPidSettingsPane(root, paneId) {
  const pane = PID_SETTINGS_PANES.includes(paneId) ? paneId : "gains";
  if (!root || typeof root.querySelectorAll !== "function") return pane;
  root.querySelectorAll("button[data-pane]").forEach((btn) => {
    const on = btn.getAttribute("data-pane") === pane;
    btn.classList.toggle("is-active", on);
    btn.setAttribute("aria-selected", on ? "true" : "false");
  });
  root.querySelectorAll("[data-pane-panel]").forEach((panel) => {
    const on = panel.getAttribute("data-pane-panel") === pane;
    if (on) panel.removeAttribute("hidden");
    else panel.setAttribute("hidden", "");
  });
  return pane;
}

function isTruthyTune(val) {
  if (val === true || val === 1 || val === "1" || val === "true") return true;
  if (typeof val === "number") return val !== 0;
  return false;
}

function paintTuneField(root, key, val) {
  const input = root.querySelector(`[data-tune="${key}"]`);
  if (!input) return;
  const focused =
    typeof document !== "undefined" && document.activeElement === input;
  if (focused) return;
  if (input.type === "checkbox") {
    input.checked = isTruthyTune(val);
    return;
  }
  input.value = val == null || val === "" ? "" : formatPidValue(val);
}

export function pidFaceplateMarkup({
  unavailable = false,
  entity = "",
  includeDialog = true,
  includeHint = true,
} = {}) {
  if (unavailable) {
    return `<div class="pid-missing">Entity ${entity} unavailable</div>`;
  }
  const dialog = includeDialog ? `${pidDialogHtml()}${pidSettingsDialogHtml()}` : "";
  return `<div class="pid-shell" data-pid-mode="man" data-pid-hi="normal">
        <div class="pid-card">
        <div class="pid-accent" aria-hidden="true"></div>
          <div class="pid-body">
            ${pidAssembledFaceHtml({ includeHint })}
          </div>
        </div>
        ${dialog}
      </div>`;
}

export function pidFaceplateRootHtml(options = {}) {
  return `<style>${pidFaceplateStyles()}</style>${pidFaceplateMarkup(options)}`;
}

function wrapIsolated(inner) {
  return `<div class="pid-shell" data-pid-mode="auto" data-pid-hi="normal">
        <div class="pid-card">
        <div class="pid-accent" aria-hidden="true"></div>
          <div class="pid-body">${inner}</div>
        </div>
      </div>`;
}

/** Named visual elements that can be mounted without the Lovelace card. */
export const PID_FACEPLATE_ELEMENT_CATALOG = [
  {
    id: "isa-glyph",
    title: "ISA-5.1 glyph",
    description: "ε / P / I / D chrome matching the App Diagram.",
    html: () => wrapIsolated(pidIsaGlyphHtml()),
  },
  {
    id: "kpi-row",
    title: "KPI row",
    description: "PV / SP / ε / CO at two decimal places.",
    html: () => wrapIsolated(pidKpiRowHtml()),
  },
  {
    id: "analog-bars",
    title: "Analog bars",
    description: "Thin tall PV/SP bars, ε between them, and a thicker MV bar.",
    html: () => wrapIsolated(pidAnalogBarsHtml()),
  },
  {
    id: "mode-row",
    title: "Mode row",
    description: "Man / Auto / Rem grayscale selected chrome.",
    html: () => wrapIsolated(pidModeRowHtml()),
  },
];

export const PID_FACEPLATE_ELEMENT_IDS = PID_FACEPLATE_ELEMENT_CATALOG.map(
  (item) => item.id
);

export function pidFaceplateElementHtml(elementId) {
  const item = PID_FACEPLATE_ELEMENT_CATALOG.find((el) => el.id === elementId);
  if (!item) return "";
  return item.html();
}

export function mountPidFaceplateElement(host, elementId, { withStyles = true } = {}) {
  if (!host) return null;
  const html = pidFaceplateElementHtml(elementId);
  if (!html) return null;
  host.innerHTML = withStyles ? `<style>${pidFaceplateStyles()}</style>${html}` : html;
  return host;
}

/**
 * Paint chrome from a loop snapshot. Safe on an isolate or a full faceplate.
 * Dialog drafts are owned by the Lovelace card.
 */
export function applyPidFaceplateState(root, state = {}) {
  if (!root) return;
  const mode = String(state.mode ?? "automatic").toLowerCase();
  const modeKey = state.modeKey || pidModeKey(mode);
  const loopId = state.loopId || "loop";
  const pv = state.pv;
  const sp = state.sp;
  const cv = state.cv;
  const err = state.err !== undefined ? state.err : pidError(sp, pv);
  const errHi = state.errHighlight || pidHighlightSeverity(err, sp, pv);
  const cvHi = state.cvHighlight || pidCvHighlightSeverity(cv, loopId);
  const faceHi = state.highlight || pidFaceplateHighlight(err, sp, pv, cv, loopId);
  const writeTarget =
    state.writeTarget !== undefined
      ? state.writeTarget
      : pidOperatorWriteTarget(mode, {
          spWritable: state.spWritable !== false,
          coWritable: state.coWritable !== false,
        });
  const dialogBar = pidNormalizeBarKey(
    state.dialogBarKey || (writeTarget === "sp" ? "sp" : "co")
  );

  const shell = root.querySelector(".pid-shell") || (root.classList && root.classList.contains("pid-shell") ? root : null);
  if (shell) {
    shell.setAttribute("data-pid-mode", modeKey);
    shell.setAttribute("data-pid-hi", faceHi);
  }

  if (state.title !== undefined) {
    setText(root, ".pid-title", state.title);
    setText(root, "[data-dialog-title]", state.title);
  }
  const badge = root.querySelector("[data-badge]");
  if (badge) badge.textContent = mode;

  setText(root, '[data-metric="pv"]', formatPidValue(pv));
  setText(root, '[data-metric="sp"]', formatPidValue(sp));
  setText(root, '[data-metric="cv"]', formatPidValue(cv));
  setText(root, '[data-metric="dlg-pv"]', formatPidValue(pv));
  setText(root, '[data-metric="dlg-sp"]', formatPidValue(sp));
  setText(root, '[data-metric="dlg-cv"]', formatPidValue(cv));
  const errText = formatPidError(err);
  for (const sel of ['[data-metric="err"]', '[data-metric="dlg-err"]']) {
    setText(root, sel, errText);
  }
  root.querySelectorAll('.pid-metric[data-role="err"]').forEach((el) => {
    el.setAttribute("data-hi", errHi);
  });

  const pvScale = pidPvScaleMax(loopId);
  const pvBar = root.querySelector("[data-pv-bar]");
  if (pvBar) pvBar.style.height = `${pidBarPct(pv, pvScale)}%`;
  const spBar = root.querySelector("[data-sp-bar]");
  if (spBar) spBar.style.height = `${pidBarPct(sp, pvScale)}%`;
  const barEl = root.querySelector("[data-cv-bar]");
  if (barEl) {
    barEl.style.width = `${pidCvBarPct(cv, loopId)}%`;
    barEl.setAttribute("data-hi", cvHi);
  }

  root.querySelectorAll("[data-bar]").forEach((el) => {
    const barKey = el.getAttribute("data-bar");
    const writable =
      (barKey === "sp" && writeTarget === "sp") ||
      (barKey === "co" && writeTarget === "co");
    el.setAttribute("data-writable", writable ? "1" : "0");
  });
  const fillWritable = {
    "[data-pv-bar]": "0",
    "[data-sp-bar]": writeTarget === "sp" ? "1" : "0",
    "[data-cv-bar]": writeTarget === "co" ? "1" : "0",
  };
  for (const [sel, flag] of Object.entries(fillWritable)) {
    const fill = root.querySelector(sel);
    if (fill) fill.setAttribute("data-writable", flag);
  }

  const canNudge = Boolean(writeTarget);
  root.querySelectorAll("[data-nudge]").forEach((btn) => {
    btn.disabled = !canNudge;
  });

  for (const key of PID_TUNE_KEYS) {
    if (!(key in state)) continue;
    paintTuneField(root, key, state[key]);
  }
  const formEl = root.querySelector('[data-tune-readonly="form"]');
  if (formEl) formEl.textContent = state.form || "Parallel";
  applyPidSettingsPane(root, state.settingsPane || "gains");

  applyPidValueDialog(root, {
    barKey: dialogBar,
    loopId,
    value: dialogBar === "sp" ? sp : dialogBar === "pv" ? pv : cv,
    writable:
      (dialogBar === "sp" && writeTarget === "sp") ||
      (dialogBar === "co" && writeTarget === "co"),
  });

  root.querySelectorAll("button[data-mode]").forEach((btn) => {
    const code = btn.getAttribute("data-mode");
    const active =
      (code === "0" && (mode === "manual" || modeKey === "man")) ||
      (code === "1" && (mode === "automatic" || modeKey === "auto")) ||
      (code === "2" && (mode === "remote" || modeKey === "rem"));
    btn.classList.toggle("active", active);
  });

  const sourceKey = modeKey === "man" ? "co" : modeKey;
  root.querySelectorAll("[data-source]").forEach((row) => {
    row.classList.toggle("active-source", row.getAttribute("data-source") === sourceKey);
  });
}
