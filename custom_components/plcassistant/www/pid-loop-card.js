/**
 * PLCAssistant PID faceplate card.
 *
 * Config: { type: "custom:plcassistant-pid-card", entity: "sensor.plcassistant_pid_level" }
 * Reads climate-like attributes from the compound PID sensor and writes
 * Manual/Auto/Remote mode + SP sources via number.* entities.
 *
 * Analog-controller faceplate chrome lives in pid-faceplate-elements.js so the
 * same elements can be mounted in the developer sandbox without Home Assistant.
 *
 * Highlighted bar is the writable analog (CO in MAN, SP in AUTO when the Auto
 * entity is a Number). Tap the bar to set from pointer position; typed Set
 * remains in the dialog.
 *
 * Colour (ISA-101 high-performance HMI): grayscale / Home Assistant tokens in
 * normal operation. Colour is reserved for caution (--warning-color) and
 * abnormal (--error-color) — never for Man / Auto / Rem identity.
 *
 * Drafts: typed SP inputs use text + inputmode=decimal (not type=number) so
 * intermediate edits like "0." survive live hass updates without caret jumps.
 * Dirty drafts persist across refreshes until Set / Escape / clear.
 *
 * Re-exported helpers are the integration↔HMI communication contract and are
 * covered by Node regression tests.
 */

import {
  PID_DISPLAY_DIGITS,
  PID_ERR_CAUTION_FRAC,
  PID_ERR_ABNORMAL_FRAC,
  PID_ERR_SCALE_FLOOR,
  PID_CV_MAX_FLOW,
  PID_CV_MAX_LEVEL,
  PID_CV_CLAMP_FRAC,
  PID_PV_MAX_LEVEL,
  PID_PV_MAX_FLOW,
  formatPidValue,
  formatPidError,
  isPresentFinite,
  pidError,
  pidHighlightSeverity,
  pidCvScaleMax,
  pidCvBarPct,
  pidCvHighlightSeverity,
  pidFaceplateHighlight,
  pidPvScaleMax,
  pidBarPct,
  pidOperatorWriteTarget,
  pidBarValueFromPointer,
  commitSpValue,
  parseSpValue,
  numberServiceValue,
  resolveFaceplateClick,
  pidModeKey,
  pidFaceplateRootHtml,
  applyPidFaceplateState,
} from "./pid-faceplate-elements.js";

export {
  PID_DISPLAY_DIGITS,
  PID_ERR_CAUTION_FRAC,
  PID_ERR_ABNORMAL_FRAC,
  PID_ERR_SCALE_FLOOR,
  PID_CV_MAX_FLOW,
  PID_CV_MAX_LEVEL,
  PID_CV_CLAMP_FRAC,
  PID_PV_MAX_LEVEL,
  PID_PV_MAX_FLOW,
  formatPidValue,
  formatPidError,
  isPresentFinite,
  pidError,
  pidHighlightSeverity,
  pidCvScaleMax,
  pidCvBarPct,
  pidCvHighlightSeverity,
  pidFaceplateHighlight,
  pidPvScaleMax,
  pidBarPct,
  pidOperatorWriteTarget,
  pidBarValueFromPointer,
  commitSpValue,
  parseSpValue,
  numberServiceValue,
  resolveFaceplateClick,
  pidModeKey,
};

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
    return 3;
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
    for (const key of ["co", "auto", "rem"]) {
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      if (!input) continue;
      // Snapshot the live input while focused so a hass restomp mid-edit can
      // restore text — but do not mark dirty on focus alone.
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
      co: this._attr(st, "cv_man_entity", ""),
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

  _applyBarClick(ev, key) {
    const barBtn = ev.target?.closest?.("[data-bar]");
    const track = barBtn?.querySelector?.(".pid-vbar-track, .pid-cv-track");
    if (!track || typeof track.getBoundingClientRect !== "function") return;
    const st = this._hass?.states?.[this._config.entity];
    const loopId = this._attr(st, "loop_id", "loop");
    let min = 0;
    let max;
    let orientation;
    if (key === "co") {
      max = pidCvScaleMax(loopId);
      orientation = "horizontal";
    } else if (key === "sp") {
      max = pidPvScaleMax(loopId);
      orientation = "vertical";
    } else {
      return;
    }
    const rect = track.getBoundingClientRect();
    const raw = pidBarValueFromPointer(
      rect,
      ev.clientX,
      ev.clientY,
      min,
      max,
      orientation
    );
    const committed = commitSpValue(raw);
    if (committed === null) return;
    const entity =
      key === "co"
        ? this._attr(st, "cv_man_entity", "")
        : this._attr(st, "sp_auto_entity", "");
    if (!entity || String(entity).startsWith("sensor.")) return;
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
        return;
      }
      if (action.type === "bar") {
        this._applyBarClick(ev, action.key);
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
          co: this._attr(st, "co_man", this._attr(st, "cv", 0)),
          auto: this._attr(st, "sp_auto", 0),
          rem: this._attr(st, "sp_rem", 0),
        };
        input.value = this._committedText(values[key]);
        input.blur();
      }
    });
    // Do not clear dirty drafts on blur — live hass updates must not reformat
    // an in-progress edit after an accidental focus loss.
  }

  _modeKey(mode) {
    return pidModeKey(mode);
  }

  _cvBarPct(cv, loopId) {
    return pidCvBarPct(cv, loopId);
  }

  _render(forceRebuild) {
    if (!this._config) return;
    const hass = this._hass;
    const st = hass?.states?.[this._config.entity];
    const mode = (st?.state || "automatic").toLowerCase();
    const loopId = this._attr(st, "loop_id", "loop");
    const title =
      this._config.title ||
      st?.attributes?.friendly_name ||
      `PID ${loopId}`;

    const pv = this._attr(st, "pv", null);
    const sp = this._attr(st, "sp", null);
    const cv = this._attr(st, "cv", null);
    const spAuto = this._attr(st, "sp_auto", 0);
    const spRem = this._attr(st, "sp_rem", 0);
    const modeEntity = this._attr(st, "mode_entity", "");
    const spAutoEntity = this._attr(st, "sp_auto_entity", "");
    const cvManEntity = this._attr(st, "cv_man_entity", "");
    const autoDisabled = String(spAutoEntity).startsWith("sensor.");
    const remDisabled = true;
    const coMan = this._attr(st, "co_man", cv);
    const unavailable = !st;

    if (!this._root) {
      this.innerHTML = "";
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
      forceRebuild = true;
    }

    this._captureFocusedDrafts();

    if (forceRebuild || !this._root.querySelector(".pid-shell")) {
      this._bound = false;
      this._root.innerHTML = pidFaceplateRootHtml({
        unavailable,
        entity: this._config.entity,
        includeDialog: true,
        includeHint: true,
      });
      this._bindEditors();
    }

    if (unavailable) {
      const missing = this._root.querySelector(".pid-missing");
      if (missing) missing.textContent = `Entity ${this._config.entity} unavailable`;
      return;
    }

    applyPidFaceplateState(this._root, {
      title,
      mode,
      loopId,
      pv,
      sp,
      cv,
      spWritable: !autoDisabled,
      coWritable: Boolean(cvManEntity),
    });

    const dialog = this._root.querySelector(".pid-dialog");
    if (dialog) {
      if (this._dialogOpen) dialog.removeAttribute("hidden");
      else dialog.setAttribute("hidden", "");
    }

    const values = { co: coMan, auto: spAuto, rem: spRem };
    for (const key of ["co", "auto", "rem"]) {
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      if (!input) continue;
      const focused = document.activeElement === input;
      if (key === "auto") {
        input.disabled = autoDisabled;
        const apply = this._root.querySelector('[data-apply="auto"]');
        if (apply) apply.disabled = autoDisabled;
      }
      if (key === "rem") {
        input.disabled = remDisabled;
        const apply = this._root.querySelector('[data-apply="rem"]');
        if (apply) apply.disabled = remDisabled;
      }
      if (key === "co") {
        input.disabled = !cvManEntity;
        const apply = this._root.querySelector('[data-apply="co"]');
        if (apply) apply.disabled = !cvManEntity;
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
        `Mode via ${modeEntity || "—"}. MAN writes CO; AUTO writes local SP; REM is cascade/remote (read-only). Click the highlighted bar or Set. Enter commits · Esc cancels draft (or closes).`;
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
