/**
 * PLCAssistant PID faceplate card (SWD-183 / SWD-222).
 *
 * Config: { type: "custom:plcassistant-pid-card", entity: "sensor.plcassistant_pid_level" }
 * Reads climate-like attributes from the compound PID sensor and writes
 * Manual/Auto/Remote mode + SP sources via number.* entities.
 *
 * Drafts: typed SP inputs are preserved across hass updates so live PV/SP/CV
 * refreshes do not stomp in-progress edits (SWD-222).
 */
class PlcAssistantPidCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.plcassistant_pid_level" };
  }

  constructor() {
    super();
    this._drafts = {};
    this._bound = false;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("plcassistant-pid-card requires `entity`");
    }
    this._config = config;
    this._drafts = {};
    this._render(true);
  }

  set hass(hass) {
    this._hass = hass;
    this._render(false);
  }

  getCardSize() {
    return 4;
  }

  _attr(stateObj, key, fallback) {
    if (!stateObj || !stateObj.attributes) return fallback;
    const v = stateObj.attributes[key];
    return v === undefined || v === null ? fallback : v;
  }

  _fmt(value, digits = 3) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "—";
    return n.toFixed(digits);
  }

  async _setNumber(entityId, value) {
    if (!this._hass || !entityId) return;
    await this._hass.callService("number", "set_value", {
      entity_id: entityId,
      value: Number(value),
    });
  }

  async _setMode(code) {
    const st = this._hass?.states?.[this._config.entity];
    const modeEntity = this._attr(st, "mode_entity", null);
    if (!modeEntity) return;
    await this._setNumber(modeEntity, code);
  }

  _inputValue(key, fallback) {
    if (this._drafts[key] !== undefined) return this._drafts[key];
    const n = Number(fallback);
    return Number.isFinite(n) ? String(n) : "0";
  }

  _captureFocusedDrafts() {
    if (!this._root) return;
    for (const key of ["man", "auto", "rem"]) {
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      if (!input) continue;
      if (document.activeElement === input) {
        this._drafts[key] = input.value;
      }
    }
  }

  _bindEditors() {
    if (!this._root || this._bound) return;
    this._bound = true;
    this._root.addEventListener("click", (ev) => {
      const modeBtn = ev.target.closest("[data-mode]");
      if (modeBtn) {
        this._setMode(modeBtn.getAttribute("data-mode"));
        return;
      }
      const applyBtn = ev.target.closest("[data-apply]");
      if (!applyBtn || applyBtn.disabled) return;
      const key = applyBtn.getAttribute("data-apply");
      const input = this._root.querySelector(`input[data-sp="${key}"]`);
      const st = this._hass?.states?.[this._config.entity];
      const entityFor = {
        man: this._attr(st, "sp_man_entity", ""),
        auto: this._attr(st, "sp_auto_entity", ""),
        rem: this._attr(st, "sp_rem_entity", ""),
      };
      const entity = entityFor[key];
      if (!input || !entity || String(entity).startsWith("sensor.")) return;
      delete this._drafts[key];
      this._setNumber(entity, input.value);
    });
    this._root.addEventListener("input", (ev) => {
      const input = ev.target.closest("input[data-sp]");
      if (!input) return;
      const key = input.getAttribute("data-sp");
      if (key) this._drafts[key] = input.value;
    });
    this._root.addEventListener("focusout", (ev) => {
      const input = ev.target.closest("input[data-sp]");
      if (!input) return;
      const key = input.getAttribute("data-sp");
      if (!key) return;
      // Clear abandoned drafts after blur so live HA values can reappear.
      // Keep draft only if focus moved to the matching Set button.
      const next = ev.relatedTarget;
      if (next && next.getAttribute && next.getAttribute("data-apply") === key) {
        return;
      }
      delete this._drafts[key];
    });
  }

  _render(forceRebuild) {
    if (!this._config) return;
    const hass = this._hass;
    const st = hass?.states?.[this._config.entity];
    const mode = (st?.state || "manual").toLowerCase();
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

    if (!this._root) {
      this.innerHTML = "";
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
      forceRebuild = true;
    }

    this._captureFocusedDrafts();

    if (forceRebuild || !this._root.querySelector(".pid-card")) {
      this._bound = false;
      this._root.innerHTML = `
      <style>
        .pid-card { padding: 14px 16px 16px; font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
        .pid-head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; margin-bottom: 10px; }
        .pid-title { font-size: 1.05rem; font-weight: 500; }
        .pid-mode { font-size: 0.78rem; opacity: 0.75; text-transform: capitalize; }
        .pid-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
        .pid-metric { display: flex; flex-direction: column; gap: 2px; }
        .pid-metric span { font-size: 0.7rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.04em; }
        .pid-metric strong { font-size: 1.35rem; font-variant-numeric: tabular-nums; font-weight: 500; }
        .pid-modes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }
        .pid-modes button {
          border: 1px solid var(--divider-color, #c8c8c8);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          border-radius: 6px;
          padding: 8px 6px;
          cursor: pointer;
          font-size: 0.82rem;
        }
        .pid-modes button.active {
          border-color: var(--primary-color, #03a9f4);
          color: var(--primary-color, #03a9f4);
          font-weight: 600;
        }
        .pid-editors { display: grid; gap: 8px; }
        .pid-row { display: grid; grid-template-columns: 72px 1fr auto; gap: 8px; align-items: center; }
        .pid-row label { font-size: 0.78rem; opacity: 0.75; }
        .pid-row input {
          border: 1px solid var(--divider-color, #c8c8c8);
          border-radius: 6px;
          padding: 6px 8px;
          background: var(--secondary-background-color, #fafafa);
          color: var(--primary-text-color);
          font-size: 0.9rem;
        }
        .pid-row button {
          border: 1px solid var(--divider-color, #c8c8c8);
          background: transparent;
          color: var(--primary-text-color);
          border-radius: 6px;
          padding: 6px 10px;
          cursor: pointer;
          font-size: 0.78rem;
        }
        .pid-note { margin-top: 8px; font-size: 0.72rem; opacity: 0.65; }
        .pid-missing { padding: 16px; opacity: 0.7; }
      </style>
      ${
        unavailable
          ? `<div class="pid-missing">Entity ${this._config.entity} unavailable</div>`
          : `<div class="pid-card">
        <div class="pid-head">
          <div class="pid-title"></div>
          <div class="pid-mode"></div>
        </div>
        <div class="pid-grid">
          <div class="pid-metric"><span>PV</span><strong data-metric="pv"></strong></div>
          <div class="pid-metric"><span>SP</span><strong data-metric="sp"></strong></div>
          <div class="pid-metric"><span>CV</span><strong data-metric="cv"></strong></div>
        </div>
        <div class="pid-modes">
          <button data-mode="0">Man</button>
          <button data-mode="1">Auto</button>
          <button data-mode="2">Rem</button>
        </div>
        <div class="pid-editors">
          <div class="pid-row">
            <label>SP Man</label>
            <input data-sp="man" type="number" step="any" />
            <button data-apply="man">Set</button>
          </div>
          <div class="pid-row">
            <label>SP Auto</label>
            <input data-sp="auto" type="number" step="any" />
            <button data-apply="auto">Set</button>
          </div>
          <div class="pid-row">
            <label>SP Rem</label>
            <input data-sp="rem" type="number" step="any" />
            <button data-apply="rem">Set</button>
          </div>
        </div>
        <div class="pid-note"></div>
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

    const titleEl = this._root.querySelector(".pid-title");
    const modeEl = this._root.querySelector(".pid-mode");
    if (titleEl) titleEl.textContent = title;
    if (modeEl) modeEl.textContent = mode;

    const pvEl = this._root.querySelector('[data-metric="pv"]');
    const spEl = this._root.querySelector('[data-metric="sp"]');
    const cvEl = this._root.querySelector('[data-metric="cv"]');
    if (pvEl) pvEl.textContent = this._fmt(pv);
    if (spEl) spEl.textContent = this._fmt(sp);
    if (cvEl) cvEl.textContent = this._fmt(cv, 2);

    this._root.querySelectorAll("[data-mode]").forEach((btn) => {
      const code = btn.getAttribute("data-mode");
      const active =
        (code === "0" && mode === "manual") ||
        (code === "1" && mode === "automatic") ||
        (code === "2" && mode === "remote");
      btn.classList.toggle("active", active);
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
      if (!focused && this._drafts[key] === undefined) {
        input.value = this._inputValue(key, values[key]);
      } else if (!focused && this._drafts[key] !== undefined) {
        input.value = this._drafts[key];
      }
    }

    const note = this._root.querySelector(".pid-note");
    if (note) {
      note.textContent = `Mode via ${modeEntity || "—"}. Writing Man/Auto/Rem SP Set flips mode.`;
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
