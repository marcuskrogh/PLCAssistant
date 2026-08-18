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
assert(kpis.includes('data-metric="cv"'), "kpi CO");
assert(kpis.includes("<span>CO</span>"), "kpi labels CO");
assert(!kpis.includes("<span>CV</span>"), "kpi does not label CV");

const bars = pidFaceplateElementHtml("analog-bars");
assert(bars.includes('data-bar="pv"'), "PV bar");
assert(bars.includes('data-bar="sp"'), "SP bar");
assert(bars.includes('data-bar="co"'), "CO bar");
assert(bars.includes("pid-vbar-track"), "vertical track");
assert(bars.includes("pid-hbar"), "horizontal CO");

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

const assembled = pidFaceplateMarkup({ includeDialog: true, includeHint: true });
assert(assembled.includes("Tap to adjust"), "assembled hint");
const cardOpen = assembled.indexOf('<div class="pid-card">');
const dialogOpen = assembled.indexOf('<div class="pid-dialog"');
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
assert(root.mk('button[data-mode="0"]').classList._on === true, "Man button active");

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
