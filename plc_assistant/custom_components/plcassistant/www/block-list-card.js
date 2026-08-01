/**
 * PLCAssistant generic attribute list card (SWD-183).
 *
 * Config: {
 *   type: "custom:plcassistant-block-list-card",
 *   entity: "sensor.plcassistant_pid_level",
 *   title?: string,
 *   include?: string[],   // attribute keys to show (default: all non-entity attrs)
 *   exclude?: string[]
 * }
 */
class PlcAssistantBlockListCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.plcassistant_status" };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("plcassistant-block-list-card requires `entity`");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 3;
  }

  _keys(attrs) {
    const include = Array.isArray(this._config.include) ? this._config.include : null;
    const exclude = new Set(this._config.exclude || []);
    let keys = Object.keys(attrs || {}).filter((k) => !k.endsWith("_entity"));
    if (include) {
      keys = include.filter((k) => k in (attrs || {}));
    }
    return keys.filter((k) => !exclude.has(k));
  }

  _fmt(value) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "object") {
      try {
        return JSON.stringify(value);
      } catch (_e) {
        return String(value);
      }
    }
    const n = Number(value);
    if (Number.isFinite(n) && String(value).trim() !== "") {
      return Math.abs(n) >= 100 ? n.toFixed(1) : n.toFixed(3).replace(/\.?0+$/, "");
    }
    return String(value);
  }

  _render() {
    if (!this._config) return;
    const st = this._hass?.states?.[this._config.entity];
    const title =
      this._config.title ||
      st?.attributes?.friendly_name ||
      this._config.entity;
    const attrs = st?.attributes || {};
    const keys = this._keys(attrs);
    if (!this._root) {
      this.innerHTML = "";
      this._root = document.createElement("ha-card");
      this.appendChild(this._root);
    }
    const rows = keys
      .map(
        (k) =>
          `<div class="row"><span class="k">${k}</span><span class="v">${this._fmt(
            attrs[k]
          )}</span></div>`
      )
      .join("");
    this._root.innerHTML = `
      <style>
        .wrap { padding: 14px 16px; }
        .title { font-size: 1.05rem; font-weight: 500; margin-bottom: 4px; }
        .state { font-size: 0.8rem; opacity: 0.7; margin-bottom: 10px; text-transform: capitalize; }
        .row { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); font-size: 0.9rem; }
        .row:last-child { border-bottom: none; }
        .k { opacity: 0.7; }
        .v { font-variant-numeric: tabular-nums; text-align: right; }
        .empty { opacity: 0.65; font-size: 0.85rem; }
      </style>
      <div class="wrap">
        <div class="title">${title}</div>
        <div class="state">${st ? st.state : "unavailable"}</div>
        ${rows || '<div class="empty">No attributes</div>'}
      </div>
    `;
  }
}

if (!customElements.get("plcassistant-block-list-card")) {
  customElements.define("plcassistant-block-list-card", PlcAssistantBlockListCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "plcassistant-block-list-card",
    name: "PLCAssistant Block List Card",
    description: "Generic attribute list for a sensor entity (library/custom blocks)",
  });
}
