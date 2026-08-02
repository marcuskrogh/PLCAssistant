/**
 * PLCAssistant PID faceplate card (SWD-183 / SWD-222 / SWD-226).
 *
 * Config: { type: "custom:plcassistant-pid-card", entity: "sensor.plcassistant_pid_level" }
 * Reads climate-like attributes from the compound PID sensor and writes
 * Manual/Auto/Remote mode + SP sources via number.* entities.
 *
 * Drafts: typed SP inputs use text + inputmode=decimal (not type=number) so
 * intermediate edits like "0." survive live hass updates without caret jumps
 * (SWD-226). Dirty drafts persist across refreshes until Set / Escape / clear.
 */
class PlcAssistantPidCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.plcassistant_pid_level" };
  }

  constructor() {
    super();
    this._drafts = {};
    this._dirty = {};
    this._bound = false;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("plcassistant-pid-card requires `entity`");
    }
    this._config = config;
    this._drafts = {};
    this._dirty = {};
    this._render(true);
  }

  set hass(hass) {
    this._hass = hass;
    this._render(false);
  }

  getCardSize() {
    return 5;
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

  _committedText(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "0";
    // Prefer short decimal text (avoid "0.300" stomping while idle display).
    const fixed = n.toFixed(6).replace(/\.?0+$/, "");
    return fixed === "-0" ? "0" : fixed;
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
      if (document.activeElement === input || this._dirty[key]) {
        this._drafts[key] = input.value;
        this._dirty[key] = true;
      }
    }
  }

  _clearDraft(key) {
    delete this._drafts[key];
    delete this._dirty[key];
  }

  _parseSp(raw) {
    const text = String(raw ?? "").trim().replace(",", ".");
    if (text === "" || text === "-" || text === "." || text === "-.") {
      return null;
    }
    const n = Number(text);
    return Number.isFinite(n) ? n : null;
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
    this._clearDraft(key);
    input.value = this._committedText(parsed);
    this._setNumber(entity, parsed);
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
      this._applySp(applyBtn.getAttribute("data-apply"));
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
      Number.isFinite(Number(sp)) && Number.isFinite(Number(pv))
        ? Number(sp) - Number(pv)
        : null;

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
        .pid-card {
          --pid-man: #c47800;
          --pid-auto: #0d9488;
          --pid-rem: #3b6ea5;
          --pid-accent: var(--pid-man);
          position: relative;
          overflow: hidden;
          padding: 0;
          font-family: var(--paper-font-body1_-_font-family, "Segoe UI", Roboto, sans-serif);
        }
        .pid-card[data-mode="man"] { --pid-accent: var(--pid-man); }
        .pid-card[data-mode="auto"] { --pid-accent: var(--pid-auto); }
        .pid-card[data-mode="rem"] { --pid-accent: var(--pid-rem); }
        .pid-accent {
          position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
          background: var(--pid-accent);
        }
        .pid-body { padding: 14px 16px 14px 18px; }
        .pid-head {
          display: flex; justify-content: space-between; align-items: center;
          gap: 10px; margin-bottom: 14px;
        }
        .pid-title {
          font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em;
          color: var(--primary-text-color);
        }
        .pid-badge {
          font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
          text-transform: uppercase; padding: 4px 10px; border-radius: 4px;
          color: #fff; background: var(--pid-accent);
        }
        .pid-hero {
          display: grid; grid-template-columns: 1.1fr 1.1fr 0.9fr;
          gap: 12px; margin-bottom: 14px;
          padding: 12px 12px 14px;
          border-radius: 8px;
          background:
            linear-gradient(135deg,
              color-mix(in srgb, var(--pid-accent) 12%, transparent),
              color-mix(in srgb, var(--secondary-background-color, #f5f5f5) 88%, transparent));
          border: 1px solid color-mix(in srgb, var(--pid-accent) 28%, var(--divider-color, #ddd));
        }
        .pid-metric { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
        .pid-metric span {
          font-size: 0.65rem; opacity: 0.7; text-transform: uppercase;
          letter-spacing: 0.06em; font-weight: 600;
        }
        .pid-metric strong {
          font-size: 1.55rem; font-variant-numeric: tabular-nums; font-weight: 600;
          letter-spacing: -0.02em; line-height: 1.15;
          color: var(--primary-text-color);
        }
        .pid-metric[data-role="sp"] strong { color: var(--pid-accent); }
        .pid-metric .pid-sub {
          font-size: 0.68rem; opacity: 0.65; font-variant-numeric: tabular-nums;
        }
        .pid-cv-track {
          margin-top: 6px; height: 4px; border-radius: 2px;
          background: color-mix(in srgb, var(--divider-color, #ccc) 55%, transparent);
          overflow: hidden;
        }
        .pid-cv-fill {
          height: 100%; width: 0%; border-radius: 2px;
          background: var(--pid-accent); transition: width 0.25s ease;
        }
        .pid-modes {
          display: grid; grid-template-columns: repeat(3, 1fr);
          gap: 0; margin-bottom: 12px;
          border: 1px solid var(--divider-color, #c8c8c8);
          border-radius: 8px; overflow: hidden;
        }
        .pid-modes button {
          border: 0; border-right: 1px solid var(--divider-color, #c8c8c8);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          padding: 10px 6px; cursor: pointer; font-size: 0.82rem; font-weight: 500;
        }
        .pid-modes button:last-child { border-right: 0; }
        .pid-modes button[data-mode="0"].active { background: var(--pid-man); color: #fff; }
        .pid-modes button[data-mode="1"].active { background: var(--pid-auto); color: #fff; }
        .pid-modes button[data-mode="2"].active { background: var(--pid-rem); color: #fff; }
        .pid-editors { display: grid; gap: 8px; }
        .pid-row {
          display: grid; grid-template-columns: 64px 1fr auto; gap: 8px;
          align-items: center; padding: 8px 10px; border-radius: 8px;
          border: 1px solid transparent;
          background: var(--secondary-background-color, #f7f7f7);
        }
        .pid-row.active-source {
          border-color: color-mix(in srgb, var(--pid-accent) 55%, transparent);
          background: color-mix(in srgb, var(--pid-accent) 10%, var(--card-background-color, #fff));
          box-shadow: inset 3px 0 0 var(--pid-accent);
        }
        .pid-row label {
          font-size: 0.72rem; font-weight: 600; opacity: 0.8;
          text-transform: uppercase; letter-spacing: 0.04em;
        }
        .pid-row input {
          border: 1px solid var(--divider-color, #c8c8c8);
          border-radius: 6px; padding: 7px 9px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          font-size: 0.95rem; font-variant-numeric: tabular-nums;
          min-width: 0;
        }
        .pid-row input:focus {
          outline: 2px solid color-mix(in srgb, var(--pid-accent) 45%, transparent);
          outline-offset: 1px; border-color: var(--pid-accent);
        }
        .pid-row input:disabled { opacity: 0.55; }
        .pid-row button {
          border: 1px solid color-mix(in srgb, var(--pid-accent) 40%, var(--divider-color, #ccc));
          background: color-mix(in srgb, var(--pid-accent) 12%, transparent);
          color: var(--primary-text-color);
          border-radius: 6px; padding: 7px 12px; cursor: pointer;
          font-size: 0.78rem; font-weight: 600;
        }
        .pid-row button:disabled { opacity: 0.45; cursor: default; }
        .pid-note { margin-top: 10px; font-size: 0.7rem; opacity: 0.6; line-height: 1.35; }
        .pid-missing { padding: 16px; opacity: 0.7; }
        @media (max-width: 420px) {
          .pid-hero { grid-template-columns: 1fr 1fr; }
          .pid-metric[data-role="cv"] { grid-column: 1 / -1; }
          .pid-metric strong { font-size: 1.35rem; }
        }
      </style>
      ${
        unavailable
          ? `<div class="pid-missing">Entity ${this._config.entity} unavailable</div>`
          : `<div class="pid-card" data-mode="man">
        <div class="pid-accent" aria-hidden="true"></div>
        <div class="pid-body">
          <div class="pid-head">
            <div class="pid-title"></div>
            <div class="pid-badge" data-badge></div>
          </div>
          <div class="pid-hero">
            <div class="pid-metric" data-role="pv">
              <span>Process</span>
              <strong data-metric="pv"></strong>
              <div class="pid-sub">PV</div>
            </div>
            <div class="pid-metric" data-role="sp">
              <span>Active SP</span>
              <strong data-metric="sp"></strong>
              <div class="pid-sub" data-metric="err"></div>
            </div>
            <div class="pid-metric" data-role="cv">
              <span>Control</span>
              <strong data-metric="cv"></strong>
              <div class="pid-cv-track"><div class="pid-cv-fill" data-cv-bar></div></div>
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

    const card = this._root.querySelector(".pid-card");
    if (card) card.setAttribute("data-mode", modeKey);

    const titleEl = this._root.querySelector(".pid-title");
    const badgeEl = this._root.querySelector("[data-badge]");
    if (titleEl) titleEl.textContent = title;
    if (badgeEl) badgeEl.textContent = mode;

    const pvEl = this._root.querySelector('[data-metric="pv"]');
    const spEl = this._root.querySelector('[data-metric="sp"]');
    const cvEl = this._root.querySelector('[data-metric="cv"]');
    const errEl = this._root.querySelector('[data-metric="err"]');
    const barEl = this._root.querySelector("[data-cv-bar]");
    if (pvEl) pvEl.textContent = this._fmt(pv);
    if (spEl) spEl.textContent = this._fmt(sp);
    if (cvEl) cvEl.textContent = this._fmt(cv, 2);
    if (errEl) {
      errEl.textContent =
        err === null ? "error —" : `error ${err >= 0 ? "+" : ""}${this._fmt(err)}`;
    }
    if (barEl) barEl.style.width = `${this._cvBarPct(cv, loopId)}%`;

    this._root.querySelectorAll("[data-mode]").forEach((btn) => {
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
        `Mode via ${modeEntity || "—"}. Set writes the SP and flips to that source. Enter commits · Esc cancels.`;
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
