/**
 * SWD-227 regression: HMI ↔ HA number.set_value communication contract.
 *
 * Exercises the exported helpers in pid-loop-card.js (parse / coerce / click
 * routing). Run via pytest or:
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

const { parseSpValue, numberServiceValue, resolveFaceplateClick } = await import(
  cardUrl
);

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

function servicePayload(value) {
  const numeric = numberServiceValue(value);
  if (numeric === null) return null;
  return {
    domain: "number",
    service: "set_value",
    serviceData: { value: numeric },
  };
}

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

const good = servicePayload("0.3");
assert(good !== null, "Set SP builds a service call");
assertEq(good.domain, "number", "service domain is number");
assertEq(good.service, "set_value", "service is set_value");
assert(
  typeof good.serviceData.value === "number" && Number.isFinite(good.serviceData.value),
  "serviceData.value is a finite number (not string/NaN)"
);
assertEq(good.serviceData.value, 0.3, "serviceData.value is 0.3");
assertEq(servicePayload("man"), null, "label string must not become set_value");

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

if (failed > 0) {
  console.error(`\n${failed} assertion(s) failed`);
  process.exit(1);
}
console.log("\nAll pid faceplate contract assertions passed");
process.exit(0);
