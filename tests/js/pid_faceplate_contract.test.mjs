/**
 * SWD-227 / SWD-228 / SWD-230 regression: HMI ↔ HA number.set_value communication
 * contract plus compact faceplate helpers (2dp format, open/close dialog routing,
 * null-safe err gating, commit rounding).
 *
 * Exercises the exported helpers in pid-loop-card.js (parse / coerce / click
 * routing / display format / ISA-101 highlight severity). Run via pytest or:
 *   node --experimental-default-type=module tests/js/pid_faceplate_contract.test.mjs
 */

globalThis.HTMLElement = class HTMLElement {};
globalThis.customElements = {
  get() {
    return undefined;
  },
  define() {},
};
globalThis.window = globalThis;

const cardUrl = new URL(
  "../../custom_components/plcassistant/www/pid-loop-card.js",
  import.meta.url
).href;

const {
  parseSpValue,
  numberServiceValue,
  resolveFaceplateClick,
  formatPidValue,
  formatPidError,
  commitSpValue,
  isPresentFinite,
  pidError,
  pidHighlightSeverity,
  pidCvBarPct,
  pidCvHighlightSeverity,
  pidFaceplateHighlight,
  pidOperatorWriteTarget,
  pidBarValueFromPointer,
  pidBarPct,
  pidPvScaleMax,
  pidNudgeValue,
  pidNudgeRange,
  pidBarFaceLabel,
  pidBarEditorKey,
  pidNormalizeBarKey,
  PID_DISPLAY_DIGITS,
  PID_CV_MAX_LEVEL,
  PID_CV_MAX_FLOW,
  PID_NUDGE_FINE,
  PID_NUDGE_COARSE,
} = await import(cardUrl);

let failed = 0;

function assert(cond, msg) {
  if (!cond) {
    failed += 1;
    console.error("FAIL:", msg);
  } else {
    console.log("ok:", msg);
  }
}

function assertEq(actual, expected, msg) {
  const same =
    actual === expected ||
    (Number.isNaN(actual) && Number.isNaN(expected)) ||
    (typeof actual === "number" &&
      typeof expected === "number" &&
      Number.isFinite(actual) &&
      Number.isFinite(expected) &&
      Math.abs(actual - expected) < 1e-12);
  assert(same, `${msg} (got ${JSON.stringify(actual)}, want ${JSON.stringify(expected)})`);
}

/** Minimal DOM node with parent walk for ``closest``. */
function node(tag, attrs = {}, parent = null) {
  const el = {
    tagName: String(tag).toUpperCase(),
    disabled: Boolean(attrs.disabled),
    _attrs: { ...attrs },
    parent,
    getAttribute(name) {
      const v = this._attrs[name];
      return v === undefined ? null : String(v);
    },
    closest(selector) {
      let cur = this;
      while (cur) {
        if (matches(cur, selector)) return cur;
        cur = cur.parent;
      }
      return null;
    },
  };
  return el;
}

function matches(el, selector) {
  const s = String(selector).trim();
  if (s.startsWith("button[")) {
    if (el.tagName !== "BUTTON") return false;
    const m = /^button\[([a-zA-Z0-9_-]+)\]$/.exec(s);
    return Boolean(m && el.getAttribute(m[1]) !== null);
  }
  if (s.startsWith(".") ) {
    const cls = s.slice(1);
    const classAttr = el.getAttribute("class") || "";
    return classAttr.split(/\s+/).includes(cls);
  }
  if (s.startsWith("[") && s.endsWith("]")) {
    const attr = s.slice(1, -1);
    return el.getAttribute(attr) !== null;
  }
  return false;
}

/** Build the exact SWD-227 failure DOM shape (card root had data-mode). */
function swd227SetClickTarget() {
  const card = node("div", { "data-mode": "man", class: "pid-card" });
  const editors = node("div", { class: "pid-editors" }, card);
  const row = node("div", { "data-source": "man" }, editors);
  const apply = node("button", { "data-apply": "man" }, row);
  // Click lands on the Set button text/children → target is the button.
  return apply;
}

function servicePayload(entityId, value) {
  const numeric = numberServiceValue(value);
  if (numeric === null) return null;
  return {
    domain: "number",
    service: "set_value",
    serviceData: { entity_id: entityId, value: numeric },
  };
}

// --- formatPidValue / 2dp display (SWD-228 / SWD-230) ---
assertEq(PID_DISPLAY_DIGITS, 2, "PID_DISPLAY_DIGITS is 2");
assertEq(formatPidValue(0.2), "0.20", "formatPidValue(0.2) → 0.20");
assertEq(formatPidValue(1.23456), "1.23", "formatPidValue truncates to 2dp");
assertEq(formatPidValue(0.20000000000000004), "0.20", "formatPidValue kills float noise");
assertEq(formatPidValue("1,259"), "1.26", "formatPidValue accepts comma decimal string");
assertEq(formatPidValue(null), "—", "formatPidValue(null) → em-dash");
assertEq(formatPidValue("bad"), "—", "formatPidValue(non-finite) → em-dash");
assertEq(formatPidValue(""), "—", "formatPidValue('') → em-dash");
assert(
  !String(formatPidValue(Math.PI)).includes("3.14159"),
  "formatPidValue never leaks long decimals"
);

// --- isPresentFinite / commitSpValue (SWD-230 review-fix) ---
assertEq(isPresentFinite(null), false, "null is not a present finite");
assertEq(isPresentFinite(undefined), false, "undefined is not a present finite");
assertEq(isPresentFinite(""), false, "empty string is not a present finite");
assertEq(isPresentFinite(0), true, "0 is present finite");
assertEq(isPresentFinite(0.2), true, "0.2 is present finite");
assertEq(commitSpValue(1.236), 1.24, "commitSpValue rounds 1.236 → 1.24");
assertEq(commitSpValue("1.236"), 1.24, "commitSpValue coerces string then rounds");
assertEq(commitSpValue("man"), null, "commitSpValue rejects non-numeric");

// --- parseSpValue ---
assertEq(parseSpValue("0.3"), 0.3, "parseSpValue accepts 0.3");
assertEq(parseSpValue("."), null, "parseSpValue rejects bare '.'");
assertEq(parseSpValue("-"), null, "parseSpValue rejects bare '-'");
assertEq(parseSpValue(""), null, "parseSpValue rejects empty");
assertEq(parseSpValue("1,25"), 1.25, "parseSpValue accepts comma decimal");
// Trailing-dot drafts like "0." are kept in the text input (SWD-226); on Set,
// Number("0.") === 0 which is a valid finite commit.
assertEq(parseSpValue("0."), 0, "parseSpValue('0.') commits as 0");

// --- numberServiceValue (HA number.set_value float contract) ---
assertEq(numberServiceValue("0.3"), 0.3, "numberServiceValue('0.3') is float 0.3");
assertEq(numberServiceValue(0.3), 0.3, "numberServiceValue(0.3) is float 0.3");
assertEq(numberServiceValue("0"), 0, "numberServiceValue('0') is 0");
assertEq(numberServiceValue("man"), null, "numberServiceValue('man') blocked (SWD-227)");
assertEq(numberServiceValue("auto"), null, "numberServiceValue('auto') blocked");
assertEq(numberServiceValue("NaN"), null, "numberServiceValue('NaN') blocked");
assertEq(numberServiceValue(""), null, "numberServiceValue('') blocked");
assertEq(numberServiceValue("0"), 0, "mode code 0 is finite");
assertEq(numberServiceValue("1"), 1, "mode code 1 is finite");
assertEq(numberServiceValue("2"), 2, "mode code 2 is finite");

const spEntity = "number.plcassistant_sp_level_man";
const good = servicePayload(spEntity, "0.3");
assert(good !== null, "Set SP builds a service call");
assertEq(good.domain, "number", "service domain is number");
assertEq(good.service, "set_value", "service is set_value");
assertEq(good.serviceData.entity_id, spEntity, "serviceData.entity_id targets SP number");
assert(
  typeof good.serviceData.value === "number" && Number.isFinite(good.serviceData.value),
  "serviceData.value is a finite number (not string/NaN)"
);
assertEq(good.serviceData.value, 0.3, "serviceData.value is 0.3");
assertEq(servicePayload(spEntity, "man"), null, "label string must not become set_value");
assertEq(
  servicePayload(spEntity, commitSpValue(1.236)).serviceData.value,
  1.24,
  "Set SP service payload uses committed 2dp value"
);

const modeEntity = "number.plcassistant_level_mode";
const modeCall = servicePayload(modeEntity, "0");
assert(modeCall !== null, "mode switch builds a service call");
assertEq(modeCall.serviceData.entity_id, modeEntity, "mode targets mode_entity");
assertEq(modeCall.serviceData.value, 0, "mode code 0 is finite float");

// Disabled Set (e.g. flow Auto sensor.*) must not apply.
const disabledApply = node("button", { "data-apply": "auto", disabled: true });
assertEq(resolveFaceplateClick(disabledApply), null, "disabled Set resolves to null");

// --- resolveFaceplateClick (Set must not be hijacked by ancestor data-mode) ---
const setBtn = swd227SetClickTarget();
const action = resolveFaceplateClick(setBtn);
assert(action !== null, "Set click resolves to an action");
assertEq(action.type, "apply", "SWD-227: Set under data-mode ancestor → apply, not mode");
assertEq(action.key, "man", "apply key is man");

// Mode button still works when the click is on button[data-mode]
const modeRoot = node("div", { "data-pid-mode": "man" });
const modeBtn = node("button", { "data-mode": "0" }, modeRoot);
const modeAction = resolveFaceplateClick(modeBtn);
assertEq(modeAction?.type, "mode", "mode button resolves to mode");
assertEq(modeAction?.code, "0", "mode code is 0");

// Accent attribute on card must not be treated as a mode control
const accentCard = node("div", { "data-pid-mode": "man" });
const setUnderAccent = node("button", { "data-apply": "rem" }, accentCard);
assertEq(
  resolveFaceplateClick(setUnderAccent)?.type,
  "apply",
  "Set under data-pid-mode ancestor still applies SP"
);

// Bare [data-mode] on a non-button must not steal Set (regression guard)
assert(
  setBtn.closest("[data-mode]") !== null,
  "fixture still has ancestor [data-mode] (documents the old bug shape)"
);
assert(
  setBtn.closest("button[data-mode]") === null,
  "Set button is not a mode button"
);

// --- Dialog open / close routing (SWD-228) ---
const face = node("button", { "data-open-editor": "", class: "pid-face" });
assertEq(resolveFaceplateClick(face)?.type, "open", "face click opens editor");
const closeBtn = node("button", { "data-close-editor": "", class: "pid-dialog-close" });
assertEq(resolveFaceplateClick(closeBtn)?.type, "close", "close button closes editor");
const backdrop = node("button", { "data-close-editor": "", class: "pid-dialog-backdrop" });
assertEq(resolveFaceplateClick(backdrop)?.type, "close", "backdrop closes editor");
const panel = node("div", { class: "pid-dialog-panel" });
const panelInput = node("input", { "data-sp": "man" }, panel);
assertEq(resolveFaceplateClick(panelInput), null, "dialog input does not re-open");
assertEq(resolveFaceplateClick(panel), null, "dialog panel click is ignored");

// --- ISA-101 highlight helpers ---
assertEq(pidError(0.3, 0.15), 0.15, "pidError is SP − PV");
assertEq(pidError(null, 0.15), null, "pidError null when SP missing");
assertEq(formatPidError(0.15), "+0.15", "formatPidError prefixes positive");
assertEq(formatPidError(-0.02), "-0.02", "formatPidError keeps minus");
assertEq(formatPidError(0), "0.00", "formatPidError zero is unsigned");
assertEq(formatPidError(null), "—", "formatPidError missing is em-dash");

assertEq(pidHighlightSeverity(null, 1, 1), "normal", "missing ε is normal");
assertEq(pidHighlightSeverity(0, 1, 1), "normal", "zero ε is normal");
assertEq(pidHighlightSeverity(0.015, 1, 0.985), "normal", "1.5% ε is normal");
assertEq(pidHighlightSeverity(0.02, 1, 0.98), "caution", "2% ε is caution");
assertEq(pidHighlightSeverity(0.099, 1, 0.901), "caution", "9.9% ε is caution");
assertEq(pidHighlightSeverity(0.1, 1, 0.9), "abnormal", "10% ε is abnormal");
assertEq(pidHighlightSeverity(0.15, 0.3, 0.15), "abnormal", "startup ε is abnormal");
assertEq(pidHighlightSeverity(0, 0, 0), "normal", "zero/zero ε is normal");

assertEq(PID_CV_MAX_LEVEL, 8, "level CO scale is 8 L/min");
assertEq(PID_CV_MAX_FLOW, 100, "flow CO scale is 100%");
assertEq(pidCvBarPct(4, "level"), 50, "level CO 4 L/min is 50% of 8");
assertEq(pidCvBarPct(6, "level"), 75, "level CO 6 L/min is 75% of 8 (not 100% of 6)");
assertEq(pidCvBarPct(8, "level"), 100, "level CO 8 L/min is 100%");
assertEq(pidCvBarPct(50, "flow"), 50, "flow CO 50% is 50% of 100");
assertEq(pidCvHighlightSeverity(4, "level"), "normal", "mid-scale CO is normal");
assertEq(pidCvHighlightSeverity(0, "level"), "caution", "CO at 0 is clamp caution");
assertEq(pidCvHighlightSeverity(8, "level"), "caution", "CO at max is clamp caution");
assertEq(pidCvHighlightSeverity(null, "level"), "normal", "missing CO is not clamp");
assertEq(
  pidFaceplateHighlight(0.015, 1, 0.985, 4, "level"),
  "normal",
  "small ε and mid CO is normal"
);
assertEq(
  pidFaceplateHighlight(0.02, 1, 0.98, 4, "level"),
  "caution",
  "caution ε wins over mid CO"
);
assertEq(
  pidFaceplateHighlight(0, 1, 1, 0, "level"),
  "caution",
  "clamp CO is caution when ε is 0"
);
assertEq(
  pidFaceplateHighlight(0.2, 1, 0.8, 0, "level"),
  "abnormal",
  "abnormal ε outranks clamp CO"
);

// --- DCS analog-controller write target + bar mapping (SWD-369) ---
assertEq(pidPvScaleMax("level"), 0.4, "level PV/SP scale is 0.40 m");
assertEq(pidPvScaleMax("flow"), 8, "flow PV/SP scale is 8 L/min");
assertEq(pidBarPct(0.2, 0.4), 50, "level PV 0.20 m is 50% of 0.40");
assertEq(pidBarPct(4, 8), 50, "flow PV 4 L/min is 50% of 8");
assertEq(pidOperatorWriteTarget("manual"), "co", "MAN writes CO");
assertEq(pidOperatorWriteTarget("automatic"), "sp", "AUTO writes SP when Number");
assertEq(
  pidOperatorWriteTarget("automatic", { spWritable: false }),
  null,
  "AUTO does not write SP when Auto entity is a sensor"
);
assertEq(pidOperatorWriteTarget("remote"), null, "REM is not operator-writable");
assertEq(pidOperatorWriteTarget("cas"), null, "cascade alias is REM (not writable)");

const track = { left: 10, top: 20, width: 100, height: 80 };
assertEq(
  pidBarValueFromPointer(track, 10, 20, 0, 1, "vertical"),
  1,
  "vertical bar top is max"
);
assertEq(
  pidBarValueFromPointer(track, 10, 100, 0, 1, "vertical"),
  0,
  "vertical bar bottom is min"
);
assertEq(
  pidBarValueFromPointer(track, 10, 20, 0, 8, "horizontal"),
  0,
  "horizontal bar left is min"
);
assertEq(
  pidBarValueFromPointer(track, 110, 20, 0, 8, "horizontal"),
  8,
  "horizontal bar right is max"
);

const writableCo = node("button", { "data-bar": "co", "data-writable": "1" });
assertEq(resolveFaceplateClick(writableCo)?.type, "bar", "writable CO bar click is bar");
assertEq(resolveFaceplateClick(writableCo)?.key, "co", "writable CO bar key is co");
const lockedSp = node("button", { "data-bar": "sp", "data-writable": "0" });
assertEq(resolveFaceplateClick(lockedSp)?.type, "bar", "non-writable SP bar still opens inspect popup");
assertEq(resolveFaceplateClick(lockedSp)?.key, "sp", "locked SP bar key is sp");
const pvBar = node("button", { "data-bar": "pv", "data-writable": "0" });
assertEq(resolveFaceplateClick(pvBar)?.type, "bar", "PV bar click opens inspect popup");
assertEq(resolveFaceplateClick(pvBar)?.key, "pv", "PV bar key is pv");
const openRoot = node("div", { "data-open-editor": "" });
const barUnderOpen = node("button", { "data-bar": "sp", "data-writable": "1" }, openRoot);
assertEq(
  resolveFaceplateClick(barUnderOpen)?.type,
  "bar",
  "writable bar wins over data-open-editor ancestor"
);

assertEq(pidBarFaceLabel("co"), "MV", "CO analog is labelled MV");
assertEq(pidBarFaceLabel("sp"), "SP", "SP analog is labelled SP");
assertEq(pidBarFaceLabel("pv"), "PV", "PV analog is labelled PV");
assertEq(pidNormalizeBarKey("cv"), "co", "cv normalises to co");
assertEq(pidBarEditorKey("co"), "co", "MV bar uses co editor");
assertEq(pidBarEditorKey("sp"), "auto", "SP bar uses auto editor");
assertEq(pidBarEditorKey("pv"), null, "PV bar has no editor");
assertEq(PID_NUDGE_FINE, 0.1, "fine nudge is 0.1");
assertEq(PID_NUDGE_COARSE, 1, "coarse nudge is 1.0");
assertEq(pidNudgeRange("sp", "level").max, 0.4, "level SP nudge max is 0.40 m");
assertEq(pidNudgeRange("co", "level").max, 8, "level CO nudge max is 8 L/min");
assertEq(pidNudgeValue(3.2, 0.1, 0, 8), 3.3, "fine nudge +0.1");
assertEq(pidNudgeValue(3.2, -1, 0, 8), 2.2, "coarse nudge -1.0");
assertEq(pidNudgeValue(0.05, -0.1, 0, 0.4), 0, "nudge clamps to min");
assertEq(pidNudgeValue(7.6, 1, 0, 8), 8, "nudge clamps to max");
assertEq(pidNudgeValue(null, 0.1, 0, 8), null, "nudge rejects missing value");

const fineUp = node("button", { "data-nudge": "0.1" });
assertEq(resolveFaceplateClick(fineUp)?.type, "nudge", "nudge click type");
assertEq(resolveFaceplateClick(fineUp)?.delta, 0.1, "nudge click delta 0.1");
const coarseDown = node("button", { "data-nudge": "-1" });
assertEq(resolveFaceplateClick(coarseDown)?.delta, -1, "nudge click delta -1");
const disabledNudge = node("button", { "data-nudge": "0.1", disabled: true });
assertEq(resolveFaceplateClick(disabledNudge), null, "disabled nudge is ignored");

const gear = node("button", { "data-settings": "open" });
assertEq(resolveFaceplateClick(gear)?.type, "settings", "gear opens settings");
assertEq(resolveFaceplateClick(gear)?.action, "open", "gear action is open");
const settingsApply = node("button", { "data-settings-apply": "" });
assertEq(resolveFaceplateClick(settingsApply)?.action, "apply", "settings apply");
const settingsCancel = node("button", { "data-settings-cancel": "" });
assertEq(resolveFaceplateClick(settingsCancel)?.action, "cancel", "settings cancel");

if (failed > 0) {
  console.error(`\n${failed} assertion(s) failed`);
  process.exit(1);
}
console.log("\nAll pid faceplate contract assertions passed");
process.exit(0);
