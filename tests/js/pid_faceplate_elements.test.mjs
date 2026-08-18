/**
 * Isolated PID faceplate elements: catalog + applyPidFaceplateState.
 *
 * Run via pytest or:
 *   node --experimental-default-type=module tests/js/pid_faceplate_elements.test.mjs
 */

globalThis.HTMLElement = class HTMLElement {};
globalThis.customElements = {
  get() {
    return undefined;
  },
  define() {},
};
globalThis.window = globalThis;

const elementsUrl = new URL(
  "../../custom_components/plcassistant/www/pid-faceplate-elements.js",
  import.meta.url
).href;

const {
  PID_FACEPLATE_ELEMENT_IDS,
  PID_FACEPLATE_ELEMENT_CATALOG,
  pidFaceplateElementHtml,
  pidFaceplateMarkup,
  pidFaceplateStyles,
  applyPidFaceplateState,
  mountPidFaceplateElement,
} = await import(elementsUrl);

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
  assert(actual === expected, `${msg} (got ${JSON.stringify(actual)}, want ${JSON.stringify(expected)})`);
}

assertEq(PID_FACEPLATE_ELEMENT_IDS.join(","), "isa-glyph,kpi-row,analog-bars,mode-row", "named element ids");
assertEq(PID_FACEPLATE_ELEMENT_CATALOG.length, 4, "catalog length");

const glyph = pidFaceplateElementHtml("isa-glyph");
assert(glyph.includes("pid-isa-eps"), "glyph has ε");
assert(glyph.includes("pid-isa-p"), "glyph has P");
assert(glyph.includes("pid-isa-i"), "glyph has I");
assert(glyph.includes("pid-isa-d"), "glyph has D");

const kpis = pidFaceplateElementHtml("kpi-row");
assert(kpis.includes('data-metric="pv"'), "kpi PV");
assert(kpis.includes('data-metric="sp"'), "kpi SP");
assert(kpis.includes('data-metric="err"'), "kpi ε");
assert(kpis.includes('data-metric="cv"'), "kpi MV");
assert(kpis.includes("<span>MV</span>"), "kpi labels MV");
assert(!kpis.includes("<span>CV</span>"), "kpi does not label CV");
assert(!kpis.includes("<span>CO</span>"), "kpi does not label CO");

const bars = pidFaceplateElementHtml("analog-bars");
assert(bars.includes('data-bar="pv"'), "PV bar");
assert(bars.includes('data-bar="sp"'), "SP bar");
assert(bars.includes('data-bar="co"'), "CO bar");
assert(bars.includes("pid-vbar-track"), "vertical track");
assert(bars.includes("pid-hbar"), "horizontal CO");
assert(bars.includes('data-metric="pv"'), "PV value on bar");
assert(bars.includes('data-metric="sp"'), "SP value on bar");
assert(bars.includes('aria-label="MV"'), "MV bar label");
assert(bars.includes("pid-err-between"), "ε sits between PV and SP");

const modes = pidFaceplateElementHtml("mode-row");
assert(modes.includes('data-mode="0"'), "Man");
assert(modes.includes('data-mode="1"'), "Auto");
assert(modes.includes('data-mode="2"'), "Rem");

assertEq(pidFaceplateElementHtml("nope"), "", "unknown element is empty");

const css = pidFaceplateStyles();
assert(css.includes("--warning-color"), "ISA-101 caution token");
assert(css.includes("--error-color"), "ISA-101 abnormal token");
assert(!css.includes("--pid-man"), "no MAN hue token");
assert(css.includes("overflow: hidden"), "card clips; shell does not own overflow in CSS block");
assert(css.includes(".pid-card"), "card selector");
assert(css.includes("min-height: 120px"), "taller vertical tracks");
assert(css.includes("width: 14px"), "thinner vertical tracks");
assert(css.includes("height: 16px"), "thicker CO track");
assert(css.includes(".pid-vbar-fill[data-writable=\"1\"]"), "writable fill colour hook");
assert(css.includes("--pid-active"), "writable fill uses activity green");
assert(css.includes("background: var(--pid-active"), "writable fill token is --pid-active");
assert(
  !css.includes('.pid-shell[data-pid-hi="abnormal"] .pid-vbar-fill[data-writable="1"]'),
  "ε severity does not recolour the writable fill"
);
assert(
  !css.includes("box-shadow: inset 0 0 0 1px var(--primary-text-color)"),
  "writable analog is not a bounding box"
);

const assembled = pidFaceplateMarkup({ includeDialog: true, includeHint: true });
assert(assembled.includes("Tap to adjust"), "assembled hint");
assert(assembled.includes("data-nudge"), "nudge row on assembled face");
assert(assembled.includes('data-settings="open"'), "settings gear");
assert(assembled.includes("pid-err-between"), "ε between PV and SP");
assert(!assembled.includes("pid-head-err"), "ε is not in the header");
assert(assembled.includes("data-value-min"), "focused popup has min");
assert(assembled.includes("data-value-max"), "focused popup has max");
assert(assembled.includes("data-value-current"), "focused popup has current value");
assert(assembled.includes(">MV<"), "assembled labels MV");
assert(!assembled.includes("Active SP"), "focused popup is not the old editor stack");
assert(!css.includes("pointer-events: none"), "non-writable bars stay clickable");
assert(css.includes("border-left: 1px solid var(--divider-color"), "ε gutter between PV and SP");
assert(assembled.includes("pid-settings-dialog"), "settings dialog");
assert(assembled.includes("pid-value-dialog"), "value dialog");
assert(!assembled.includes("pid-hero"), "assembled face does not keep the KPI hero row");
const cardOpen = assembled.indexOf('<div class="pid-card">');
const dialogOpen = assembled.indexOf('class="pid-dialog');
assert(cardOpen !== -1 && dialogOpen > cardOpen, "dialog after card");
const between = assembled.slice(cardOpen, dialogOpen);
assert(between.includes("</div>"), "pid-card closes before dialog");

function makeNode() {
  const store = new Map();
  const mk = (key) => {
    if (!store.has(key)) {
      store.set(key, {
        style: {},
        textContent: "",
        _attrs: {},
        classList: {
          toggle(name, on) {
            this._on = on;
            this._name = name;
          },
        },
        getAttribute(name) {
          return this._attrs[name] ?? null;
        },
        setAttribute(name, value) {
          this._attrs[name] = String(value);
        },
      });
    }
    return store.get(key);
  };
  return {
    store,
    mk,
    classList: { contains: () => false },
    querySelector(sel) {
      if (sel === ".pid-shell") return mk("shell");
      return mk(sel);
    },
    querySelectorAll(sel) {
      if (sel === "[data-bar]") {
        return ["pv", "sp", "co"].map((k) => {
          const n = mk(`[data-bar="${k}"]`);
          n._attrs["data-bar"] = k;
          return n;
        });
      }
      if (sel === "[data-nudge]") {
        return ["-1", "-0.1", "0.1", "1"].map((delta) => {
          const n = mk(`button[data-nudge="${delta}"]`);
          n._attrs["data-nudge"] = delta;
          n.disabled = false;
          return n;
        });
      }
      if (sel === "button[data-mode]") {
        return ["0", "1", "2"].map((code) => {
          const n = mk(`button[data-mode="${code}"]`);
          n._attrs["data-mode"] = code;
          return n;
        });
      }
      if (sel === '.pid-metric[data-role="err"]') return [mk("err-metric")];
      if (sel === "[data-source]") return [];
      return [mk(sel)];
    },
  };
}

const root = makeNode();
applyPidFaceplateState(root, {
  title: "Level PID",
  mode: "manual",
  loopId: "level",
  pv: 0.2,
  sp: 0.3,
  cv: 3.2,
  coWritable: true,
  spWritable: false,
});
assertEq(root.mk("shell")._attrs["data-pid-mode"], "man", "shell mode man");
assertEq(root.mk('[data-metric="pv"]').textContent, "0.20", "PV 2dp");
assertEq(root.mk('[data-metric="sp"]').textContent, "0.30", "SP 2dp");
assertEq(root.mk("[data-pv-bar]").style.height, "50%", "PV bar 0.2/0.4");
assertEq(root.mk('[data-bar="co"]')._attrs["data-writable"], "1", "MAN highlights CO");
assertEq(root.mk('[data-bar="sp"]')._attrs["data-writable"], "0", "MAN does not write SP");
assertEq(root.mk("[data-cv-bar]")._attrs["data-writable"], "1", "MAN colours CO fill");
assertEq(root.mk("[data-value-title]").textContent, "MV", "MAN default popup is MV");
assertEq(root.mk("[data-value-min]").textContent, "0.00", "MV min is 0");
assertEq(root.mk("[data-value-max]").textContent, "8.00", "level MV max is 8");
assertEq(root.mk("[data-value-unit]").textContent, "L/min", "level MV unit");
assertEq(root.mk("[data-value-current]").textContent, "3.20", "MV current follows cv");
assert(root.mk("button[data-nudge=\"-1\"]").disabled === false, "nudge enabled in MAN");
assert(root.mk('button[data-mode="0"]').classList._on === true, "Man button active");

applyPidFaceplateState(root, {
  title: "Level PID",
  mode: "automatic",
  loopId: "level",
  pv: 0.2,
  sp: 0.3,
  cv: 3.2,
  coWritable: true,
  spWritable: true,
  dialogBarKey: "sp",
});
assertEq(root.mk("[data-value-title]").textContent, "SP", "SP popup title");
assertEq(root.mk("[data-value-max]").textContent, "0.40", "level SP max is 0.40 m");
assertEq(root.mk("[data-value-unit]").textContent, "m", "level SP unit");
assertEq(root.mk("[data-value-current]").textContent, "0.30", "SP current follows sp");
assertEq(root.mk(".pid-value-focus")._attrs["data-writable"], "1", "SP popup is writable in AUTO");

applyPidFaceplateState(root, {
  title: "Level PID",
  mode: "automatic",
  loopId: "level",
  pv: 0.2,
  sp: 0.3,
  cv: 3.2,
  coWritable: true,
  spWritable: true,
  dialogBarKey: "pv",
});
assertEq(root.mk("[data-value-title]").textContent, "PV", "PV popup title");
assertEq(root.mk("[data-value-max]").textContent, "0.40", "level PV max is 0.40 m");
assertEq(root.mk("[data-value-current]").textContent, "0.20", "PV current follows pv");
assertEq(root.mk(".pid-value-focus")._attrs["data-writable"], "0", "PV popup is read-only");

const host = { innerHTML: "" };
const mounted = mountPidFaceplateElement(host, "analog-bars");
assert(mounted === host, "mount returns host");
assert(host.innerHTML.includes("pid-vbars"), "mounted analog bars");
assert(host.innerHTML.includes("<style>"), "mount injects styles");

if (failed > 0) {
  console.error(`\n${failed} assertion(s) failed`);
  process.exit(1);
}
console.log("\nAll pid faceplate element assertions passed");
process.exit(0);
