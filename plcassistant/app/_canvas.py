"""HTML/JS block program editor for Soft-PLC PLCAssistant (SWD-133).

Serves a self-contained single-page application for editing block programs:
library picker, canvas placement/wiring, JSON program sync, user template editor.
Operator HMI lives in Home Assistant Lovelace — not in this App.
"""

from __future__ import annotations

__all__ = ["get_canvas_html"]


def get_canvas_html() -> str:
    """Return the complete HTML page for the block program editor."""
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="application-name" content="PLC Assistant">
<title>PLCAssistant — block program editor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Sora:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --paper: #e8eef4;
    --paper-2: #dce5ef;
    --mist: #c5d0dc;
    --ink: #122033;
    --ink-soft: #3a4a5c;
    --muted: #5c6b7a;
    --line: #b7c4d1;
    --panel: rgba(248, 251, 255, 0.78);
    --teal: #0f6b62;
    --amber: #b86a10;
    --bad: #a83232;
    --wire: #3a7ca5;
    --pin-in: #2f8f6b;
    --pin-out: #c47a12;
    --radius: 8px;
    --font-display: "Fraunces", "Times New Roman", serif;
    --font-ui: "Sora", "Segoe UI", sans-serif;
    --mono: "Cascadia Code", "Fira Code", "Consolas", monospace;
    --ease: cubic-bezier(0.22, 1, 0.36, 1);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    min-height: 100dvh;
    color: var(--ink);
    font-family: var(--font-ui);
    display: flex;
    flex-direction: column;
    background:
      radial-gradient(ellipse 90% 55% at 12% -10%, var(--mist) 0%, transparent 55%),
      radial-gradient(ellipse 70% 45% at 95% 8%, rgba(184, 197, 214, 0.55) 0%, transparent 50%),
      radial-gradient(ellipse 60% 40% at 50% 100%, rgba(26, 122, 109, 0.08) 0%, transparent 55%),
      linear-gradient(165deg, var(--paper) 0%, var(--paper-2) 100%);
    background-attachment: fixed;
  }

  #app-header {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 6px 14px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--line);
    background: rgba(244, 241, 235, 0.85);
    backdrop-filter: blur(8px);
    flex-shrink: 0;
  }
  #app-header .mark {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: -0.02em;
    color: var(--ink);
  }
  #app-header .subtitle {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--muted);
  }
  #msg-status {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--muted);
  }
  #msg-status.ok { color: var(--teal); }
  #msg-status.err { color: var(--bad); }

  .hmi-banner {
    padding: 8px 18px;
    font-size: 0.78rem;
    color: var(--ink-soft);
    background: rgba(26, 122, 109, 0.08);
    border-bottom: 1px solid var(--line);
    flex-shrink: 0;
  }

  #editor-root {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }

  #editor-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-bottom: 1px solid var(--line);
    background: rgba(255, 252, 247, 0.65);
    flex-shrink: 0;
  }
  .btn {
    font-family: var(--font-ui);
    background: var(--panel);
    border: 1px solid var(--line);
    color: var(--ink);
    padding: 6px 12px;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .btn:hover { border-color: var(--teal); color: var(--teal); }
  .btn.danger { border-color: rgba(179, 58, 58, 0.45); color: var(--bad); }
  .btn.danger:hover { background: rgba(179, 58, 58, 0.08); }

  #editor-main {
    display: flex;
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  #sidebar {
    width: 210px;
    background: rgba(255, 252, 247, 0.7);
    border-right: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    overflow: hidden;
  }
  #sidebar h2, #right h2, #user-editor h2 {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 10px 12px;
    color: var(--muted);
    border-bottom: 1px solid var(--line);
    font-weight: 600;
  }
  #lib-list { flex: 1; overflow-y: auto; padding: 6px; }
  .lib-item {
    background: rgba(255, 255, 255, 0.55);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 8px 10px;
    margin-bottom: 5px;
    cursor: grab;
    font-size: 0.78rem;
    user-select: none;
  }
  .lib-item:hover { border-color: var(--teal); }
  .lib-item .lib-id { font-weight: 600; color: var(--wire); }
  .lib-item .lib-lib { font-size: 0.68rem; color: var(--muted); }
  .lib-item .lib-desc {
    font-size: 0.7rem; color: var(--muted); margin-top: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #add-user-btn { margin: 8px; }

  #canvas-wrap {
    flex: 1;
    position: relative;
    overflow: hidden;
    background:
      linear-gradient(90deg, rgba(197, 206, 217, 0.25) 1px, transparent 1px),
      linear-gradient(rgba(197, 206, 217, 0.25) 1px, transparent 1px),
      rgba(244, 241, 235, 0.4);
    background-size: 24px 24px, 24px 24px, auto;
    min-width: 0;
    min-height: 220px;
  }
  #canvas { width: 100%; height: 100%; cursor: default; }

  #right {
    width: 300px;
    background: rgba(255, 252, 247, 0.7);
    border-left: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    overflow: hidden;
  }
  #yaml-area {
    flex: 1;
    font-family: var(--mono);
    font-size: 0.72rem;
    background: #1a2332;
    color: #d5dde8;
    border: none;
    resize: none;
    padding: 10px;
    outline: none;
    overflow-y: auto;
    min-height: 120px;
  }
  .panel-sep { height: 1px; background: var(--line); }

  #user-editor {
    background: transparent;
    border-top: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    max-height: 300px;
    flex-shrink: 0;
  }
  #user-editor h2 {
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: none;
  }
  #user-editor h2 span.tog { color: var(--teal); }
  #user-form {
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    overflow-y: auto;
    flex: 1;
  }
  #user-form label { font-size: 0.7rem; color: var(--muted); }
  #user-form input, #user-form textarea {
    background: #fff;
    border: 1px solid var(--line);
    color: var(--ink);
    border-radius: var(--radius);
    padding: 5px 8px;
    font-size: 0.76rem;
    font-family: var(--mono);
    width: 100%;
  }
  #user-form textarea { resize: vertical; min-height: 64px; }
  #user-form .row { display: flex; gap: 6px; }
  #user-form .row button { flex: 1; }

  #overlay {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%);
    background: #fffcf7; border: 1px solid var(--line); border-radius: 10px;
    padding: 16px; min-width: 280px; max-width: 420px; z-index: 1000;
    display: none; flex-direction: column; gap: 10px;
    box-shadow: 0 12px 40px rgba(26, 35, 50, 0.12);
  }
  #overlay h3 { color: var(--wire); font-size: 0.9rem; margin-bottom: 4px; font-family: var(--font-display); }
  #overlay label { font-size: 0.75rem; color: var(--muted); }
  #overlay input {
    background: #fff; border: 1px solid var(--line); color: var(--ink);
    border-radius: var(--radius); padding: 5px 8px; font-size: 0.8rem; width: 100%;
  }
  #overlay .btns { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
  #backdrop { position: fixed; inset: 0; background: rgba(26, 35, 50, 0.35); z-index: 999; display: none; }

  .block-g { cursor: move; }
  .block-rect { fill: #fffcf7; stroke: var(--line); stroke-width: 1.5; rx: 4; ry: 4; }
  .block-rect.selected { stroke: var(--teal); stroke-width: 2; }
  .block-title { fill: var(--wire); font-size: 11px; font-weight: 600; font-family: var(--font-ui); }
  .block-id { fill: var(--muted); font-size: 9px; font-family: var(--font-ui); }
  .pin-circle { cursor: crosshair; }
  .pin-in { fill: var(--pin-in); }
  .pin-out { fill: var(--pin-out); }
  .pin-label { fill: var(--ink); font-size: 9px; font-family: var(--font-ui); }
  .wire-path { stroke: var(--wire); stroke-width: 1.5; fill: none; opacity: 0.85; }
  .wire-path.draft { stroke-dasharray: 5,3; opacity: 0.6; }
  .exec-badge { fill: #e8eef4; }
  .exec-text { fill: var(--muted); font-size: 9px; font-family: var(--mono); }

  .panel-tog {
    display: none;
    font-family: var(--font-ui);
    font-size: 0.75rem;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--ink-soft);
    padding: 6px 10px;
    border-radius: var(--radius);
    cursor: pointer;
  }

  @media (max-width: 860px) {
    #editor-main {
      flex-direction: column;
      overflow-y: auto;
    }
    #sidebar, #right {
      width: 100%;
      border-right: none;
      border-left: none;
      max-height: none;
    }
    #sidebar.collapsed, #right.collapsed { display: none; }
    #canvas-wrap {
      min-height: 42dvh;
      flex: 1 0 auto;
    }
    .panel-tog { display: inline-flex; }
    #user-editor { max-height: none; }
  }
</style>
</head>
<body>

<header id="app-header">
  <div class="mark">PLCAssistant</div>
  <div class="subtitle">block program editor</div>
  <div id="msg-status" class="ok">Ready</div>
</header>
<p class="hmi-banner">Operator HMI is in Home Assistant Lovelace — this App is the Soft-PLC program editor.</p>

<div id="editor-root" aria-label="Program editor">
  <div id="editor-bar">
    <button class="btn" onclick="applyRestart()">Apply (restart)</button>
    <button class="btn" onclick="applyHot()">Hot Apply</button>
    <button class="btn danger" onclick="removeSelected()">Remove</button>
    <button type="button" class="panel-tog" onclick="togglePanel('sidebar')">Library</button>
    <button type="button" class="panel-tog" onclick="togglePanel('right')">JSON</button>
  </div>

  <div id="editor-main">
    <div id="sidebar">
      <h2>Block Library</h2>
      <div id="lib-list"></div>
      <button class="btn" id="add-user-btn" onclick="openUserEditor(null)">+ New User Block</button>
    </div>

    <div id="canvas-wrap">
      <svg id="canvas" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto">
            <polygon points="0 0, 6 2, 0 4" fill="var(--wire)" opacity="0.8"/>
          </marker>
        </defs>
        <g id="wires-layer"></g>
        <g id="blocks-layer"></g>
        <line id="draft-wire" class="wire-path draft" style="display:none" marker-end="url(#arrowhead)"/>
      </svg>
    </div>

    <div id="right">
      <h2>Program JSON</h2>
      <textarea id="yaml-area" spellcheck="false" oninput="onYamlEdit()"></textarea>
      <div class="panel-sep"></div>
      <div id="user-editor">
        <h2 onclick="toggleUserEditor()">User Block Editor <span class="tog" id="ue-tog">▲</span></h2>
        <div id="user-form">
          <label>Template ID</label>
          <input id="ue-tid" placeholder="my_block" />
          <label>Description</label>
          <input id="ue-desc" placeholder="What this block does" />
          <label>Pins JSON (array of {name, direction, data_type?, default?})</label>
          <textarea id="ue-pins" rows="3">[{"name":"x","direction":"IN","data_type":"float","default":0.0},{"name":"out","direction":"OUT","data_type":"float"}]</textarea>
          <label>Params JSON (dict of name→default_value)</label>
          <textarea id="ue-params" rows="2">{"gain": 1.0}</textarea>
          <label>Python Body</label>
          <textarea id="ue-body" rows="4" placeholder="out = x * gain"></textarea>
          <div class="row">
            <button class="btn" onclick="saveUserBlock()">Save</button>
            <button class="btn danger" onclick="deleteUserBlock()">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="backdrop" onclick="closeOverlay()"></div>
<div id="overlay">
  <h3 id="ov-title">Block Properties</h3>
  <div id="ov-fields"></div>
  <div class="btns">
    <button class="btn" onclick="applyOverlay()">Apply</button>
    <button class="btn" onclick="resetInstanceOverlay()">Reset to library</button>
    <button class="btn" onclick="closeOverlay()">Cancel</button>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let program = { version: "1.0", instances: {}, wires: [], execution_order: [] };
let library = [];
let selectedId = null;
let dragging = null;
let wiring = null;
let overlayInst = null;
let ueVisible = true;

const BLOCK_W = 140, BLOCK_H_BASE = 30, PIN_ROW = 16, PIN_R = 5;

window.onload = () => {
  loadLibrary();
  loadProgram();
};

function setStatus(msg, ok = true) {
  const el = document.getElementById('msg-status');
  el.textContent = msg;
  el.className = ok ? 'ok' : 'err';
}

function togglePanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('collapsed');
}

// ── API (Ingress-safe relative paths) ──────────────────────────────────────
function apiUrl(path) {
  const rel = String(path || '').replace(/^\//, '');
  let dir = window.location.pathname || '/';
  if (!dir.endsWith('/')) {
    dir = dir + '/';
  }
  return dir + rel;
}

async function apiFetch(path, opts = {}) {
  try {
    const r = await fetch(apiUrl(path), opts);
    if (!r.ok) {
      const txt = await r.text();
      throw new Error(txt || r.statusText);
    }
    return r.headers.get('content-type')?.includes('json') ? r.json() : r.text();
  } catch (e) { setStatus('Error: ' + e.message, false); throw e; }
}

async function loadLibrary() {
  library = await apiFetch('api/library');
  renderLibrary();
}

async function loadProgram() {
  program = await apiFetch('api/program');
  syncYamlPane();
  render();
  setStatus('Loaded', true);
}

async function putProgram(prog) {
  program = await apiFetch('api/program', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(prog)
  });
  syncYamlPane();
  render();
  setStatus('Saved', true);
}

async function applyRestart() {
  await apiFetch('api/apply', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode: 'restart'})
  });
  setStatus('Applied (restart)', true);
}

async function applyHot() {
  await apiFetch('api/apply', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode: 'hot'})
  });
  setStatus('Applied (hot)', true);
}

// ── Library panel ──────────────────────────────────────────────────────────
function renderLibrary() {
  const el = document.getElementById('lib-list');
  el.innerHTML = '';
  for (const t of library) {
    const d = document.createElement('div');
    d.className = 'lib-item';
    d.draggable = true;
    d.dataset.tid = t.template_id;
    d.dataset.lib = t.library;
    d.innerHTML = `<div class="lib-id">${esc(t.template_id)}</div>
      <div class="lib-lib">${esc(t.library)}</div>
      <div class="lib-desc">${esc(t.description||'')}</div>`;
    d.addEventListener('dragstart', e => {
      e.dataTransfer.setData('tid', t.template_id);
      e.dataTransfer.setData('tlib', t.library);
    });
    if (!t.is_builtin) {
      d.title = 'Double-click to edit';
      d.addEventListener('dblclick', () => openUserEditor(t));
    }
    el.appendChild(d);
  }
}

// ── Canvas drag-drop to place ──────────────────────────────────────────────
const canvasSvg = document.getElementById('canvas');
canvasSvg.addEventListener('dragover', e => e.preventDefault());
canvasSvg.addEventListener('drop', async e => {
  e.preventDefault();
  const tid = e.dataTransfer.getData('tid');
  const tlib = e.dataTransfer.getData('tlib');
  if (!tid) return;
  const rect = canvasSvg.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const iid = tid + '_' + Date.now();
  await place(tid, tlib, iid, x, y);
});

async function place(tid, tlib, iid, x, y) {
  program = await apiFetch('api/place', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template_id: tid, library: tlib, instance_id: iid, x, y})
  });
  syncYamlPane();
  render();
  setStatus('Placed ' + tid, true);
}

// ── Canvas render ──────────────────────────────────────────────────────────
function blockHeight(tmpl) {
  const pins = tmpl ? tmpl.pins : [];
  const inPins = pins.filter(p => p.direction === 'IN');
  const outPins = pins.filter(p => p.direction === 'OUT');
  return BLOCK_H_BASE + Math.max(inPins.length, outPins.length) * PIN_ROW + 10;
}

function templateFor(inst) {
  return library.find(t => t.template_id === inst.template_id && t.library === inst.library)
    || (program.user_templates || {})[inst.template_id]
    || null;
}

function pinY(bh, idx, count) {
  const usable = bh - BLOCK_H_BASE - 10;
  return BLOCK_H_BASE + (idx + 0.5) * (usable / Math.max(count, 1));
}

function render() {
  const wl = document.getElementById('wires-layer');
  const bl = document.getElementById('blocks-layer');
  if (!wl || !bl) return;
  wl.innerHTML = ''; bl.innerHTML = '';

  for (const w of (program.wires || [])) {
    const srcInst = program.instances[w.src_instance];
    const dstInst = program.instances[w.dst_instance];
    if (!srcInst || !dstInst) continue;
    const srcT = templateFor(srcInst);
    const dstT = templateFor(dstInst);
    const srcPins = (srcT?.pins||[]).filter(p => p.direction==='OUT');
    const dstPins = (dstT?.pins||[]).filter(p => p.direction==='IN');
    const srcIdx = srcPins.findIndex(p => p.name===w.src_pin);
    const dstIdx = dstPins.findIndex(p => p.name===w.dst_pin);
    const sh = blockHeight(srcT), dh = blockHeight(dstT);
    const x1 = (srcInst.x||0) + BLOCK_W;
    const y1 = (srcInst.y||0) + pinY(sh, srcIdx, srcPins.length);
    const x2 = (dstInst.x||0);
    const y2 = (dstInst.y||0) + pinY(dh, dstIdx, dstPins.length);
    const cp = Math.abs(x2 - x1) * 0.5;
    const path = svgEl('path');
    path.setAttribute('d', `M${x1},${y1} C${x1+cp},${y1} ${x2-cp},${y2} ${x2},${y2}`);
    path.setAttribute('class', 'wire-path');
    path.setAttribute('marker-end', 'url(#arrowhead)');
    path.dataset.wire = JSON.stringify(w);
    path.addEventListener('click', e => { e.stopPropagation(); removeWire(w); });
    wl.appendChild(path);
  }

  const order = [...(program.execution_order||[])];
  for (const iid of Object.keys(program.instances||{})) {
    if (!order.includes(iid)) order.push(iid);
  }
  order.forEach((iid) => {
    const inst = program.instances[iid];
    if (!inst) return;
    const tmpl = templateFor(inst);
    const bh = blockHeight(tmpl);
    const bx = inst.x || 0, by = inst.y || 0;
    const g = svgEl('g');
    g.setAttribute('class', 'block-g');
    g.dataset.iid = iid;

    const rect = svgEl('rect');
    rect.setAttribute('x', bx); rect.setAttribute('y', by);
    rect.setAttribute('width', BLOCK_W); rect.setAttribute('height', bh);
    rect.setAttribute('class', 'block-rect' + (iid===selectedId?' selected':''));
    rect.setAttribute('rx', 4); rect.setAttribute('ry', 4);
    g.appendChild(rect);

    const badge = svgEl('rect');
    badge.setAttribute('x', bx+BLOCK_W-22); badge.setAttribute('y', by+2);
    badge.setAttribute('width', 20); badge.setAttribute('height', 13);
    badge.setAttribute('rx', 3); badge.setAttribute('class', 'exec-badge');
    g.appendChild(badge);
    const badgeTxt = svgEl('text');
    badgeTxt.setAttribute('x', bx+BLOCK_W-12); badgeTxt.setAttribute('y', by+12);
    badgeTxt.setAttribute('class', 'exec-text'); badgeTxt.setAttribute('text-anchor', 'middle');
    badgeTxt.textContent = (program.execution_order||[]).indexOf(iid)+1 || '?';
    g.appendChild(badgeTxt);

    const title = svgEl('text');
    title.setAttribute('x', bx+6); title.setAttribute('y', by+14);
    title.setAttribute('class', 'block-title');
    title.textContent = inst.template_id;
    g.appendChild(title);
    const idTxt = svgEl('text');
    idTxt.setAttribute('x', bx+6); idTxt.setAttribute('y', by+24);
    idTxt.setAttribute('class', 'block-id');
    idTxt.textContent = iid;
    g.appendChild(idTxt);

    const inPins = (tmpl?.pins||[]).filter(p=>p.direction==='IN');
    const outPins = (tmpl?.pins||[]).filter(p=>p.direction==='OUT');
    inPins.forEach((pin, pi) => {
      const py = by + pinY(bh, pi, inPins.length);
      const circ = svgEl('circle');
      circ.setAttribute('cx', bx); circ.setAttribute('cy', py); circ.setAttribute('r', PIN_R);
      circ.setAttribute('class', 'pin-circle pin-in');
      circ.dataset.inst = iid; circ.dataset.pin = pin.name; circ.dataset.dir = 'IN';
      circ.addEventListener('mouseup', onPinMouseUp);
      g.appendChild(circ);
      const lbl = svgEl('text');
      lbl.setAttribute('x', bx+PIN_R+3); lbl.setAttribute('y', py+4);
      lbl.setAttribute('class', 'pin-label'); lbl.textContent = pin.name;
      g.appendChild(lbl);
    });
    outPins.forEach((pin, pi) => {
      const py = by + pinY(bh, pi, outPins.length);
      const circ = svgEl('circle');
      circ.setAttribute('cx', bx+BLOCK_W); circ.setAttribute('cy', py); circ.setAttribute('r', PIN_R);
      circ.setAttribute('class', 'pin-circle pin-out');
      circ.dataset.inst = iid; circ.dataset.pin = pin.name; circ.dataset.dir = 'OUT';
      circ.addEventListener('mousedown', onPinMouseDown);
      g.appendChild(circ);
      const lbl = svgEl('text');
      lbl.setAttribute('x', bx+BLOCK_W-PIN_R-3); lbl.setAttribute('y', py+4);
      lbl.setAttribute('class', 'pin-label'); lbl.setAttribute('text-anchor', 'end');
      lbl.textContent = pin.name;
      g.appendChild(lbl);
    });

    g.addEventListener('mousedown', e => {
      if (e.target.classList.contains('pin-circle')) return;
      selectedId = iid; render();
      dragging = {id: iid, ox: e.clientX - (inst.x||0), oy: e.clientY - (inst.y||0)};
      e.stopPropagation();
    });
    g.addEventListener('dblclick', e => {
      if (e.target.classList.contains('pin-circle')) return;
      openOverlay(iid);
    });

    bl.appendChild(g);
  });
}

canvasSvg.addEventListener('mousemove', e => {
  if (dragging) {
    const inst = program.instances[dragging.id];
    if (inst) {
      inst.x = e.clientX - dragging.ox;
      inst.y = e.clientY - dragging.oy;
      render();
    }
  }
  if (wiring) {
    const dw = document.getElementById('draft-wire');
    const rect = canvasSvg.getBoundingClientRect();
    dw.setAttribute('x2', e.clientX - rect.left);
    dw.setAttribute('y2', e.clientY - rect.top);
  }
});
canvasSvg.addEventListener('mouseup', async () => {
  if (dragging) {
    dragging = null;
    await putProgram(program);
  }
  if (wiring) {
    wiring = null;
    document.getElementById('draft-wire').style.display = 'none';
  }
});
canvasSvg.addEventListener('click', () => { selectedId = null; render(); });

function onPinMouseDown(e) {
  const circ = e.currentTarget;
  if (circ.dataset.dir !== 'OUT') return;
  e.stopPropagation();
  const rect = canvasSvg.getBoundingClientRect();
  const x = parseFloat(circ.getAttribute('cx'));
  const y = parseFloat(circ.getAttribute('cy'));
  wiring = {srcInst: circ.dataset.inst, srcPin: circ.dataset.pin};
  const dw = document.getElementById('draft-wire');
  dw.setAttribute('x1', x); dw.setAttribute('y1', y);
  dw.setAttribute('x2', e.clientX - rect.left); dw.setAttribute('y2', e.clientY - rect.top);
  dw.style.display = '';
}

async function onPinMouseUp(e) {
  const circ = e.currentTarget;
  if (!wiring || circ.dataset.dir !== 'IN') return;
  e.stopPropagation();
  const wire = {
    src_instance: wiring.srcInst, src_pin: wiring.srcPin,
    dst_instance: circ.dataset.inst, dst_pin: circ.dataset.pin
  };
  wiring = null;
  document.getElementById('draft-wire').style.display = 'none';
  program.wires = (program.wires||[]).filter(w =>
    !(w.dst_instance===wire.dst_instance && w.dst_pin===wire.dst_pin)
  );
  program.wires.push(wire);
  await putProgram(program);
}

async function removeWire(wire) {
  program.wires = (program.wires||[]).filter(w =>
    !(w.src_instance===wire.src_instance && w.src_pin===wire.src_pin &&
      w.dst_instance===wire.dst_instance && w.dst_pin===wire.dst_pin)
  );
  await putProgram(program);
}

async function removeSelected() {
  if (!selectedId) { setStatus('Select a block first', false); return; }
  delete program.instances[selectedId];
  program.wires = (program.wires||[]).filter(w =>
    w.src_instance !== selectedId && w.dst_instance !== selectedId
  );
  program.execution_order = (program.execution_order||[]).filter(id => id !== selectedId);
  selectedId = null;
  await putProgram(program);
}

function syncYamlPane() {
  document.getElementById('yaml-area').value = JSON.stringify(program, null, 2);
}

async function onYamlEdit() {
  try {
    const txt = document.getElementById('yaml-area').value;
    program = JSON.parse(txt);
    await putProgram(program);
  } catch (_) { /* JSON parse error; user is still typing */ }
}

function openOverlay(iid) {
  overlayInst = iid;
  const inst = program.instances[iid];
  document.getElementById('ov-title').textContent = `${inst.template_id} [${iid}]`;
  const fields = document.getElementById('ov-fields');
  fields.innerHTML = '';
  for (const [k, v] of Object.entries(inst.params||{})) {
    const lbl = document.createElement('label'); lbl.textContent = k;
    const inp = document.createElement('input');
    inp.id = 'ov_' + k; inp.value = v; inp.type = 'number'; inp.step = 'any';
    fields.appendChild(lbl); fields.appendChild(inp);
  }
  document.getElementById('backdrop').style.display = '';
  document.getElementById('overlay').style.display = 'flex';
}

function closeOverlay() {
  document.getElementById('backdrop').style.display = 'none';
  document.getElementById('overlay').style.display = 'none';
  overlayInst = null;
}

async function applyOverlay() {
  if (!overlayInst) return;
  const inst = program.instances[overlayInst];
  for (const k of Object.keys(inst.params||{})) {
    const el = document.getElementById('ov_' + k);
    if (el) inst.params[k] = parseFloat(el.value);
  }
  closeOverlay();
  await putProgram(program);
}

async function resetInstanceOverlay() {
  if (!overlayInst) return;
  program = await apiFetch('api/reset_instance', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({instance_id: overlayInst})
  });
  syncYamlPane(); render();
  closeOverlay();
  setStatus('Reset ' + overlayInst, true);
}

function toggleUserEditor() {
  ueVisible = !ueVisible;
  document.getElementById('user-form').style.display = ueVisible ? '' : 'none';
  document.getElementById('ue-tog').textContent = ueVisible ? '▲' : '▼';
}

function openUserEditor(tmpl) {
  document.getElementById('ue-tid').value = tmpl?.template_id || '';
  document.getElementById('ue-desc').value = tmpl?.description || '';
  document.getElementById('ue-pins').value = JSON.stringify(
    (tmpl?.pins||[]).map(p => ({name:p.name,direction:p.direction,data_type:p.data_type||'float',...(p.default!==undefined?{default:p.default}:{})})), null, 2
  );
  document.getElementById('ue-params').value = JSON.stringify(tmpl?.params||{}, null, 2);
  document.getElementById('ue-body').value = tmpl?.body || '';
  if (!ueVisible) toggleUserEditor();
}

async function saveUserBlock() {
  const tid = document.getElementById('ue-tid').value.trim();
  if (!tid) { setStatus('Template ID required', false); return; }
  let pins, params;
  try { pins = JSON.parse(document.getElementById('ue-pins').value); }
  catch(e) { setStatus('Pins JSON invalid: ' + e.message, false); return; }
  try { params = JSON.parse(document.getElementById('ue-params').value); }
  catch(e) { setStatus('Params JSON invalid: ' + e.message, false); return; }
  const body = document.getElementById('ue-body').value;
  const desc = document.getElementById('ue-desc').value;
  await apiFetch('api/library/user', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template_id: tid, description: desc, pins, params, body})
  });
  await loadLibrary();
  await loadProgram();
  setStatus('Saved user block ' + tid, true);
}

async function deleteUserBlock() {
  const tid = document.getElementById('ue-tid').value.trim();
  if (!tid) { setStatus('Template ID required', false); return; }
  if (!confirm('Delete user block ' + tid + '?')) return;
  await apiFetch('api/library/user/' + encodeURIComponent(tid), {method: 'DELETE'});
  await loadLibrary();
  await loadProgram();
  setStatus('Deleted ' + tid, true);
}

function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
</script>
</body>
</html>
"""
