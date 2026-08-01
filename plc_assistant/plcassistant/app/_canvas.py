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
<title>PLCAssistant — Program engineering</title>
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
  #app-header .subtitle { font-size: 0.82rem; font-weight: 500; color: var(--muted); }
  #top-nav { display: flex; gap: 6px; flex-wrap: wrap; margin-left: 4px; }
  #msg-status { margin-left: auto; font-size: 0.72rem; color: var(--muted); }
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

  .page {
    width: min(920px, 100%);
    margin: 0 auto;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .page-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
  .page h1, .shell-title {
    font-family: var(--font-display);
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--ink);
  }
  .page h1 { font-size: clamp(1.5rem, 9vw, 2.4rem); }
  .helper { color: var(--muted); font-size: 0.86rem; line-height: 1.5; }
  .program-list, .task-list, .call-list, .library-list { display: grid; grid-template-columns: 1fr; gap: 12px; }
  .program-card, .task-card, .call-card, .library-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-shadow: 0 10px 26px rgba(18, 32, 51, 0.08);
  }
  .program-card h2 { font-family: var(--font-display); font-size: 1.35rem; letter-spacing: -0.02em; }
  .program-card .desc, .task-card .desc { color: var(--ink-soft); font-size: 0.86rem; min-height: 1.2em; }
  .card-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .chip {
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 4px 9px;
    background: rgba(255, 252, 247, 0.68);
    font-size: 0.72rem;
    color: var(--ink-soft);
  }
  .chip.running, .chip.ok { border-color: rgba(15, 107, 98, 0.45); color: var(--teal); }
  .chip.not-running { border-color: var(--line); color: var(--ink-soft); }
  .chip.warning { border-color: rgba(184, 106, 16, 0.45); color: var(--amber); }
  .chip.error { border-color: rgba(168, 50, 50, 0.45); color: var(--bad); }

  .btn {
    font-family: var(--font-ui);
    background: var(--panel);
    border: 1px solid var(--line);
    color: var(--ink);
    padding: 7px 12px;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 0.78rem;
    font-weight: 500;
    text-decoration: none;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    gap: 6px;
  }
  .btn:hover, .btn.active { border-color: var(--teal); color: var(--teal); }
  .btn.primary { background: rgba(15, 107, 98, 0.1); border-color: rgba(15, 107, 98, 0.4); color: var(--teal); }
  .btn.danger { border-color: rgba(179, 58, 58, 0.45); color: var(--bad); }
  .btn.danger:hover { background: rgba(179, 58, 58, 0.08); }

  .form-card, .log-list {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  label { font-size: 0.75rem; color: var(--muted); font-weight: 600; }
  input, textarea, select {
    background: #fff;
    border: 1px solid var(--line);
    color: var(--ink);
    border-radius: var(--radius);
    padding: 8px 10px;
    font-size: 0.9rem;
    font-family: var(--font-ui);
    width: 100%;
  }
  textarea { resize: vertical; min-height: 84px; }
  .form-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .form-row > * { flex: 1 1 140px; }
  .library-section { display: grid; grid-template-columns: 1fr; gap: 10px; }
  .library-card h2 { font-family: var(--font-display); font-size: 1.25rem; }
  .library-card.active { border-color: var(--teal); }

  #program-shell { flex: 1; display: none; min-height: 0; flex-direction: column; }
  .shell-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--line);
    background: rgba(255, 252, 247, 0.68);
  }
  .shell-title { font-size: 1.15rem; margin-right: auto; }
  .shell-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
  .shell-page { display: none; flex: 1; min-height: 0; }
  .shell-page.active { display: flex; flex-direction: column; }

  #editor-root { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
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
  #editor-main { display: flex; flex: 1; overflow: hidden; min-height: 0; }
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
  .lib-item .lib-desc { font-size: 0.7rem; color: var(--muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
    min-height: 260px;
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
  #user-editor { background: transparent; border-top: 1px solid var(--line); display: flex; flex-direction: column; max-height: 300px; flex-shrink: 0; }
  #user-editor h2 { cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: none; }
  #user-editor h2 span.tog { color: var(--teal); }
  #user-form { padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; flex: 1; }
  #user-form input, #user-form textarea { font-family: var(--mono); font-size: 0.76rem; padding: 5px 8px; }
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
  #overlay .btns { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
  #backdrop { position: fixed; inset: 0; background: rgba(26, 35, 50, 0.35); z-index: 999; display: none; }

  .log-entry { border-bottom: 1px solid var(--line); padding: 10px 0; display: grid; gap: 4px; }
  .log-entry:last-child { border-bottom: 0; }
  .log-meta { color: var(--muted); font-size: 0.72rem; display: flex; gap: 8px; flex-wrap: wrap; }
  .log-level-info { color: var(--teal); }
  .log-level-warn, .log-level-warning { color: var(--amber); }
  .log-level-error { color: var(--bad); }

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
  .panel-tog { display: none; font-family: var(--font-ui); font-size: 0.75rem; border: 1px solid var(--line); background: var(--panel); color: var(--ink-soft); padding: 6px 10px; border-radius: var(--radius); cursor: pointer; }

  @media (max-width: 860px) {
    #editor-main { flex-direction: column; overflow-y: auto; }
    #sidebar, #right { width: 100%; border-right: none; border-left: none; max-height: none; }
    #sidebar.collapsed, #right.collapsed { display: none; }
    #canvas-wrap { min-height: 42dvh; flex: 1 0 auto; }
    .panel-tog { display: inline-flex; }
    #user-editor { max-height: none; }
  }
</style>
</head>
<body>

<header id="app-header">
  <div class="mark">PLCAssistant</div>
  <div class="subtitle">Program engineering</div>
  <nav id="top-nav" aria-label="Main">
    <a class="btn" id="nav-programs" href="#/programs">Programs</a>
    <a class="btn" id="nav-tasks" href="#/tasks">Tasks</a>
    <a class="btn" id="nav-library" href="#/library">Library</a>
  </nav>
  <div id="msg-status" class="ok">Ready</div>
</header>
<p class="hmi-banner">Operator HMI is in Home Assistant Lovelace — this App is the Soft-PLC Program editor.</p>

<main id="programs-view" class="page" aria-label="Programs">
  <div class="page-head">
    <div>
      <h1>Programs</h1>
      <p class="helper">One Program card per Soft-PLC Program. Status reflects the live applied schedule.</p>
    </div>
    <a class="btn primary" href="#/programs/new" data-route="#/programs/new">Create Program</a>
  </div>
  <div id="program-list" class="program-list" data-testid="program-cards"></div>
</main>

<main id="create-view" class="page" aria-label="Create Program" style="display:none">
  <div class="page-head">
    <div>
      <h1>Create Program</h1>
      <p class="helper">New Programs start empty and unscheduled.</p>
    </div>
    <a class="btn" href="#/programs">Back</a>
  </div>
  <form id="create-form" class="form-card" onsubmit="createProgram(event)">
    <label for="new-name">Name</label>
    <input id="new-name" name="name" required autocomplete="off" placeholder="Tank startup" />
    <label for="new-description">Description (optional)</label>
    <textarea id="new-description" name="description" placeholder="What this Program owns"></textarea>
    <div class="form-row"><button class="btn primary" type="submit">Save</button></div>
  </form>
</main>

<main id="tasks-view" class="page" aria-label="Tasks" style="display:none">
  <div class="page-head">
    <div>
      <h1>Tasks</h1>
      <p class="helper" id="schedule-helper">Edit the saved schedule, then Save or Apply (restart) to the live Soft-PLC.</p>
    </div>
    <div class="form-row">
      <a class="btn primary" href="#/tasks/new">Create Task</a>
      <button class="btn" type="button" onclick="saveSchedule()">Save</button>
      <button class="btn primary" type="button" onclick="applySchedule()">Apply (restart)</button>
    </div>
  </div>
  <div id="task-list" class="task-list" data-testid="task-list"></div>
</main>

<main id="task-create-view" class="page" aria-label="Create Task" style="display:none">
  <div class="page-head">
    <div>
      <h1>Create Task</h1>
      <p class="helper">Tasks run Programs in priority order; lower priority numbers run first.</p>
    </div>
    <a class="btn" href="#/tasks">Back</a>
  </div>
  <form id="task-create-form" class="form-card" onsubmit="createTask(event)">
    <label for="task-new-id">Task id</label>
    <input id="task-new-id" required autocomplete="off" placeholder="main" />
    <label for="task-new-priority">Priority</label>
    <input id="task-new-priority" type="number" required value="1" />
    <label for="task-new-description">Description (optional)</label>
    <textarea id="task-new-description" placeholder="What this Task calls"></textarea>
    <div class="form-row"><button class="btn primary" type="submit">Create</button></div>
  </form>
</main>

<main id="task-detail-view" class="page" aria-label="Task editor" style="display:none">
  <div class="page-head">
    <div>
      <h1 id="task-editor-title">Task</h1>
      <p class="helper">The call list accepts unscheduled Programs, or Programs already on this Task.</p>
    </div>
    <div class="form-row">
      <a class="btn" href="#/tasks">Back</a>
      <button class="btn" type="button" onclick="saveSchedule()">Save</button>
      <button class="btn primary" type="button" onclick="applySchedule()">Apply (restart)</button>
    </div>
  </div>
  <form id="task-meta-form" class="form-card" onsubmit="saveTaskMeta(event)">
    <label for="task-id">Task id</label>
    <input id="task-id" required autocomplete="off" />
    <label for="task-priority">Priority</label>
    <input id="task-priority" type="number" required />
    <label for="task-description">Description (optional)</label>
    <textarea id="task-description"></textarea>
    <div class="form-row">
      <button class="btn primary" type="submit">Save Task</button>
      <button class="btn danger" type="button" onclick="deleteTask()">Delete Task</button>
    </div>
  </form>
  <section class="form-card">
    <h2>Program call list</h2>
    <div id="task-programs" class="call-list"></div>
    <div class="form-row">
      <select id="unscheduled-picker" aria-label="Unscheduled Programs"></select>
      <button class="btn" type="button" onclick="addProgramToTask()">Add Program</button>
    </div>
  </section>
</main>

<main id="library-view" class="page" aria-label="Library" style="display:none">
  <div class="page-head">
    <div>
      <h1>Library</h1>
      <p class="helper">Shipped blocks and custom blocks are edited here. Placing a block copies its current equation and params onto the instance.</p>
    </div>
    <button class="btn primary" type="button" onclick="newCustomLibraryBlock()">Create Custom</button>
  </div>
  <section class="library-section">
    <h2>Shipped</h2>
    <div id="library-shipped" class="library-list"></div>
  </section>
  <section class="library-section">
    <h2>Custom</h2>
    <div id="library-custom" class="library-list"></div>
  </section>
  <form id="library-form" class="form-card" onsubmit="saveLibraryTemplate(event)">
    <h2 id="library-form-title">Select a library block</h2>
    <input type="hidden" id="lib-kind" />
    <label for="lib-tid">Template ID</label>
    <input id="lib-tid" autocomplete="off" />
    <label for="lib-desc">Description</label>
    <input id="lib-desc" autocomplete="off" />
    <label for="lib-pins">Pins JSON (array of {name, direction, data_type?, default?})</label>
    <textarea id="lib-pins" rows="4"></textarea>
    <label for="lib-params">Default params JSON</label>
    <textarea id="lib-params" rows="4"></textarea>
    <label for="lib-body">Math equation</label>
    <textarea id="lib-body" rows="12" spellcheck="false"></textarea>
    <div class="form-row">
      <button class="btn primary" type="submit">Save Library Block</button>
      <button class="btn" type="button" onclick="resetShippedLibraryBlock()">Reset to factory</button>
      <button class="btn danger" type="button" onclick="deleteCustomLibraryBlock()">Delete Custom</button>
    </div>
  </form>
</main>

<div id="program-shell" aria-label="Program shell">
  <div class="shell-bar">
    <a class="btn" href="#/programs">Back</a>
    <div class="shell-title" id="program-title">Program</div>
    <nav class="shell-tabs" aria-label="Program tabs">
      <a class="btn" id="tab-diagram" href="#/programs/tank/diagram">Diagram</a>
      <a class="btn" id="tab-log" href="#/programs/tank/log">Log</a>
      <a class="btn" id="tab-settings" href="#/programs/tank/settings">Settings</a>
    </nav>
  </div>

  <section id="diagram-view" class="shell-page" aria-label="Diagram">
    <div id="editor-root" aria-label="Program editor">
      <div id="editor-bar">
        <button class="btn" onclick="applyRestart()">Apply (restart)</button>
        <button class="btn" onclick="applyHot()">Hot Apply</button>
        <button class="btn" onclick="editSelected()">Edit</button>
        <button class="btn danger" onclick="removeSelected()">Remove</button>
        <button type="button" class="panel-tog" onclick="togglePanel('sidebar')">Library</button>
        <button type="button" class="panel-tog" onclick="togglePanel('right')">JSON</button>
      </div>

      <div id="editor-main">
        <div id="sidebar">
          <h2>Block Library</h2>
          <div id="lib-list"></div>
          <button class="btn" id="add-user-btn" onclick="openUserEditor(null)">+ Program Block</button>
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
            <h2 onclick="toggleUserEditor()">Program Block Editor <span class="tog" id="ue-tog">▲</span></h2>
            <div id="user-form">
              <label>Template ID</label>
              <input id="ue-tid" placeholder="my_block" />
              <label>Description</label>
              <input id="ue-desc" placeholder="What this block does" />
              <label>Pins JSON (array of {name, direction, data_type?, default?})</label>
              <textarea id="ue-pins" rows="3">[{"name":"x","direction":"IN","data_type":"float","default":0.0},{"name":"out","direction":"OUT","data_type":"float"}]</textarea>
              <label>Params JSON (dict of name to default_value)</label>
              <textarea id="ue-params" rows="2">{"gain": 1.0}</textarea>
              <label>Math equation</label>
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
  </section>

  <section id="log-view" class="shell-page page" aria-label="Log">
    <div class="page-head"><h1>Log</h1></div>
    <div id="log-list" class="log-list"></div>
  </section>

  <section id="settings-view" class="shell-page page" aria-label="Settings">
    <div class="page-head"><h1>Settings</h1></div>
    <form id="settings-form" class="form-card" onsubmit="saveSettings(event)">
      <label for="settings-name">Name</label>
      <input id="settings-name" required autocomplete="off" />
      <label for="settings-description">Description (optional)</label>
      <textarea id="settings-description"></textarea>
      <div class="form-row">
        <button class="btn primary" type="submit">Save</button>
        <button class="btn danger" type="button" onclick="deleteProgram()">Delete</button>
      </div>
    </form>
  </section>
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
let program = { version: "1.0", instances: {}, wires: [], execution_order: [] };
let programMeta = null;
let programs = [];
let tasks = [];
let selectedTaskId = null;
let selectedProgramId = null;
let currentTab = 'diagram';
let library = [];
let librarySelection = null;
let selectedId = null;
let dragging = null;
let wiring = null;
let overlayInst = null;
let ueVisible = true;

const BLOCK_W = 140, BLOCK_H_BASE = 30, PIN_ROW = 16, PIN_R = 5;

window.onload = () => {
  window.addEventListener('hashchange', route);
  loadLibrary();
  route();
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

function show(id) {
  for (const elId of ['programs-view', 'create-view', 'tasks-view', 'task-create-view', 'task-detail-view', 'library-view', 'program-shell']) {
    const el = document.getElementById(elId);
    if (el) el.style.display = elId === id ? (id === 'program-shell' ? 'flex' : '') : 'none';
  }
  document.getElementById('nav-programs').classList.toggle('active', id === 'programs-view' || id === 'create-view' || id === 'program-shell');
  document.getElementById('nav-tasks').classList.toggle('active', id === 'tasks-view' || id === 'task-create-view' || id === 'task-detail-view');
  document.getElementById('nav-library').classList.toggle('active', id === 'library-view');
}

function programUrl(id, tab) {
  return '#/programs/' + encodeURIComponent(id) + '/' + tab;
}

async function route() {
  const hash = window.location.hash || '#/programs';
  if (hash === '#/' || hash === '#/programs') {
    selectedProgramId = null;
    show('programs-view');
    await loadPrograms();
    return;
  }
  if (hash === '#/programs/new') {
    selectedProgramId = null;
    show('create-view');
    return;
  }
  if (hash === '#/tasks') {
    selectedTaskId = null;
    show('tasks-view');
    await loadTasks();
    return;
  }
  if (hash === '#/library') {
    selectedProgramId = null;
    selectedTaskId = null;
    show('library-view');
    await loadLibraryPage(null);
    return;
  }
  const libMatch = hash.match(/^#\/library\/([^/]+)$/);
  if (libMatch) {
    selectedProgramId = null;
    selectedTaskId = null;
    show('library-view');
    await loadLibraryPage(decodeURIComponent(libMatch[1]));
    return;
  }
  if (hash === '#/tasks/new') {
    selectedTaskId = null;
    show('task-create-view');
    return;
  }
  const taskMatch = hash.match(/^#\/tasks\/([^/]+)$/);
  if (taskMatch) {
    selectedTaskId = decodeURIComponent(taskMatch[1]);
    show('task-detail-view');
    await loadTaskEditor(selectedTaskId);
    return;
  }
  const match = hash.match(/^#\/programs\/([^/]+)\/(diagram|log|settings)$/);
  if (match) {
    selectedProgramId = decodeURIComponent(match[1]);
    currentTab = match[2];
    show('program-shell');
    await loadProgramMeta(selectedProgramId);
    setShellTab(currentTab);
    if (currentTab === 'diagram') {
      await loadLibrary();
      await loadProgram();
    } else if (currentTab === 'log') {
      await loadLog();
    } else {
      renderSettings();
    }
    return;
  }
  window.location.hash = '#/programs';
}

async function loadPrograms() {
  programs = await apiFetch('api/programs');
  const list = document.getElementById('program-list');
  list.innerHTML = '';
  if (!programs.length) {
    list.innerHTML = '<div class="program-card"><p class="helper">No Programs yet.</p></div>';
    return;
  }
  for (const p of programs) {
    const card = document.createElement('article');
    card.className = 'program-card';
    const statusClass = String(p.status || '').replace(/\s+/g, '-');
    card.innerHTML = `<h2>${esc(p.name || p.id)}</h2>
      <p class="desc">${esc(p.description || 'No description')}</p>
      <div class="card-row">
        <span class="chip ${esc(statusClass)}">${esc(p.status)}</span>
        <span class="chip ${esc(p.health)}">health: ${esc(p.health)}</span>
        <span class="chip">${p.task_id ? 'Task ' + esc(p.task_id) : 'No task'}</span>
      </div>
      <div><a class="btn primary" href="${programUrl(p.id, 'diagram')}">Open Diagram</a></div>`;
    list.appendChild(card);
  }
  setStatus('Programs loaded', true);
}

async function loadTasks() {
  tasks = await apiFetch('api/tasks');
  const status = await apiFetch('api/schedule/status');
  const helper = document.getElementById('schedule-helper');
  if (helper) helper.textContent = status.saved_applied
    ? 'Saved schedule is applied to the live Soft-PLC.'
    : 'Saved schedule has pending changes. Apply (restart) to update live Soft-PLC.';
  const list = document.getElementById('task-list');
  list.innerHTML = '';
  if (!tasks.length) {
    list.innerHTML = '<div class="task-card"><p class="helper">No Tasks. The Soft-PLC schedule is empty until you add one.</p></div>';
    setStatus('Tasks loaded', true);
    return;
  }
  for (const t of tasks) {
    const card = document.createElement('article');
    card.className = 'task-card';
    card.innerHTML = `<h2>${esc(t.id)}</h2>
      <p class="desc">${esc(t.description || 'No description')}</p>
      <div class="card-row">
        <span class="chip">priority ${esc(t.priority)}</span>
        <span class="chip">${(t.programs || []).length} Program(s)</span>
      </div>
      <div><a class="btn primary" href="#/tasks/${encodeURIComponent(t.id)}">Edit Task</a></div>`;
    list.appendChild(card);
  }
  setStatus('Tasks loaded', true);
}

async function createTask(event) {
  event.preventDefault();
  const id = document.getElementById('task-new-id').value.trim();
  const priority = parseInt(document.getElementById('task-new-priority').value, 10);
  const description = document.getElementById('task-new-description').value;
  const task = await apiFetch('api/tasks', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, priority, description})
  });
  document.getElementById('task-create-form').reset();
  window.location.hash = '#/tasks/' + encodeURIComponent(task.id);
}

async function loadTaskEditor(id) {
  tasks = await apiFetch('api/tasks');
  const task = tasks.find(t => t.id === id);
  if (!task) {
    setStatus('Task not found', false);
    window.location.hash = '#/tasks';
    return;
  }
  selectedTaskId = task.id;
  document.getElementById('task-editor-title').textContent = 'Task ' + task.id;
  document.getElementById('task-id').value = task.id;
  document.getElementById('task-priority').value = task.priority;
  document.getElementById('task-description').value = task.description || '';
  renderTaskPrograms(task);
  await loadUnscheduledPicker();
}

function currentTask() {
  return tasks.find(t => t.id === selectedTaskId) || null;
}

function renderTaskPrograms(task) {
  const el = document.getElementById('task-programs');
  el.innerHTML = '';
  const ids = task.programs || [];
  if (!ids.length) {
    el.innerHTML = '<p class="helper">No Programs scheduled on this Task.</p>';
    return;
  }
  ids.forEach((pid, idx) => {
    const row = document.createElement('div');
    row.className = 'call-card';
    row.innerHTML = `<strong>${esc(pid)}</strong>
      <div class="form-row">
        <button class="btn" type="button" ${idx === 0 ? 'disabled' : ''} onclick="moveTaskProgram(${idx}, -1)">Up</button>
        <button class="btn" type="button" ${idx === ids.length - 1 ? 'disabled' : ''} onclick="moveTaskProgram(${idx}, 1)">Down</button>
        <button class="btn danger" type="button" onclick="removeProgramFromTask(${idx})">Remove</button>
      </div>`;
    el.appendChild(row);
  });
}

async function loadUnscheduledPicker() {
  const picker = document.getElementById('unscheduled-picker');
  const task = currentTask();
  const unscheduled = await apiFetch('api/programs/unscheduled');
  picker.innerHTML = '';
  for (const p of unscheduled) {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.name ? `${p.name} (${p.id})` : p.id;
    picker.appendChild(opt);
  }
  if (!picker.options.length) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = task ? 'No unscheduled Programs available' : 'Select a Task first';
    picker.appendChild(opt);
  }
}

async function saveTaskMeta(event) {
  event.preventDefault();
  const id = document.getElementById('task-id').value.trim();
  const priority = parseInt(document.getElementById('task-priority').value, 10);
  const description = document.getElementById('task-description').value;
  const task = await apiFetch('api/tasks/' + encodeURIComponent(selectedTaskId), {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, priority, description})
  });
  selectedTaskId = task.id;
  setStatus('Task updated; Save to persist', true);
  window.location.hash = '#/tasks/' + encodeURIComponent(task.id);
}

async function setCurrentTaskPrograms(programIds) {
  const task = await apiFetch('api/tasks/' + encodeURIComponent(selectedTaskId) + '/programs', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({programs: programIds})
  });
  tasks = tasks.map(t => t.id === task.id ? task : t);
  renderTaskPrograms(task);
  await loadUnscheduledPicker();
  setStatus('Task call list updated; Save to persist', true);
}

async function addProgramToTask() {
  const picker = document.getElementById('unscheduled-picker');
  const pid = picker.value;
  const task = currentTask();
  if (!pid || !task) return;
  await setCurrentTaskPrograms([...(task.programs || []), pid]);
}

async function removeProgramFromTask(index) {
  const task = currentTask();
  if (!task) return;
  const ids = [...(task.programs || [])];
  ids.splice(index, 1);
  await setCurrentTaskPrograms(ids);
}

async function moveTaskProgram(index, delta) {
  const task = currentTask();
  if (!task) return;
  const ids = [...(task.programs || [])];
  const next = index + delta;
  if (next < 0 || next >= ids.length) return;
  [ids[index], ids[next]] = [ids[next], ids[index]];
  await setCurrentTaskPrograms(ids);
}

async function deleteTask() {
  if (!selectedTaskId) return;
  if (!confirm('Are you sure you want to delete this Task? Programs on it become unscheduled.')) return;
  await apiFetch('api/tasks/' + encodeURIComponent(selectedTaskId), {method: 'DELETE'});
  setStatus('Task deleted; Save to persist', true);
  window.location.hash = '#/tasks';
}

async function saveSchedule() {
  const status = await apiFetch('api/schedule/save', {method: 'POST'});
  setStatus(status.saved_applied ? 'Saved and applied' : 'Saved; pending apply', true);
  if ((window.location.hash || '').startsWith('#/tasks')) await loadTasks();
}

async function applySchedule() {
  await apiFetch('api/schedule/apply', {method: 'POST'});
  setStatus('Applied saved schedule with restart', true);
  if ((window.location.hash || '').startsWith('#/tasks')) await loadTasks();
}

async function createProgram(event) {
  event.preventDefault();
  const name = document.getElementById('new-name').value.trim();
  const description = document.getElementById('new-description').value;
  const card = await apiFetch('api/programs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, description})
  });
  document.getElementById('create-form').reset();
  window.location.hash = programUrl(card.id, 'diagram');
}

async function loadProgramMeta(id) {
  programMeta = await apiFetch('api/programs/' + encodeURIComponent(id));
  const title = programMeta.name || id;
  document.getElementById('program-title').textContent = title;
  for (const tab of ['diagram', 'log', 'settings']) {
    document.getElementById('tab-' + tab).href = programUrl(id, tab);
  }
}

function setShellTab(tab) {
  for (const name of ['diagram', 'log', 'settings']) {
    document.getElementById(name + '-view').classList.toggle('active', name === tab);
    document.getElementById('tab-' + name).classList.toggle('active', name === tab);
  }
}

async function loadLog() {
  const entries = await apiFetch('api/programs/' + encodeURIComponent(selectedProgramId) + '/log');
  const el = document.getElementById('log-list');
  if (!entries.length) {
    el.innerHTML = '<p class="helper">No log entries yet.</p>';
    return;
  }
  el.innerHTML = '';
  for (const entry of entries) {
    const row = document.createElement('div');
    row.className = 'log-entry';
    const level = String(entry.level || 'info').toLowerCase();
    row.innerHTML = `<div class="log-meta"><span>${esc(entry.ts || '')}</span><strong class="log-level-${esc(level)}">${esc(level)}</strong></div><div>${esc(entry.message || '')}</div>`;
    el.appendChild(row);
  }
}

function renderSettings() {
  document.getElementById('settings-name').value = programMeta?.name || selectedProgramId || '';
  document.getElementById('settings-description').value = programMeta?.description || '';
}

async function saveSettings(event) {
  event.preventDefault();
  const name = document.getElementById('settings-name').value.trim();
  const description = document.getElementById('settings-description').value;
  programMeta = await apiFetch('api/programs/' + encodeURIComponent(selectedProgramId) + '/meta', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, description})
  });
  document.getElementById('program-title').textContent = programMeta.name || selectedProgramId;
  setStatus('Settings saved', true);
}

async function deleteProgram() {
  if (!selectedProgramId) return;
  if (!confirm('Are you sure you want to delete this Program?')) return;
  await apiFetch('api/programs/' + encodeURIComponent(selectedProgramId), {method: 'DELETE'});
  window.location.hash = '#/programs';
}

async function loadLibrary() {
  library = await apiFetch('api/library' + selectedQuery());
  renderLibrary();
}

function libraryDisplayId(t) {
  return t.kind === 'custom' ? 'custom:' + t.template_id : t.template_id;
}

async function loadLibraryPage(selectId) {
  library = await apiFetch('api/library');
  renderLibraryPage();
  const chosen = selectId
    ? library.find(t => libraryDisplayId(t) === selectId || t.template_id === selectId)
    : (library.find(t => t.kind === 'shipped') || library.find(t => t.kind === 'custom') || null);
  if (chosen) openLibraryTemplate(chosen);
  else newCustomLibraryBlock();
  setStatus('Library loaded', true);
}

function renderLibraryPage() {
  const shipped = document.getElementById('library-shipped');
  const custom = document.getElementById('library-custom');
  if (!shipped || !custom) return;
  shipped.innerHTML = '';
  custom.innerHTML = '';
  const addCard = (container, t) => {
    const card = document.createElement('article');
    card.className = 'library-card' + (librarySelection && libraryDisplayId(t) === libraryDisplayId(librarySelection) ? ' active' : '');
    card.innerHTML = `<h2>${esc(t.template_id)}</h2>
      <p class="helper">${esc(t.description || 'No description')}</p>
      <div class="card-row"><span class="chip">${esc(t.library)}</span><span class="chip">${esc(t.kind || '')}</span></div>
      <div><button class="btn" type="button">Edit</button></div>`;
    card.querySelector('button').onclick = () => openLibraryTemplate(t);
    container.appendChild(card);
  };
  for (const t of library.filter(t => t.kind === 'shipped' || t.is_builtin)) addCard(shipped, t);
  for (const t of library.filter(t => t.kind === 'custom')) addCard(custom, t);
  if (!custom.children.length) {
    custom.innerHTML = '<div class="library-card"><p class="helper">No custom blocks yet.</p></div>';
  }
}

function openLibraryTemplate(t) {
  librarySelection = JSON.parse(JSON.stringify(t));
  document.getElementById('library-form-title').textContent = (t.kind === 'custom' ? 'Custom ' : 'Shipped ') + t.template_id;
  document.getElementById('lib-kind').value = t.kind || (t.is_builtin ? 'shipped' : 'custom');
  document.getElementById('lib-tid').value = t.template_id || '';
  document.getElementById('lib-tid').disabled = (t.kind !== 'custom');
  document.getElementById('lib-desc').value = t.description || '';
  document.getElementById('lib-pins').value = JSON.stringify(t.pins || [], null, 2);
  document.getElementById('lib-params').value = JSON.stringify(t.params || {}, null, 2);
  document.getElementById('lib-body').value = t.body || '';
  renderLibraryPage();
}

function newCustomLibraryBlock() {
  const t = {
    kind: 'custom',
    library: 'custom',
    template_id: '',
    description: '',
    pins: [{name:'x', direction:'IN', data_type:'float', default:0.0}, {name:'out', direction:'OUT', data_type:'float'}],
    params: {gain: 1.0},
    body: 'out = x * gain'
  };
  openLibraryTemplate(t);
}

async function saveLibraryTemplate(event) {
  event.preventDefault();
  const kind = document.getElementById('lib-kind').value || 'custom';
  const tid = document.getElementById('lib-tid').value.trim();
  if (!tid) { setStatus('Template ID required', false); return; }
  let pins, params;
  try { pins = JSON.parse(document.getElementById('lib-pins').value); }
  catch(e) { setStatus('Pins JSON invalid: ' + e.message, false); return; }
  try { params = JSON.parse(document.getElementById('lib-params').value); }
  catch(e) { setStatus('Params JSON invalid: ' + e.message, false); return; }
  const payload = {
    template_id: tid,
    description: document.getElementById('lib-desc').value,
    pins,
    params,
    body: document.getElementById('lib-body').value
  };
  if (kind === 'shipped') {
    await apiFetch('api/library/shipped/' + encodeURIComponent(tid), {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
  } else {
    await apiFetch('api/library/custom', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
  }
  await loadLibraryPage(kind === 'custom' ? 'custom:' + tid : tid);
  setStatus('Saved library block ' + tid, true);
}

async function resetShippedLibraryBlock() {
  const kind = document.getElementById('lib-kind').value;
  const tid = document.getElementById('lib-tid').value.trim();
  if (kind !== 'shipped' || !tid) { setStatus('Select a shipped block first', false); return; }
  await apiFetch('api/library/shipped/' + encodeURIComponent(tid) + '/reset', {method: 'POST'});
  await loadLibraryPage(tid);
  setStatus('Reset ' + tid + ' to factory', true);
}

async function deleteCustomLibraryBlock() {
  const kind = document.getElementById('lib-kind').value;
  const tid = document.getElementById('lib-tid').value.trim();
  if (kind !== 'custom' || !tid) { setStatus('Select a custom block first', false); return; }
  if (!confirm('Delete custom library block ' + tid + '?')) return;
  await apiFetch('api/library/custom/' + encodeURIComponent(tid), {method: 'DELETE'});
  await loadLibraryPage(null);
  setStatus('Deleted custom block ' + tid, true);
}

function selectedQuery() {
  return selectedProgramId ? '?id=' + encodeURIComponent(selectedProgramId) : '';
}

async function loadProgram() {
  if (!selectedProgramId) program = await apiFetch('api/program');
  else program = await apiFetch('api/program' + selectedQuery());
  syncYamlPane();
  render();
  setStatus('Loaded', true);
}

async function putProgram(prog) {
  const path = 'api/program' + selectedQuery();
  program = await apiFetch(path, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(prog)
  });
  syncYamlPane();
  render();
  setStatus('Saved', true);
}

async function applyRestart() {
  await apiFetch('api/apply' + selectedQuery(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode: 'restart', program_id: selectedProgramId})
  });
  setStatus('Applied (restart)', true);
}

async function applyHot() {
  await apiFetch('api/apply' + selectedQuery(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mode: 'hot', program_id: selectedProgramId})
  });
  setStatus('Applied (hot)', true);
}

function renderLibrary() {
  const el = document.getElementById('lib-list');
  if (!el) return;
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
  program = await apiFetch('api/place' + selectedQuery(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template_id: tid, library: tlib, instance_id: iid, x, y, program_id: selectedProgramId})
  });
  syncYamlPane();
  render();
  setStatus('Placed ' + tid, true);
}

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
  } catch (_) { }
}

function openOverlay(iid) {
  overlayInst = iid;
  const inst = program.instances[iid];
  document.getElementById('ov-title').textContent = `${inst.template_id} [${iid}]`;
  const fields = document.getElementById('ov-fields');
  fields.innerHTML = '';
  const eqLabel = document.createElement('label'); eqLabel.textContent = 'Math equation';
  const eq = document.createElement('textarea');
  eq.id = 'ov_equation'; eq.rows = 10; eq.spellcheck = false; eq.value = inst.equation || '';
  fields.appendChild(eqLabel); fields.appendChild(eq);
  for (const [k, v] of Object.entries(inst.params||{})) {
    const lbl = document.createElement('label'); lbl.textContent = k;
    const inp = document.createElement('input');
    inp.id = 'ov_' + k; inp.value = v; inp.type = typeof v === 'boolean' ? 'text' : 'number'; inp.step = 'any';
    fields.appendChild(lbl); fields.appendChild(inp);
  }
  document.getElementById('backdrop').style.display = '';
  document.getElementById('overlay').style.display = 'flex';
}

function editSelected() {
  if (!selectedId) { setStatus('Select a block first', false); return; }
  openOverlay(selectedId);
}

function closeOverlay() {
  document.getElementById('backdrop').style.display = 'none';
  document.getElementById('overlay').style.display = 'none';
  overlayInst = null;
}

async function applyOverlay() {
  if (!overlayInst) return;
  const inst = program.instances[overlayInst];
  const eq = document.getElementById('ov_equation');
  if (eq) inst.equation = eq.value;
  for (const k of Object.keys(inst.params||{})) {
    const el = document.getElementById('ov_' + k);
    if (!el) continue;
    if (typeof inst.params[k] === 'boolean') {
      const raw = String(el.value).trim().toLowerCase();
      if (raw !== 'true' && raw !== 'false' && raw !== '1' && raw !== '0') {
        setStatus('Invalid boolean for ' + k + ' (use true/false)', false);
        return;
      }
      inst.params[k] = raw === 'true' || raw === '1';
    } else {
      const n = parseFloat(el.value);
      if (!Number.isFinite(n)) {
        setStatus('Invalid number for ' + k, false);
        return;
      }
      inst.params[k] = n;
    }
  }
  closeOverlay();
  await putProgram(program);
}

async function resetInstanceOverlay() {
  if (!overlayInst) return;
  program = await apiFetch('api/reset_instance' + selectedQuery(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({instance_id: overlayInst, program_id: selectedProgramId})
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
  await apiFetch('api/library/user' + selectedQuery(), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({template_id: tid, description: desc, pins, params, body, program_id: selectedProgramId})
  });
  await loadLibrary();
  await loadProgram();
  setStatus('Saved user block ' + tid, true);
}

async function deleteUserBlock() {
  const tid = document.getElementById('ue-tid').value.trim();
  if (!tid) { setStatus('Template ID required', false); return; }
  if (!confirm('Delete user block ' + tid + '?')) return;
  await apiFetch('api/library/user/' + encodeURIComponent(tid) + selectedQuery(), {method: 'DELETE'});
  await loadLibrary();
  await loadProgram();
  setStatus('Deleted ' + tid, true);
}

function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
</script>
</body>
</html>
"""
