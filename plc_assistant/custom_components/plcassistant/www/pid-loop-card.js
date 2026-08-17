/**
 * PLCAssistant PID faceplate card (SWD-183 / SWD-222 / SWD-226 / SWD-227 / SWD-228 / SWD-230).
 *
 * Config: { type: "custom:plcassistant-pid-card", entity: "sensor.plcassistant_pid_level" }
 * Reads climate-like attributes from the compound PID sensor and writes
 * Manual/Auto/Remote mode + SP sources via number.* entities.
 *
 * Compact faceplate (SWD-228 / SWD-360): PV / Active SP / CO at 2dp in a single row;
 * click opens a climate-style dialog for mode + SP edits.
 *
 * Typography (SWD-230): use HA Lovelace design tokens (--ha-font-*) so the
 * faceplate matches surrounding entities / glance cards.
 *
 * Drafts: typed SP inputs use text + inputmode=decimal (not type=number) so
 * intermediate edits like "0." survive live hass updates without caret jumps
 * (SWD-226). Dirty drafts persist across refreshes until Set / Escape / clear.
 *
 * Exported helpers below are the integration↔HMI communication contract and are
 * covered by Node regression tests (SWD-227 / SWD-228 / SWD-230).
 */

/** Display precision for faceplate KPIs (PV / SP / CO / error) and SP editors. */
export const PID_DISPLAY_DIGITS = 2;

/**
 * Format a numeric faceplate value to fixed decimal places, or em-dash.
 * Always uses ``toFixed`` so float noise never leaks into the HMI.
 * Keep digits in sync with DISPLAY_PRECISION in const.py (SWD-230).
 */
export function formatPidValue(value, digits = PID_DISPLAY_DIGITS) {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

/** True when value is present and finite (null/undefined/"" are not). */
export function isPresentFinite(value) {
  if (value === null || value === undefined || value === "") return false;
  const n = typeof value === "number" ? value : Number(String(value).trim().replace(",", "."));
  return Number.isFinite(n);
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
 * (SWD-227: ``data-mode="man"`` → Number("man") → NaN toast).
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

class PlcAssistantPidCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.plcassistant_pid_level" };
  }

  constructor() {
    super();
    this._drafts = {};
    this._dirty = {};
    this._bound = false;
    this._dialogOpen = false;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("plcassistant-pid-card requires `entity`");
    }
    this._config = config;
    this._drafts = {};
    this._dirty = {};
    this._dialogOpen = false;
    this._render(true);
  }

  set hass(hass) {
    this._hass = hass;
    this._render(false);
  }

  getCardSize() {
    return 2;
  }

  _attr(stateObj, key, fallback) {
    if (!stateObj || !stateObj.attributes) return fallback;
    const v = stateObj.attributes[key];
    return v === undefined || v === null ? fallback : v;
  }

  _fmt(value, digits = PID_DISPLAY_DIGITS) {
    return formatPidValue(value, digits);
  }

  _committedText(value) {
    // Committed editor text always matches faceplate display precision (2dp).
    const text = formatPidValue(value, PID_DISPLAY_DIGITS);
    return text === "—" ? "0.00" : text;
  }

  async _setNumber(entityId, value) {
    if (!this._hass || !entityId) return;
    const numeric = numberServiceValue(value);
    if (numeric === null) return;
    // Keep entity_id in serviceData (legacy-compatible Lovelace shape) alongside
    // the finite float — do not rely solely on a 4th-arg target.
    await this._hass.callService("number", "set_value", {
      entity_id: entityId,
      value: numeric,
    });
  }

  async _setMode(code) {
    const st = this._hass?.states?.[this._config.entity];
    const modeEntity = this._attr(st, "mode_entity", null);
    if (!modeEntity) return;
    // Mode codes are 0/1/2 — never pass label strings like "man".
    const numeric = numberServiceValue(code);
    if (numeric === null) return;
    await this._setNumber(modeEntity, numeric);
  }

  _inputValue(key, fallback) {
    if (this._dirty[key] && this._drafts[key] !== undefined) {
      return this._drafts[key];
    }
    return this._committedText(fallback);
  }

  _captureFocusedDrafts() {
    if (!this._root) return;
    for (const key of ["man", "auto", "rem"]) {
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      if (!input) continue;
      // Snapshot the live input while focused so a hass restomp mid-edit can
      // restore text — but do not mark dirty on focus alone (SWD-226 review).
      if (document.activeElement === input) {
        this._drafts[key] = input.value;
      } else if (this._dirty[key]) {
        this._drafts[key] = input.value;
      }
    }
  }

  _clearDraft(key) {
    delete this._drafts[key];
    delete this._dirty[key];
  }

  _parseSp(raw) {
    return parseSpValue(raw);
  }

  _applySp(key) {
    const input = this._root?.querySelector(`input[data-sp="${key}"]`);
    const st = this._hass?.states?.[this._config.entity];
    const entityFor = {
      man: this._attr(st, "sp_man_entity", ""),
      auto: this._attr(st, "sp_auto_entity", ""),
      rem: this._attr(st, "sp_rem_entity", ""),
    };
    const entity = entityFor[key];
    if (!input || !entity || String(entity).startsWith("sensor.")) return;
    const parsed = this._parseSp(input.value);
    if (parsed === null) return;
    const committed = commitSpValue(parsed);
    if (committed === null) return;
    this._clearDraft(key);
    input.value = this._committedText(committed);
    this._setNumber(entity, committed);
  }

  _openDialog() {
    if (this._dialogOpen) return;
    this._dialogOpen = true;
    this._render(false);
  }

  _closeDialog() {
    if (!this._dialogOpen) return;
    this._dialogOpen = false;
    this._render(false);
  }

  _bindEditors() {
    if (!this._root || this._bound) return;
    this._bound = true;
    this._root.addEventListener("click", (ev) => {
      const action = resolveFaceplateClick(ev.target);
      if (!action) return;
      if (action.type === "open") {
        this._openDialog();
        return;
      }
      if (action.type === "close") {
        this._closeDialog();
        return;
      }
      if (action.type === "mode") {
        this._setMode(action.code);
        return;
      }
      if (action.type === "apply") {
        this._applySp(action.key);
      }
    });
    this._root.addEventListener("input", (ev) => {
      const input = ev.target.closest("input[data-sp]");
      if (!input) return;
      const key = input.getAttribute("data-sp");
      if (!key) return;
      this._drafts[key] = input.value;
      this._dirty[key] = true;
    });
    this._root.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && this._dialogOpen) {
        const onInput = ev.target.closest?.("input[data-sp]");
        if (!onInput) {
          ev.preventDefault();
          this._closeDialog();
          return;
        }
      }
      const input = ev.target.closest("input[data-sp]");
      if (!input) return;
      const key = input.getAttribute("data-sp");
      if (!key) return;
      if (ev.key === "Enter") {
        ev.preventDefault();
        this._applySp(key);
        input.blur();
      } else if (ev.key === "Escape") {
        ev.preventDefault();
        this._clearDraft(key);
        const st = this._hass?.states?.[this._config.entity];
        const values = {
          man: this._attr(st, "sp_man", 0),
          auto: this._attr(st, "sp_auto", 0),
          rem: this._attr(st, "sp_rem", 0),
        };
        input.value = this._committedText(values[key]);
        input.blur();
      }
    });
    // Do not clear dirty drafts on blur — live hass updates must not reformat
    // an in-progress edit after an accidental focus loss (SWD-226).
  }

  _modeKey(mode) {
    if (mode === "automatic") return "auto";
    if (mode === "remote") return "rem";
    return "man";
  }

  _cvBarPct(cv, loopId) {
    const n = Number(cv);
    if (!Number.isFinite(n)) return 0;
    const max = loopId === "flow" ? 100 : 6;
    return Math.max(0, Math.min(100, (Math.abs(n) / max) * 100));
  }

  _render(forceRebuild) {
    if (!this._config) return;
    const hass = this._hass;
    const st = hass?.states?.[this._config.entity];
    const mode = (st?.state || "manual").toLowerCase();
    const modeKey = this._modeKey(mode);
    const loopId = this._attr(st, "loop_id", "loop");
    const title =
      this._config.title ||
      st?.attributes?.friendly_name ||
      `PID ${loopId}`;

    const pv = this._attr(st, "pv", null);
    const sp = this._attr(st, "sp", null);
    const cv = this._attr(st, "cv", null);
    const spMan = this._attr(st, "sp_man", 0);
    const spAuto = this._attr(st, "sp_auto", 0);
    const spRem = this._attr(st, "sp_rem", 0);
    const modeEntity = this._attr(st, "mode_entity", "");
    const spAutoEntity = this._attr(st, "sp_auto_entity", "");
    const autoDisabled = String(spAutoEntity).startsWith("sensor.");
    const unavailable = !st;
    const err =
      isPresentFinite(sp) && isPresentFinite(pv)
        ? Number(sp) - Number(pv)
        : null;

    if (!this._root) {
      this.innerHTML = "";
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
      forceRebuild = true;
    }

    this._captureFocusedDrafts();

    if (forceRebuild || !this._root.querySelector(".pid-shell")) {
      this._bound = false;
      this._root.innerHTML = `
      <style>
        .pid-shell {
          --pid-man: #c47800;
          --pid-auto: #0d9488;
          --pid-rem: #3b6ea5;
          --pid-accent: var(--pid-man);
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
        .pid-shell[data-pid-mode="man"] { --pid-accent: var(--pid-man); }
        .pid-shell[data-pid-mode="auto"] { --pid-accent: var(--pid-auto); }
        .pid-shell[data-pid-mode="rem"] { --pid-accent: var(--pid-rem); }
        .pid-card {
          position: relative;
          overflow: hidden;
        }
        .pid-accent {
          position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
          background: var(--pid-accent);
          transition: background 0.2s ease;
        }
        .pid-face {
          display: block; width: 100%; border: 0; background: transparent;
          text-align: left; color: inherit; cursor: pointer; padding: 0;
          font: inherit;
        }
        .pid-face:focus-visible {
          outline: 2px solid var(--pid-accent);
          outline-offset: -2px;
        }
        .pid-body { padding: 12px 16px 12px 18px; }
        .pid-head {
          display: flex; justify-content: space-between; align-items: center;
          gap: 8px; margin-bottom: 10px;
        }
        .pid-title {
          font-family: var(--ha-card-header-font-family, var(--pid-font));
          font-size: var(--pid-title-size);
          font-weight: var(--pid-title-weight);
          line-height: var(--ha-line-height-normal, 1.4);
          color: var(--ha-card-header-color, var(--primary-text-color));
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
          min-width: 0;
        }
        .pid-badge {
          flex: 0 0 auto;
          font-family: var(--pid-font);
          font-size: var(--pid-label-size);
          font-weight: var(--ha-font-weight-medium, 500);
          letter-spacing: 0.04em;
          text-transform: uppercase; padding: 2px 8px; border-radius: 4px;
          color: #fff; background: var(--pid-accent);
        }
        .pid-hero {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
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
        .pid-metric[data-role="sp"] strong { color: var(--pid-accent); }
        .pid-metric .pid-sub {
          font-size: var(--pid-label-size);
          color: var(--secondary-text-color);
          font-variant-numeric: tabular-nums;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .pid-cv-track {
          margin-top: 10px; height: 3px; border-radius: 2px;
          background: var(--divider-color, #ccc);
          overflow: hidden;
        }
        .pid-cv-fill {
          height: 100%; width: 0%; border-radius: 2px;
          background: var(--pid-accent); transition: width 0.25s ease;
        }
        .pid-hint {
          margin-top: 8px;
          font-size: var(--pid-label-size);
          color: var(--secondary-text-color);
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
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
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
        .pid-modes button[data-mode="0"].active { background: var(--pid-man); color: #fff; }
        .pid-modes button[data-mode="1"].active { background: var(--pid-auto); color: #fff; }
        .pid-modes button[data-mode="2"].active { background: var(--pid-rem); color: #fff; }
        .pid-editors { display: grid; gap: 8px; }
        .pid-row {
          display: grid; grid-template-columns: 56px 1fr auto; gap: 8px;
          align-items: center; padding: 8px 10px;
          border-radius: var(--ha-card-border-radius, 8px);
          border: 1px solid transparent;
          background: var(--secondary-background-color, #f7f7f7);
        }
        .pid-row.active-source {
          border-color: var(--pid-accent);
          background: var(--card-background-color, #fff);
          box-shadow: inset 3px 0 0 var(--pid-accent);
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
          outline: 2px solid var(--pid-accent);
          outline-offset: 1px; border-color: var(--pid-accent);
        }
        .pid-row input:disabled { opacity: 0.55; }
        .pid-row button {
          border: 1px solid var(--pid-accent);
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
            background:
              linear-gradient(135deg,
                color-mix(in srgb, var(--pid-accent) 12%, transparent),
                color-mix(in srgb, var(--secondary-background-color, #f5f5f5) 88%, transparent));
            border: 1px solid color-mix(in srgb, var(--pid-accent) 28%, var(--divider-color, #ddd));
          }
          .pid-row.active-source {
            border-color: color-mix(in srgb, var(--pid-accent) 55%, transparent);
            background: color-mix(in srgb, var(--pid-accent) 10%, var(--card-background-color, #fff));
          }
          .pid-row input:focus {
            outline: 2px solid color-mix(in srgb, var(--pid-accent) 45%, transparent);
          }
          .pid-row button {
            border-color: color-mix(in srgb, var(--pid-accent) 40%, var(--divider-color, #ccc));
            background: color-mix(in srgb, var(--pid-accent) 12%, transparent);
          }
          .pid-cv-track {
            background: color-mix(in srgb, var(--divider-color, #ccc) 55%, transparent);
          }
        }
      </style>
      ${
        unavailable
          ? `<div class="pid-missing">Entity ${this._config.entity} unavailable</div>`
          : `<div class="pid-shell" data-pid-mode="man">
        <div class="pid-card">
        <div class="pid-accent" aria-hidden="true"></div>
        <button type="button" class="pid-face" data-open-editor aria-haspopup="dialog">
          <div class="pid-body">
            <div class="pid-head">
              <div class="pid-title"></div>
              <div class="pid-badge" data-badge></div>
            </div>
            <div class="pid-hero">
              <div class="pid-metric" data-role="pv">
                <span>PV</span>
                <strong data-metric="pv"></strong>
              </div>
              <div class="pid-metric" data-role="sp">
                <span>SP</span>
                <strong data-metric="sp"></strong>
                <div class="pid-sub" data-metric="err"></div>
              </div>
              <div class="pid-metric" data-role="cv">
                <span>CO</span>
                <strong data-metric="cv"></strong>
              </div>
            </div>
            <div class="pid-cv-track"><div class="pid-cv-fill" data-cv-bar></div></div>
            <div class="pid-hint">Tap to adjust</div>
          </div>
        </button>
        </div>
        <div class="pid-dialog" hidden role="dialog" aria-modal="true">
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
                  <div class="pid-sub" data-metric="dlg-err"></div>
                </div>
                <div class="pid-metric" data-role="cv">
                  <span>CO</span>
                  <strong data-metric="dlg-cv"></strong>
                </div>
              </div>
              <div class="pid-modes">
                <button type="button" data-mode="0">Man</button>
                <button type="button" data-mode="1">Auto</button>
                <button type="button" data-mode="2">Rem</button>
              </div>
              <div class="pid-editors">
                <div class="pid-row" data-source="man">
                  <label>Man</label>
                  <input data-sp="man" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" />
                  <button type="button" data-apply="man">Set</button>
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
        </div>
      </div>`
      }
    `;
      this._bindEditors();
    }

    if (unavailable) {
      const missing = this._root.querySelector(".pid-missing");
      if (missing) missing.textContent = `Entity ${this._config.entity} unavailable`;
      return;
    }

    const shell = this._root.querySelector(".pid-shell");
    if (shell) shell.setAttribute("data-pid-mode", modeKey);

    const titleEl = this._root.querySelector(".pid-title");
    const badgeEl = this._root.querySelector("[data-badge]");
    const dlgTitle = this._root.querySelector("[data-dialog-title]");
    if (titleEl) titleEl.textContent = title;
    if (badgeEl) badgeEl.textContent = mode;
    if (dlgTitle) dlgTitle.textContent = title;

    const setMetric = (sel, value) => {
      const el = this._root.querySelector(sel);
      if (el) el.textContent = this._fmt(value);
    };
    setMetric('[data-metric="pv"]', pv);
    setMetric('[data-metric="sp"]', sp);
    setMetric('[data-metric="cv"]', cv);
    setMetric('[data-metric="dlg-pv"]', pv);
    setMetric('[data-metric="dlg-sp"]', sp);
    setMetric('[data-metric="dlg-cv"]', cv);

    const errText =
      err === null ? "err —" : `err ${err >= 0 ? "+" : ""}${this._fmt(err)}`;
    for (const sel of ['[data-metric="err"]', '[data-metric="dlg-err"]']) {
      const errEl = this._root.querySelector(sel);
      if (errEl) errEl.textContent = errText;
    }

    const barEl = this._root.querySelector("[data-cv-bar]");
    if (barEl) barEl.style.width = `${this._cvBarPct(cv, loopId)}%`;

    const dialog = this._root.querySelector(".pid-dialog");
    if (dialog) {
      if (this._dialogOpen) dialog.removeAttribute("hidden");
      else dialog.setAttribute("hidden", "");
    }

    this._root.querySelectorAll("button[data-mode]").forEach((btn) => {
      const code = btn.getAttribute("data-mode");
      const active =
        (code === "0" && mode === "manual") ||
        (code === "1" && mode === "automatic") ||
        (code === "2" && mode === "remote");
      btn.classList.toggle("active", active);
    });

    this._root.querySelectorAll("[data-source]").forEach((row) => {
      row.classList.toggle(
        "active-source",
        row.getAttribute("data-source") === modeKey
      );
    });

    const values = { man: spMan, auto: spAuto, rem: spRem };
    for (const key of ["man", "auto", "rem"]) {
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      if (!input) continue;
      const focused = document.activeElement === input;
      if (key === "auto") {
        input.disabled = autoDisabled;
        const apply = this._root.querySelector('[data-apply="auto"]');
        if (apply) apply.disabled = autoDisabled;
      }
      // Never rewrite a focused or dirty draft from live HA values.
      // Focus alone (no typing) still skips rewrite to protect caret/selection;
      // after blur without input, _dirty is false so live SP resumes.
      if (focused || this._dirty[key]) {
        if (this._drafts[key] !== undefined && input.value !== this._drafts[key]) {
          input.value = this._drafts[key];
        }
        continue;
      }
      input.value = this._inputValue(key, values[key]);
    }

    const note = this._root.querySelector(".pid-note");
    if (note) {
      note.textContent =
        `Mode via ${modeEntity || "—"}. Set writes the SP and flips to that source. Enter commits · Esc cancels draft (or closes).`;
    }
  }
}

// Guard double-load (resource + extra_js, or upgrade re-exec).
if (!customElements.get("plcassistant-pid-card")) {
  customElements.define("plcassistant-pid-card", PlcAssistantPidCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "plcassistant-pid-card",
    name: "PLCAssistant PID Card",
    description: "Faceplate for sensor.plcassistant_pid_* compound entities",
  });
}
