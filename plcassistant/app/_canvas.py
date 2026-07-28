"""HTML/JS visual canvas for the block program editor (SWD-120).

Serves a self-contained single-page application that:
- Shows a block canvas where blocks can be placed and wired.
- Displays the JSON representation in a sync'd textarea.
- Provides a library picker for builtin and user templates.
- Allows editing user block Python bodies in-App.
"""

from __future__ import annotations


def get_canvas_html() -> str:
    """Return the complete HTML page for the visual canvas."""
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PLC Assistant — Block Editor</title>
<style>
  :root {
    --bg: #1a1a2e; --panel: #16213e; --card: #0f3460;
    --accent: #e94560; --text: #eaeaea; --muted: #888;
    --wire: #4fc3f7; --pin-in: #81c784; --pin-out: #ffb74d;
    --border: #2a3a5c; --radius: 6px; --mono: 'Cascadia Code', 'Fira Code', monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif;
         display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

  /* ── Top bar ── */
  #topbar { background: var(--panel); border-bottom: 1px solid var(--border);
            padding: 8px 16px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
  #topbar h1 { font-size: 1rem; font-weight: 600; color: var(--accent); }
  .btn { background: var(--card); border: 1px solid var(--border); color: var(--text);
         padding: 5px 12px; border-radius: var(--radius); cursor: pointer; font-size: 0.8rem; }
  .btn:hover { background: var(--accent); border-color: var(--accent); }
  .btn.danger { border-color: #c62828; }
  .btn.danger:hover { background: #c62828; border-color: #c62828; }
  #status { margin-left: auto; font-size: 0.75rem; color: var(--muted); }
  #status.ok { color: #81c784; } #status.err { color: var(--accent); }

  /* ── Main layout ── */
  #main { display: flex; flex: 1; overflow: hidden; }

  /* ── Left sidebar: library ── */
  #sidebar { width: 220px; background: var(--panel); border-right: 1px solid var(--border);
             display: flex; flex-direction: column; flex-shrink: 0; overflow: hidden; }
  #sidebar h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
                padding: 10px 12px; color: var(--muted); border-bottom: 1px solid var(--border); }
  #lib-list { flex: 1; overflow-y: auto; padding: 6px; }
  .lib-item { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
              padding: 8px 10px; margin-bottom: 5px; cursor: grab; font-size: 0.8rem;
              user-select: none; }
  .lib-item:hover { border-color: var(--accent); }
  .lib-item .lib-id { font-weight: 600; color: var(--wire); }
  .lib-item .lib-lib { font-size: 0.7rem; color: var(--muted); }
  .lib-item .lib-desc { font-size: 0.72rem; color: var(--muted); margin-top: 2px;
                        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #add-user-btn { margin: 8px; }

  /* ── Canvas area ── */
  #canvas-wrap { flex: 1; position: relative; overflow: hidden; background: var(--bg); }
  #canvas { width: 100%; height: 100%; cursor: default; }

  /* ── Right panel: YAML + user editor ── */
  #right { width: 320px; background: var(--panel); border-left: 1px solid var(--border);
           display: flex; flex-direction: column; flex-shrink: 0; overflow: hidden; }
  #right h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
              padding: 10px 12px; color: var(--muted); border-bottom: 1px solid var(--border); }
  #yaml-area { flex: 1; font-family: var(--mono); font-size: 0.72rem; background: #0d1b2a;
               color: #b0c4de; border: none; resize: none; padding: 10px; outline: none;
               overflow-y: auto; }
  .panel-sep { height: 1px; background: var(--border); }

  /* ── User template editor (collapsible) ── */
  #user-editor { background: var(--panel); border-top: 1px solid var(--border);
                 display: flex; flex-direction: column; max-height: 320px; flex-shrink: 0; }
  #user-editor h2 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
                    padding: 8px 12px; color: var(--muted); cursor: pointer;
                    display: flex; justify-content: space-between; align-items: center; }
  #user-editor h2 span.tog { color: var(--accent); }
  #user-form { padding: 8px 10px; display: flex; flex-direction: column; gap: 6px;
               overflow-y: auto; flex: 1; }
  #user-form label { font-size: 0.72rem; color: var(--muted); }
  #user-form input, #user-form textarea {
    background: #0d1b2a; border: 1px solid var(--border); color: var(--text);
    border-radius: var(--radius); padding: 5px 8px; font-size: 0.78rem;
    font-family: var(--mono); width: 100%;
  }
  #user-form textarea { resize: vertical; min-height: 80px; }
  #user-form .row { display: flex; gap: 6px; }
  #user-form .row button { flex: 1; }

  /* ── Overlay for block properties ── */
  #overlay { position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%);
             background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
             padding: 16px; min-width: 280px; max-width: 420px; z-index: 1000;
             display: none; flex-direction: column; gap: 10px; }
  #overlay h3 { color: var(--wire); font-size: 0.9rem; margin-bottom: 4px; }
  #overlay label { font-size: 0.75rem; color: var(--muted); }
  #overlay input { background: #0d1b2a; border: 1px solid var(--border); color: var(--text);
                   border-radius: var(--radius); padding: 5px 8px; font-size: 0.8rem; width: 100%; }
  #overlay .btns { display: flex; gap: 8px; justify-content: flex-end; }
  #backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 999; display: none; }

  /* SVG blocks */
  .block-g { cursor: move; }
  .block-rect { fill: var(--card); stroke: var(--border); stroke-width: 1.5; rx: 4; ry: 4; }
  .block-rect.selected { stroke: var(--accent); stroke-width: 2; }
  .block-title { fill: var(--wire); font-size: 11px; font-weight: 600; font-family: system-ui; }
  .block-id { fill: var(--muted); font-size: 9px; font-family: system-ui; }
  .pin-circle { cursor: crosshair; }
  .pin-in { fill: var(--pin-in); }
  .pin-out { fill: var(--pin-out); }
  .pin-label { fill: var(--text); font-size: 9px; font-family: system-ui; }
  .wire-path { stroke: var(--wire); stroke-width: 1.5; fill: none; opacity: 0.8; }
  .wire-path.draft { stroke-dasharray: 5,3; opacity: 0.6; }
  .exec-badge { fill: #37474f; }
  .exec-text { fill: var(--muted); font-size: 9px; font-family: monospace; }
</style>
</head>
<body>

<!-- Top bar -->
<div id="topbar">
  <h1>PLC Assistant — Block Editor</h1>
  <button class="btn" onclick="applyRestart()">↺ Apply (restart)</button>
  <button class="btn" onclick="applyHot()">⚡ Hot Apply</button>
  <button class="btn danger" onclick="removeSelected()">✕ Remove</button>
  <span id="status" class="ok">Ready</span>
</div>

<!-- Main layout -->
<div id="main">

  <!-- Library sidebar -->
  <div id="sidebar">
    <h2>Block Library</h2>
    <div id="lib-list"></div>
    <button class="btn" id="add-user-btn" onclick="openUserEditor(null)">+ New User Block</button>
  </div>

  <!-- Canvas -->
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

  <!-- Right panel -->
  <div id="right">
    <h2>Program JSON</h2>
    <textarea id="yaml-area" spellcheck="false" oninput="onYamlEdit()"></textarea>
    <div class="panel-sep"></div>
    <!-- User block editor (inline) -->
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
          <button class="btn" onclick="saveUserBlock()">💾 Save</button>
          <button class="btn danger" onclick="deleteUserBlock()">🗑 Delete</button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Block properties overlay -->
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
let dragging = null;       // {id, ox, oy}
let wiring = null;         // {srcInst, srcPin, x1, y1}
let overlayInst = null;    // instance_id being edited in overlay
let ueVisible = true;

const BLOCK_W = 140, BLOCK_H_BASE = 30, PIN_ROW = 16, PIN_R = 5;

// ── Init ───────────────────────────────────────────────────────────────────
window.onload = () => { fetchLibrary(); fetchProgram(); };

function setStatus(msg, ok = true) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = ok ? 'ok' : 'err';
}

// ── API calls ──────────────────────────────────────────────────────────────
// HA Ingress serves this page under /api/hassio_ingress/<token>/. Absolute
// fetch('/api/...') hits Home Assistant Core (404) instead of the Soft-PLC App.
// Resolve every API path relative to the current document directory.
function apiUrl(path) {
  const rel = String(path || '').replace(/^\//, '');
  let dir = window.location.pathname || '/';
  // Ingress may omit the trailing slash. Treat the whole pathname as a
  // directory (append '/') — do NOT strip the last segment (that drops the
  // ingress token and yields /api/hassio_ingress/api/...).
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

async function fetchLibrary() {
  library = await apiFetch('api/library');
  renderLibrary();
}

async function fetchProgram() {
  program = await apiFetch('api/program');
  syncYamlPane();
  renderCanvas();
  setStatus('Loaded', true);
}

async function putProgram(prog) {
  program = await apiFetch('api/program', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(prog)
  });
  syncYamlPane();
  renderCanvas();
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
  // Hot-apply authority is controlled by the server-side env var
  // PLCASSISTANT_SUPERUSER_HOT_APPLY=1. The server ignores any
  // superuser field from the client.
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
  const resp = await apiFetch('api/place', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template_id: tid, library: tlib, instance_id: iid, x, y})
  });
  program = resp;
  syncYamlPane();
  renderCanvas();
  setStatus('Placed ' + tid, true);
});

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

function renderCanvas() {
  const wl = document.getElementById('wires-layer');
  const bl = document.getElementById('blocks-layer');
  wl.innerHTML = ''; bl.innerHTML = '';

  // Draw wires
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

  // Draw blocks in execution order (then any not in order)
  const order = [...(program.execution_order||[])];
  for (const iid of Object.keys(program.instances||{})) {
    if (!order.includes(iid)) order.push(iid);
  }
  order.forEach((iid, idx) => {
    const inst = program.instances[iid];
    if (!inst) return;
    const tmpl = templateFor(inst);
    const bh = blockHeight(tmpl);
    const bx = inst.x || 0, by = inst.y || 0;
    const g = svgEl('g');
    g.setAttribute('class', 'block-g');
    g.dataset.iid = iid;

    // Background rect
    const rect = svgEl('rect');
    rect.setAttribute('x', bx); rect.setAttribute('y', by);
    rect.setAttribute('width', BLOCK_W); rect.setAttribute('height', bh);
    rect.setAttribute('class', 'block-rect' + (iid===selectedId?' selected':''));
    rect.setAttribute('rx', 4); rect.setAttribute('ry', 4);
    g.appendChild(rect);

    // Execution order badge
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

    // Title
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

    // Pins
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

    // Drag + select
    g.addEventListener('mousedown', e => {
      if (e.target.classList.contains('pin-circle')) return;
      selectedId = iid; renderCanvas();
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

// ── Drag to move blocks ────────────────────────────────────────────────────
canvasSvg.addEventListener('mousemove', e => {
  if (dragging) {
    const inst = program.instances[dragging.id];
    if (inst) {
      inst.x = e.clientX - dragging.ox;
      inst.y = e.clientY - dragging.oy;
      renderCanvas();
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
canvasSvg.addEventListener('click', () => { selectedId = null; renderCanvas(); });

// ── Pin wiring ─────────────────────────────────────────────────────────────
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

// ── Remove selected block ──────────────────────────────────────────────────
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

// ── YAML textarea sync ─────────────────────────────────────────────────────
function syncYamlPane() {
  document.getElementById('yaml-area').value = JSON.stringify(program, null, 2);
}

async function onYamlEdit() {
  try {
    const txt = document.getElementById('yaml-area').value;
    const parsed = JSON.parse(txt);
    program = parsed;
    await putProgram(program);
  } catch (_) { /* JSON parse error; user is still typing */ }
}

// ── Block properties overlay ───────────────────────────────────────────────
function openOverlay(iid) {
  overlayInst = iid;
  const inst = program.instances[iid];
  const tmpl = templateFor(inst);
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
  const resp = await apiFetch('api/reset_instance', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({instance_id: overlayInst})
  });
  program = resp;
  syncYamlPane(); renderCanvas();
  closeOverlay();
  setStatus('Reset ' + overlayInst, true);
}

// ── User block editor ──────────────────────────────────────────────────────
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
  await fetchLibrary();
  await fetchProgram();
  setStatus('Saved user block ' + tid, true);
}

async function deleteUserBlock() {
  const tid = document.getElementById('ue-tid').value.trim();
  if (!tid) { setStatus('Template ID required', false); return; }
  if (!confirm('Delete user block ' + tid + '?')) return;
  await apiFetch('api/library/user/' + encodeURIComponent(tid), {method: 'DELETE'});
  await fetchLibrary();
  await fetchProgram();
  setStatus('Deleted ' + tid, true);
}

// ── Helpers ────────────────────────────────────────────────────────────────
function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
</script>
</body>
</html>
"""
