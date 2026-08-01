/**
 * PLCAssistant PID faceplate card (SWD-183).
 *
 * Config: { type: "custom:plcassistant-pid-card", entity: "sensor.plcassistant_pid_level" }
 * Reads climate-like attributes from the compound PID sensor and writes
 * Manual/Auto/Remote mode + SP sources via number.* entities.
 */
class PlcAssistantPidCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.plcassistant_pid_level" };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("plcassistant-pid-card requires `entity`");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
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

  _render() {
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
    const spManEntity = this._attr(st, "sp_man_entity", "");
    const spAutoEntity = this._attr(st, "sp_auto_entity", "");
    const spRemEntity = this._attr(st, "sp_rem_entity", "");

    if (!this._root) {
      this.innerHTML = "";
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
    }
    const unavailable = !st;
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
          <div class="pid-title">${title}</div>
          <div class="pid-mode">${mode}</div>
        </div>
        <div class="pid-grid">
          <div class="pid-metric"><span>PV</span><strong>${this._fmt(pv)}</strong></div>
          <div class="pid-metric"><span>SP</span><strong>${this._fmt(sp)}</strong></div>
          <div class="pid-metric"><span>CV</span><strong>${this._fmt(cv, 2)}</strong></div>
        </div>
        <div class="pid-modes">
          <button data-mode="0" class="${mode === "manual" ? "active" : ""}">Man</button>
          <button data-mode="1" class="${mode === "automatic" ? "active" : ""}">Auto</button>
          <button data-mode="2" class="${mode === "remote" ? "active" : ""}">Rem</button>
        </div>
        <div class="pid-editors">
          <div class="pid-row">
            <label>SP Man</label>
            <input data-sp="man" type="number" step="any" value="${Number(spMan)}" />
            <button data-apply="man">Set</button>
          </div>
          <div class="pid-row">
            <label>SP Auto</label>
            <input data-sp="auto" type="number" step="any" value="${Number(spAuto)}" ${
              String(spAutoEntity).startsWith("sensor.") ? "disabled" : ""
            } />
            <button data-apply="auto" ${
              String(spAutoEntity).startsWith("sensor.") ? "disabled" : ""
            }>Set</button>
          </div>
          <div class="pid-row">
            <label>SP Rem</label>
            <input data-sp="rem" type="number" step="any" value="${Number(spRem)}" />
            <button data-apply="rem">Set</button>
          </div>
        </div>
        <div class="pid-note">Mode via ${modeEntity || "—"}. Writing Man/Rem SP auto-flips mode.</div>
      </div>`
      }
    `;

    if (unavailable) return;

    this._root.querySelectorAll("[data-mode]").forEach((btn) => {
      btn.addEventListener("click", () => this._setMode(btn.getAttribute("data-mode")));
    });
    const entityFor = {
      man: spManEntity,
      auto: spAutoEntity,
      rem: spRemEntity,
    };
    this._root.querySelectorAll("[data-apply]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-apply");
        const input = this._root.querySelector(`input[data-sp="${key}"]`);
        const entity = entityFor[key];
        if (!input || !entity || String(entity).startsWith("sensor.")) return;
        this._setNumber(entity, input.value);
      });
    });
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
