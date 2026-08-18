/**
 * Isolated PID faceplate elements — shared chrome for Lovelace and the
 * developer sandbox. Operator writes stay in pid-loop-card.js.
 *
 * Named elements: isa-glyph, kpi-row, analog-bars, mode-row.
 * Mount one-at-a-time via mountPidFaceplateElement, or assemble a full face.
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
 * Resolve a faceplate click to a mode, SP-apply, open, or close action.
 *
 * Mode switches must use ``button[data-mode]`` only — never a bare
 * ``[data-mode]`` match — so a card-root accent attribute cannot hijack Set
 * (``data-mode="man"`` → Number("man") → NaN toast).
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
  const barBtn = target.closest("[data-bar]");
  if (barBtn) {
    if (barBtn.getAttribute("data-writable") !== "1") return null;
    return { type: "bar", key: barBtn.getAttribute("data-bar") };
  }
  // Dialog chrome (inputs/labels/panel) must not re-trigger open.
  if (target.closest(".pid-dialog-panel") || target.closest("input[data-sp]")) {
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
  gap: 8px;
  margin: 8px 0 4px;
}
.pid-vbars {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  min-height: 88px;
}
.pid-vbar,
.pid-hbar {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  min-width: 0;
  padding: 4px;
  margin: 0;
  border: 1px solid transparent;
  background: transparent;
  color: inherit;
  cursor: default;
  font: inherit;
  border-radius: 6px;
}
.pid-vbar-track {
  flex: 1;
  min-height: 72px;
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
  transition: height 0.25s ease;
}
.pid-vbar-lab,
.pid-cv-lab {
  font-size: var(--pid-label-size);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  text-align: center;
  color: var(--secondary-text-color);
}
.pid-cv-track {
  height: 10px; border-radius: 4px;
  background: var(--divider-color, #ccc);
  overflow: hidden;
}
.pid-cv-fill {
  height: 100%; width: 0%; border-radius: 2px;
  background: var(--primary-text-color); opacity: 0.45;
  transition: width 0.25s ease, background 0.2s ease, opacity 0.2s ease;
}
.pid-cv-fill[data-hi="caution"] {
  background: var(--pid-hi-caution); opacity: 1;
}
.pid-vbar[data-writable="1"],
.pid-hbar[data-writable="1"] {
  cursor: pointer;
  border-color: var(--primary-text-color);
  box-shadow: inset 0 0 0 1px var(--primary-text-color);
}
.pid-vbar[data-writable="0"],
.pid-hbar[data-writable="0"] {
  pointer-events: none;
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
                <span>CO</span>
                <strong data-metric="${p}cv"></strong>
              </div>
            </div>`;
}

export function pidAnalogBarsHtml() {
  return `<div class="pid-analog">
              <div class="pid-vbars">
                <button type="button" class="pid-vbar" data-bar="pv" data-writable="0" aria-label="PV">
                  <div class="pid-vbar-track"><div class="pid-vbar-fill" data-pv-bar></div></div>
                  <span class="pid-vbar-lab">PV</span>
                </button>
                <button type="button" class="pid-vbar" data-bar="sp" data-writable="0" aria-label="SP">
                  <div class="pid-vbar-track"><div class="pid-vbar-fill" data-sp-bar></div></div>
                  <span class="pid-vbar-lab">SP</span>
                </button>
              </div>
              <button type="button" class="pid-hbar" data-bar="co" data-writable="0" aria-label="CO">
                <div class="pid-cv-track"><div class="pid-cv-fill" data-cv-bar></div></div>
                <span class="pid-cv-lab">CO</span>
              </button>
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
              <div class="pid-badge" data-badge></div>
            </div>
            ${pidKpiRowHtml()}
            ${pidAnalogBarsHtml()}
            ${pidModeRowHtml()}
            ${hint}`;
}

export function pidDialogHtml() {
  return `<div class="pid-dialog" hidden role="dialog" aria-modal="true">
          <button type="button" class="pid-dialog-backdrop" data-close-editor aria-label="Dismiss"></button>
          <div class="pid-dialog-panel" role="document">
            <div class="pid-dialog-head">
              <div class="pid-dialog-title" data-dialog-title></div>
              <button type="button" class="pid-dialog-close" data-close-editor aria-label="Close">×</button>
            </div>
            <div class="pid-dialog-body">
              <div class="pid-dialog-summary">
                <div class="pid-metric" data-role="pv">
                  <span>PV</span>
                  <strong data-metric="dlg-pv"></strong>
                </div>
                <div class="pid-metric" data-role="sp">
                  <span>Active SP</span>
                  <strong data-metric="dlg-sp"></strong>
                </div>
                <div class="pid-metric" data-role="err">
                  <span>ε</span>
                  <strong data-metric="dlg-err"></strong>
                </div>
                <div class="pid-metric" data-role="cv">
                  <span>CO</span>
                  <strong data-metric="dlg-cv"></strong>
                </div>
              </div>
              ${pidModeRowHtml({ className: "pid-modes" })}
              <div class="pid-editors">
                <div class="pid-row" data-source="co">
                  <label>CO</label>
                  <input data-sp="co" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                  <button type="button" data-apply="co">Set</button>
                </div>
                <div class="pid-row" data-source="auto">
                  <label>Auto</label>
                  <input data-sp="auto" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                  <button type="button" data-apply="auto">Set</button>
                </div>
                <div class="pid-row" data-source="rem">
                  <label>Rem</label>
                  <input data-sp="rem" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                  <button type="button" data-apply="rem">Set</button>
                </div>
              </div>
              <div class="pid-note"></div>
            </div>
          </div>
        </div>`;
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
  const dialog = includeDialog ? pidDialogHtml() : "";
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
    description: "Vertical PV and SP, horizontal CO.",
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

function setText(root, sel, value) {
  const el = root.querySelector(sel);
  if (el) el.textContent = value;
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
