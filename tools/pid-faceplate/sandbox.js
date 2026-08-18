/**
 * Developer sandbox for PID faceplate elements. Local mock state only.
 */
import {
  PID_FACEPLATE_ELEMENT_CATALOG,
  PID_PV_MAX_LEVEL,
  PID_PV_MAX_FLOW,
  PID_CV_MAX_LEVEL,
  PID_CV_MAX_FLOW,
  pidFaceplateStyles,
  pidFaceplateMarkup,
  applyPidFaceplateState,
  mountPidFaceplateElement,
  pidBarValueFromPointer,
  commitSpValue,
  pidOperatorWriteTarget,
} from "../../custom_components/plcassistant/www/pid-faceplate-elements.js";

const loopEl = document.querySelector("#loop");
const modeEl = document.querySelector("#mode");
const pvEl = document.querySelector("#pv");
const spEl = document.querySelector("#sp");
const cvEl = document.querySelector("#cv");
const isolates = document.querySelector("#isolates");
const mockLevel = document.querySelector("#mock-level");
const mockFlow = document.querySelector("#mock-flow");

function scaleFor(loopId) {
  if (loopId === "flow") {
    return { pv: PID_PV_MAX_FLOW, cv: PID_CV_MAX_FLOW, pvUnit: "L/min", cvUnit: "%" };
  }
  return { pv: PID_PV_MAX_LEVEL, cv: PID_CV_MAX_LEVEL, pvUnit: "m", cvUnit: "L/min" };
}

function snapshot(loopId) {
  const scale = scaleFor(loopId);
  const mode = modeEl.value;
  return {
    title: loopId === "flow" ? "Flow PID" : "Level PID",
    mode,
    loopId,
    pv: Number(pvEl.value),
    sp: Number(spEl.value),
    cv: Number(cvEl.value),
    spWritable: mode === "automatic" && loopId === "level",
    coWritable: true,
    writeTarget: pidOperatorWriteTarget(mode, {
      spWritable: mode === "automatic" && loopId === "level",
      coWritable: true,
    }),
    scale,
  };
}

function paintReadouts() {
  const loopId = loopEl.value;
  const scale = scaleFor(loopId);
  pvEl.max = String(scale.pv);
  spEl.max = String(scale.pv);
  cvEl.max = String(scale.cv);
  document.querySelector('[data-readout="pv"]').textContent =
    `${Number(pvEl.value).toFixed(2)} ${scale.pvUnit}`;
  document.querySelector('[data-readout="sp"]').textContent =
    `${Number(spEl.value).toFixed(2)} ${scale.pvUnit}`;
  document.querySelector('[data-readout="cv"]').textContent =
    `${Number(cvEl.value).toFixed(2)} ${scale.cvUnit}`;
}

function bindLocalChrome(root, loopId) {
  root.addEventListener("click", (ev) => {
    const modeBtn = ev.target.closest?.("button[data-mode]");
    if (modeBtn) {
      const code = modeBtn.getAttribute("data-mode");
      modeEl.value = code === "0" ? "manual" : code === "2" ? "remote" : "automatic";
      refresh();
      return;
    }
    const barBtn = ev.target.closest?.("[data-bar]");
    if (!barBtn || barBtn.getAttribute("data-writable") !== "1") return;
    const track = barBtn.querySelector(".pid-vbar-track, .pid-cv-track");
    if (!track) return;
    const key = barBtn.getAttribute("data-bar");
    const scale = scaleFor(loopId);
    const orientation = key === "co" ? "horizontal" : "vertical";
    const max = key === "co" ? scale.cv : scale.pv;
    const raw = pidBarValueFromPointer(
      track.getBoundingClientRect(),
      ev.clientX,
      ev.clientY,
      0,
      max,
      orientation
    );
    const committed = commitSpValue(raw);
    if (committed === null) return;
    if (key === "co") cvEl.value = String(committed);
    if (key === "sp") spEl.value = String(committed);
    refresh();
  });
}

function mountIsolates() {
  isolates.innerHTML = "";
  for (const item of PID_FACEPLATE_ELEMENT_CATALOG) {
    const tile = document.createElement("div");
    tile.className = "tile";
    tile.dataset.element = item.id;
    tile.innerHTML = `<h3>${item.title}</h3><p>${item.description}</p><div data-host></div>`;
    isolates.appendChild(tile);
    mountPidFaceplateElement(tile.querySelector("[data-host]"), item.id, {
      withStyles: true,
    });
  }
}

function mountAssembled() {
  const style = `<style>${pidFaceplateStyles()}</style>`;
  mockLevel.innerHTML =
    style +
    pidFaceplateMarkup({ includeDialog: false, includeHint: false });
  mockFlow.innerHTML =
    style +
    pidFaceplateMarkup({ includeDialog: false, includeHint: false });
  bindLocalChrome(mockLevel, "level");
  bindLocalChrome(mockFlow, "flow");
}

function refresh() {
  paintReadouts();
  const selected = snapshot(loopEl.value);
  isolates.querySelectorAll("[data-host]").forEach((host) => {
    applyPidFaceplateState(host, selected);
  });
  applyPidFaceplateState(mockLevel, snapshot("level"));
  applyPidFaceplateState(mockFlow, {
    ...snapshot("flow"),
    title: "Flow PID",
    loopId: "flow",
    spWritable: false,
  });
}

for (const el of [loopEl, modeEl, pvEl, spEl, cvEl]) {
  el.addEventListener("input", refresh);
  el.addEventListener("change", refresh);
}

mountIsolates();
mountAssembled();
refresh();
