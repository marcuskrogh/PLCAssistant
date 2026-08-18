/**
 * Developer sandbox for PID faceplate elements. Local mock state only.
 */
import {
  PID_FACEPLATE_ELEMENT_CATALOG,
  PID_PV_MAX_LEVEL,
  PID_PV_MAX_FLOW,
  PID_CV_MAX_LEVEL,
  PID_CV_MAX_FLOW,
  PID_TUNE_KEYS,
  PID_TUNE_BOOL_KEYS,
  pidFaceplateStyles,
  pidFaceplateMarkup,
  applyPidFaceplateState,
  applyPidSettingsPane,
  mountPidFaceplateElement,
  pidOperatorWriteTarget,
  pidNudgeValue,
  pidNudgeRange,
  commitSpValue,
  parseSpValue,
  resolveFaceplateClick,
  applyPidValueDialog,
  pidBarEditorKey,
  pidNormalizeBarKey,
  rampSetpoint,
} from "../../custom_components/plcassistant/www/pid-faceplate-elements.js?v=sp-ramp-full";

const loopEl = document.querySelector("#loop");
const modeEl = document.querySelector("#mode");
const pvEl = document.querySelector("#pv");
const spEl = document.querySelector("#sp");
const cvEl = document.querySelector("#cv");
const isolates = document.querySelector("#isolates");
const mockLevel = document.querySelector("#mock-level");
const mockFlow = document.querySelector("#mock-flow");

function defaultTune(loopId) {
  const cvMax = loopId === "flow" ? PID_CV_MAX_FLOW : PID_CV_MAX_LEVEL;
  return {
    kp: loopId === "flow" ? 12 : 40,
    ki: loopId === "flow" ? 2 : 5,
    kd: 0,
    u0: 0,
    beta: 1,
    direct_acting: false,
    form: "Parallel",
    cv_min: 0,
    cv_max: cvMax,
    hold_when_stopped: loopId !== "flow",
    ts: 0.1,
    tf_ts: 0,
    sp_ramp_max: loopId === "flow" ? 1.0 : 0.05,
  };
}

const tunings = {
  level: defaultTune("level"),
  flow: defaultTune("flow"),
};

const settingsPaneByLoop = {
  level: "gains",
  flow: "gains",
};

const dialogBarByLoop = {
  level: "co",
  flow: "co",
};

const spLiveByLoop = {
  level: Number(spEl.value),
  flow: Number(spEl.value),
};

let lastRampAt = performance.now();

function scaleFor(loopId) {
  if (loopId === "flow") {
    return { pv: PID_PV_MAX_FLOW, cv: PID_CV_MAX_FLOW, pvUnit: "L/min", cvUnit: "%" };
  }
  return { pv: PID_PV_MAX_LEVEL, cv: PID_CV_MAX_LEVEL, pvUnit: "m", cvUnit: "L/min" };
}

function snapshot(loopId) {
  const scale = scaleFor(loopId);
  const mode = modeEl.value;
  const tune = tunings[loopId] || tunings.level;
  return {
    title: loopId === "flow" ? "Flow PID" : "Level PID",
    mode,
    loopId,
    pv: Number(pvEl.value),
    sp: spLiveByLoop[loopId] ?? Number(spEl.value),
    spTarget: Number(spEl.value),
    cv: Number(cvEl.value),
    kp: tune.kp,
    ki: tune.ki,
    kd: tune.kd,
    u0: tune.u0,
    beta: tune.beta,
    direct_acting: tune.direct_acting,
    cv_min: tune.cv_min,
    cv_max: tune.cv_max,
    hold_when_stopped: tune.hold_when_stopped,
    ts: tune.ts,
    tf_ts: tune.tf_ts,
    sp_ramp_max: tune.sp_ramp_max,
    form: tune.form || "Parallel",
    settingsPane: settingsPaneByLoop[loopId] || "gains",
    spWritable: mode === "automatic",
    coWritable: true,
    writeTarget: pidOperatorWriteTarget(mode, {
      spWritable: mode === "automatic",
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

function setDialogOpen(root, selector, open) {
  const dialog = root.querySelector(selector);
  if (!dialog) return;
  if (open) dialog.removeAttribute("hidden");
  else dialog.setAttribute("hidden", "");
}

function closeDialogs(root) {
  setDialogOpen(root, ".pid-value-dialog", false);
  setDialogOpen(root, ".pid-settings-dialog", false);
}

function applyLocalValue(loopId, key, raw) {
  const parsed = parseSpValue(raw);
  const committed = commitSpValue(parsed);
  if (committed === null) return;
  const scale = scaleFor(loopId);
  if (key === "co") {
    cvEl.value = String(Math.max(0, Math.min(scale.cv, committed)));
  } else if (key === "auto") {
    const next = String(Math.max(0, Math.min(scale.pv, committed)));
    spEl.value = next;
  }
}

function applyLocalSettings(root, loopId) {
  const next = { ...tunings[loopId] };
  for (const key of PID_TUNE_KEYS) {
    const input = root.querySelector(`[data-tune="${key}"]`);
    if (!input) continue;
    if (input.type === "checkbox" || PID_TUNE_BOOL_KEYS.includes(key)) {
      next[key] = Boolean(input.checked);
      continue;
    }
    const committed = commitSpValue(parseSpValue(input.value));
    if (committed === null) continue;
    next[key] = committed;
  }
  tunings[loopId] = next;
}

function bindLocalChrome(root, loopId) {
  root.addEventListener("click", (ev) => {
    const action = resolveFaceplateClick(ev.target);
    if (!action) return;
    if (action.type === "mode") {
      const code = action.code;
      modeEl.value = code === "0" ? "manual" : code === "2" ? "remote" : "automatic";
      closeDialogs(root);
      refresh();
      return;
    }
    if (action.type === "close") {
      closeDialogs(root);
      return;
    }
    if (action.type === "open" || action.type === "bar") {
      const state = snapshot(loopId);
      const barKey =
        action.type === "bar"
          ? pidNormalizeBarKey(action.key)
          : state.writeTarget
            ? pidNormalizeBarKey(state.writeTarget)
            : null;
      if (!barKey) return;
      dialogBarByLoop[loopId] = barKey;
      applyPidValueDialog(root, {
        barKey,
        loopId,
        value: barKey === "sp" ? state.sp : barKey === "pv" ? state.pv : state.cv,
        writable:
          (barKey === "sp" && state.writeTarget === "sp") ||
          (barKey === "co" && state.writeTarget === "co"),
      });
      const input = root.querySelector(".pid-value-dialog input[data-sp]");
      if (input) {
        const editorKey = pidBarEditorKey(barKey);
        input.value = String(
          editorKey === "auto" ? state.sp : barKey === "pv" ? state.pv : state.cv
        );
      }
      setDialogOpen(root, ".pid-settings-dialog", false);
      setDialogOpen(root, ".pid-value-dialog", true);
      return;
    }
    if (action.type === "apply") {
      const input = root.querySelector(`input[data-sp="${action.key}"]`);
      applyLocalValue(loopId, action.key, input?.value);
      closeDialogs(root);
      refresh();
      return;
    }
    if (action.type === "nudge") {
      const state = snapshot(loopId);
      if (!state.writeTarget) return;
      const range = pidNudgeRange(state.writeTarget, loopId);
      const current = state.writeTarget === "co" ? state.cv : state.spTarget;
      const next = pidNudgeValue(current, action.delta, range.min, range.max);
      if (next === null) return;
      if (state.writeTarget === "co") cvEl.value = String(next);
      else spEl.value = String(next);
      refresh();
      return;
    }
    if (action.type === "settings") {
      if (action.action === "open") {
        setDialogOpen(root, ".pid-value-dialog", false);
        setDialogOpen(root, ".pid-settings-dialog", true);
      } else if (action.action === "cancel") {
        setDialogOpen(root, ".pid-settings-dialog", false);
      } else if (action.action === "apply") {
        applyLocalSettings(root, loopId);
        closeDialogs(root);
        refresh();
      }
      return;
    }
    if (action.type === "pane") {
      settingsPaneByLoop[loopId] = action.id || "gains";
      applyPidSettingsPane(root, settingsPaneByLoop[loopId]);
    }
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
    pidFaceplateMarkup({ includeDialog: true, includeHint: false });
  mockFlow.innerHTML =
    style +
    pidFaceplateMarkup({ includeDialog: true, includeHint: false });
  bindLocalChrome(mockLevel, "level");
  bindLocalChrome(mockFlow, "flow");
}

function refresh() {
  paintReadouts();
  const selected = snapshot(loopEl.value);
  isolates.querySelectorAll("[data-host]").forEach((host) => {
    applyPidFaceplateState(host, selected);
  });
  applyPidFaceplateState(mockLevel, {
    ...snapshot("level"),
    dialogBarKey: dialogBarByLoop.level,
  });
  applyPidFaceplateState(mockFlow, {
    ...snapshot("flow"),
    title: "Flow PID",
    loopId: "flow",
    spWritable: false,
    dialogBarKey: dialogBarByLoop.flow,
  });
}

for (const el of [loopEl, modeEl, pvEl, spEl, cvEl]) {
  el.addEventListener("input", refresh);
  el.addEventListener("change", refresh);
}

mountIsolates();
mountAssembled();
refresh();

function tickRamp(now) {
  const dt = Math.min(0.25, Math.max(0, (now - lastRampAt) / 1000));
  lastRampAt = now;
  const target = Number(spEl.value);
  let moved = false;
  for (const loopId of ["level", "flow"]) {
    const rate = Number(tunings[loopId]?.sp_ramp_max) || 0;
    const current = spLiveByLoop[loopId];
    const next = rampSetpoint(
      Number.isFinite(current) ? current : target,
      target,
      rate,
      dt
    );
    if (next !== current) moved = true;
    spLiveByLoop[loopId] = next;
  }
  if (moved) refresh();
  requestAnimationFrame(tickRamp);
}

requestAnimationFrame(tickRamp);
