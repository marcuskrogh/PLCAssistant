"""HTML/JS operator dashboard and block program editor (SWD-132 / SWD-120).

Serves a self-contained single-page application that:
- Defaults to an operator dashboard with live runtime signals and Start/Stop/Reset.
- Offers a secondary Program view for the block canvas (place, wire, apply).
- Displays the JSON representation in a sync'd textarea.
- Provides a library picker for builtin and user templates.
- Allows editing user block Python bodies in-App.
"""

from __future__ import annotations


def get_canvas_html() -> str:
    """Return the complete HTML page for the operator dashboard and editor."""
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="application-name" content="PLC Assistant">
<title>PLCAssistant</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Sora:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --paper: #f4f1eb;
    --paper-2: #ebe6dc;
    --mist: #d5dde8;
    --mist-deep: #b8c5d6;
    --ink: #1a2332;
    --ink-soft: #3d4a5c;
    --muted: #6b7789;
    --line: #c5ced9;
    --panel: rgba(255, 252, 247, 0.72);
    --teal: #1a7a6d;
    --teal-bright: #249688;
    --amber: #c47a12;
    --bad: #b33a3a;
    --uncertain: #a67c2a;
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
    background:
      radial-gradient(ellipse 90% 55% at 12% -10%, var(--mist) 0%, transparent 55%),
      radial-gradient(ellipse 70% 45% at 95% 8%, rgba(184, 197, 214, 0.55) 0%, transparent 50%),
      radial-gradient(ellipse 60% 40% at 50% 100%, rgba(26, 122, 109, 0.08) 0%, transparent 55%),
      linear-gradient(165deg, var(--paper) 0%, var(--paper-2) 100%);
    background-attachment: fixed;
  }

  /* ── App chrome ── */
  #app-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 16px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--line);
    background: rgba(244, 241, 235, 0.85);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 40;
  }
  #app-header .mark {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: -0.02em;
    color: var(--ink);
  }
  .view-tabs {
    display: flex;
    gap: 4px;
    background: transparent;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 3px;
  }
  .view-tabs button {
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-weight: 500;
    border: none;
    background: transparent;
    color: var(--muted);
    padding: 7px 14px;
    border-radius: 6px;
    cursor: pointer;
  }
  .view-tabs button.active {
    background: var(--ink);
    color: var(--paper);
  }
  #status-chip {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--ink-soft);
    border: 1px solid var(--line);
    padding: 6px 12px;
    border-radius: var(--radius);
    background: var(--panel);
    text-transform: lowercase;
  }
  #status-chip .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--muted);
  }
  #status-chip.running .dot {
    background: var(--teal-bright);
    animation: statusPulse 1.6s ease-in-out infinite;
  }
  #status-chip.stopped .dot { background: var(--amber); }
  #status-chip.offline .dot { background: var(--bad); }
  #msg-status {
    width: 100%;
    font-size: 0.72rem;
    color: var(--muted);
    order: 5;
  }
  #msg-status.ok { color: var(--teal); }
  #msg-status.err { color: var(--bad); }

  @keyframes statusPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
  }

  /* ── Views ── */
  .view {
    display: none;
    opacity: 0;
    transition: opacity 0.35s var(--ease);
  }
  .view.active {
    display: block;
    opacity: 1;
    animation: viewIn 0.4s var(--ease);
  }
  @keyframes viewIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ── Dashboard ── */
  #view-dashboard {
    padding: 28px 20px 48px;
    max-width: 980px;
    margin: 0 auto;
  }
  .dash-hero {
    display: grid;
    gap: 28px;
  }
  .dash-intro .brand {
    font-family: var(--font-display);
    font-size: clamp(2.6rem, 9vw, 4.2rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.05;
    color: var(--ink);
    margin-bottom: 10px;
  }
  .dash-intro .headline {
    font-family: var(--font-display);
    font-size: clamp(1.35rem, 3.5vw, 1.85rem);
    font-weight: 500;
    color: var(--ink-soft);
    margin-bottom: 8px;
  }
  .dash-intro .support {
    font-size: 0.95rem;
    color: var(--muted);
    max-width: 36rem;
    line-height: 1.5;
    margin-bottom: 22px;
  }
  .op-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
  .op-btn {
    font-family: var(--font-ui);
    font-size: 0.9rem;
    font-weight: 600;
    padding: 12px 22px;
    border-radius: var(--radius);
    border: 1.5px solid var(--ink);
    background: var(--ink);
    color: var(--paper);
    cursor: pointer;
    min-width: 6.5rem;
  }
  .op-btn:hover { background: var(--ink-soft); border-color: var(--ink-soft); }
  .op-btn.stop {
    background: transparent;
    color: var(--ink);
  }
  .op-btn.stop:hover { background: rgba(26, 35, 50, 0.06); }
  .op-btn.reset {
    background: transparent;
    color: var(--amber);
    border-color: var(--amber);
  }
  .op-btn.reset:hover { background: rgba(196, 122, 18, 0.08); }

  .process-stage {
    position: relative;
    width: 100%;
    min-height: 280px;
    border: 1px solid var(--line);
    border-radius: 12px;
    background:
      linear-gradient(180deg, rgba(213, 221, 232, 0.35) 0%, rgba(255, 252, 247, 0.5) 100%);
    overflow: hidden;
  }
  #process-svg { width: 100%; height: auto; display: block; min-height: 280px; }

  .tank-fill {
    transition: height 0.55s var(--ease), y 0.55s var(--ease);
  }
  .res-fill {
    transition: height 0.55s var(--ease), y 0.55s var(--ease);
  }
  .speed-fill {
    transition: width 0.45s var(--ease);
  }
  .flow-needle {
    transition: transform 0.45s var(--ease);
    transform-origin: 545px 150px;
  }

  .setpoint-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 28px;
    margin-top: 14px;
    padding: 10px 4px 0;
    border-top: 1px solid var(--line);
    font-size: 0.8rem;
    color: var(--ink-soft);
  }
  .setpoint-row .sp-item { display: inline-flex; gap: 8px; align-items: baseline; }
  .setpoint-row .sp-name {
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .setpoint-row .sp-val { font-variant-numeric: tabular-nums; font-weight: 500; }
  .setpoint-row .q {
    font-size: 0.65rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .setpoint-row .q.GOOD { color: var(--teal); }
  .setpoint-row .q.BAD { color: var(--bad); }
  .setpoint-row .q.UNCERTAIN { color: var(--uncertain); }

  .signal-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 20px;
    margin-top: 18px;
    font-size: 0.78rem;
    color: var(--ink-soft);
  }
  .signal-strip .sig {
    display: inline-flex;
    gap: 7px;
    align-items: baseline;
  }
  .signal-strip .sig-name {
    font-size: 0.65rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .signal-strip .sig-val { font-variant-numeric: tabular-nums; font-weight: 500; }
  .signal-strip .q {
    font-size: 0.62rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .signal-strip .q.GOOD { color: var(--teal); }
  .signal-strip .q.BAD { color: var(--bad); }
  .signal-strip .q.UNCERTAIN { color: var(--uncertain); }

  /* ── Program editor ── */
  #view-program {
    height: calc(100dvh - 58px);
    display: none;
    flex-direction: column;
    overflow: hidden;
  }
  #view-program.active {
    display: flex;
    opacity: 1;
    animation: viewIn 0.4s var(--ease);
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
    #view-dashboard { padding: 20px 16px 40px; }
    .process-stage { min-height: 240px; }
  }
</style>
</head>
<body>

<header id="app-header">
  <div class="mark">PLCAssistant</div>
  <nav class="view-tabs" aria-label="Views">
    <button type="button" id="tab-dashboard" class="active" onclick="showView('dashboard')">Dashboard</button>
    <button type="button" id="tab-program" onclick="showView('program')">Program</button>
  </nav>
  <div id="status-chip" class="offline"><span class="dot" aria-hidden="true"></span><span id="chip-label">offline</span></div>
  <div id="msg-status" class="ok">Ready</div>
</header>

<!-- ═══════════════ Operator Dashboard (default) ═══════════════ -->
<section id="view-dashboard" class="view active" aria-label="Operator dashboard">
  <div class="dash-hero">
    <div class="dash-intro">
      <h1 class="brand">PLCAssistant</h1>
      <p class="headline" id="status-headline">Offline</p>
      <p class="support" id="status-support">Connect to the Soft-PLC runtime to watch tank level, flow, and speed — then start or stop the scan from here.</p>
      <div class="op-controls">
        <button type="button" class="op-btn" onclick="sendCmd('start')">Start</button>
        <button type="button" class="op-btn stop" onclick="sendCmd('stop')">Stop</button>
        <button type="button" class="op-btn reset" onclick="sendCmd('reset')">Reset</button>
      </div>
    </div>

    <div class="process-stage" aria-label="Process visualisation">
      <svg id="process-svg" viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="process-title">
        <title id="process-title">Tank level, reservoir, inlet flow, and command speed</title>
        <defs>
          <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#5aa8a0"/>
            <stop offset="100%" stop-color="#1a7a6d"/>
          </linearGradient>
          <linearGradient id="resGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#8aa4bc"/>
            <stop offset="100%" stop-color="#4a657d"/>
          </linearGradient>
        </defs>

        <!-- Process pipe -->
        <path d="M118 210 H210 M430 210 H500" stroke="#8a96a8" stroke-width="6" fill="none" stroke-linecap="round"/>
        <path d="M210 210 H430" stroke="#8a96a8" stroke-width="4" fill="none" opacity="0.55"/>

        <!-- Reservoir (LT_RES) -->
        <text x="48" y="78" fill="#6b7789" font-size="11" font-family="Sora,sans-serif" letter-spacing="0.08em">RESERVOIR</text>
        <rect x="40" y="88" width="78" height="140" rx="4" fill="#fffcf7" stroke="#a8b4c4" stroke-width="2"/>
        <clipPath id="resClip"><rect x="42" y="90" width="74" height="136" rx="2"/></clipPath>
        <g clip-path="url(#resClip)">
          <rect id="res-fill" class="res-fill" x="42" y="226" width="74" height="0" fill="url(#resGrad)"/>
        </g>
        <text id="res-label" x="79" y="248" text-anchor="middle" fill="#1a2332" font-size="12" font-family="Sora,sans-serif" font-weight="600">—</text>

        <!-- Main tank (LT_TANK) -->
        <text x="248" y="48" fill="#6b7789" font-size="11" font-family="Sora,sans-serif" letter-spacing="0.08em">PROCESS TANK</text>
        <rect x="230" y="58" width="180" height="190" rx="6" fill="#fffcf7" stroke="#a8b4c4" stroke-width="2.5"/>
        <clipPath id="tankClip"><rect x="233" y="61" width="174" height="184" rx="4"/></clipPath>
        <g clip-path="url(#tankClip)">
          <rect id="tank-fill" class="tank-fill" x="233" y="245" width="174" height="0" fill="url(#waterGrad)"/>
        </g>
        <!-- Level marks -->
        <line x1="410" y1="80" x2="418" y2="80" stroke="#8a96a8" stroke-width="1.5"/>
        <line x1="410" y1="152" x2="418" y2="152" stroke="#8a96a8" stroke-width="1.5"/>
        <line x1="410" y1="224" x2="418" y2="224" stroke="#8a96a8" stroke-width="1.5"/>
        <text id="tank-label" x="320" y="268" text-anchor="middle" fill="#1a2332" font-size="14" font-family="Sora,sans-serif" font-weight="600">—</text>

        <!-- Flow gauge (FT_INLET) -->
        <text x="500" y="78" fill="#6b7789" font-size="11" font-family="Sora,sans-serif" letter-spacing="0.08em">INLET FLOW</text>
        <circle cx="545" cy="150" r="48" fill="#fffcf7" stroke="#a8b4c4" stroke-width="2"/>
        <circle cx="545" cy="150" r="40" fill="none" stroke="#d5dde8" stroke-width="6"/>
        <path d="M510 168 A40 40 0 1 1 580 168" fill="none" stroke="#1a7a6d" stroke-width="6" stroke-linecap="round" opacity="0.35"/>
        <g id="flow-needle" class="flow-needle" style="transform: rotate(-90deg)">
          <line x1="545" y1="150" x2="545" y2="118" stroke="#1a2332" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="545" cy="150" r="4" fill="#1a2332"/>
        </g>
        <text id="flow-label" x="545" y="218" text-anchor="middle" fill="#1a2332" font-size="12" font-family="Sora,sans-serif" font-weight="600">—</text>

        <!-- Speed bar (CMD_SPEED) -->
        <text x="230" y="292" fill="#6b7789" font-size="10" font-family="Sora,sans-serif" letter-spacing="0.06em">CMD SPEED</text>
        <rect x="310" y="282" width="200" height="10" rx="2" fill="#e8eef4" stroke="#c5ced9"/>
        <rect id="speed-fill" class="speed-fill" x="310" y="282" width="0" height="10" rx="2" fill="#1a7a6d"/>
        <text id="speed-label" x="520" y="291" fill="#1a2332" font-size="11" font-family="Sora,sans-serif" font-weight="600">—</text>
      </svg>
    </div>

    <div class="setpoint-row" id="setpoint-row" aria-label="Setpoints">
      <div class="sp-item"><span class="sp-name">SP Level</span><span class="sp-val" id="sp-level-val">—</span><span class="q" id="sp-level-q"></span></div>
      <div class="sp-item"><span class="sp-name">SP Flow</span><span class="sp-val" id="sp-flow-val">—</span><span class="q" id="sp-flow-q"></span></div>
    </div>

    <div class="signal-strip" id="signal-strip" aria-label="Live signals"></div>
  </div>
</section>

<!-- ═══════════════ Program editor ═══════════════ -->
<section id="view-program" class="view" aria-label="Program editor">
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
</section>

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
let currentView = 'dashboard';
let runtimePollTimer = null;

const BLOCK_W = 140, BLOCK_H_BASE = 30, PIN_ROW = 16, PIN_R = 5;
const SIGNAL_KEYS = ['LT_TANK', 'LT_RES', 'FT_INLET', 'CMD_SPEED', 'SP_LEVEL', 'SP_LEVEL_REQ', 'SP_FLOW'];

// ── Init ───────────────────────────────────────────────────────────────────
window.onload = () => {
  fetchLibrary();
  fetchProgram();
  pollRuntime();
  runtimePollTimer = setInterval(pollRuntime, 500);
};

function setStatus(msg, ok = true) {
  const el = document.getElementById('msg-status');
  el.textContent = msg;
  el.className = ok ? 'ok' : 'err';
}

function showView(name) {
  currentView = name;
  const dash = document.getElementById('view-dashboard');
  const prog = document.getElementById('view-program');
  const tabD = document.getElementById('tab-dashboard');
  const tabP = document.getElementById('tab-program');
  dash.classList.toggle('active', name === 'dashboard');
  prog.classList.toggle('active', name === 'program');
  tabD.classList.toggle('active', name === 'dashboard');
  tabP.classList.toggle('active', name === 'program');
  if (name === 'program') {
    renderCanvas();
  }
}

function togglePanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('collapsed');
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

// ── Runtime dashboard ──────────────────────────────────────────────────────
async function pollRuntime() {
  try {
    const r = await fetch(apiUrl('api/runtime'));
    if (!r.ok) return;
    const data = await r.json();
    updateDashboard(data);
  } catch (_) { /* quiet poll */ }
}

async function sendCmd(name) {
  try {
    const data = await apiFetch('api/cmd', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name})
    });
    updateDashboard(data);
    setStatus('Command: ' + name, true);
  } catch (_) { /* status already set */ }
}

function tagOf(tags, name) {
  if (!tags) return null;
  return tags[name] || null;
}

function fmtVal(tag, digits) {
  if (!tag || tag.value === null || tag.value === undefined) return '—';
  const n = Number(tag.value);
  if (!Number.isFinite(n)) return String(tag.value);
  const d = digits === undefined ? 2 : digits;
  const unit = tag.unit ? ' ' + tag.unit : '';
  return n.toFixed(d) + unit;
}

function qualityClass(tag) {
  const s = (tag && tag.status) ? String(tag.status).toUpperCase() : '';
  return s || '';
}

function updateDashboard(data) {
  const status = String((data && data.status) || 'offline').toLowerCase();
  const chip = document.getElementById('status-chip');
  chip.className = status;
  document.getElementById('chip-label').textContent = status;

  const headline = document.getElementById('status-headline');
  const support = document.getElementById('status-support');
  if (status === 'running') {
    headline.textContent = 'Running';
    support.textContent = 'Scan loop is active. Watch levels and flow update live, or stop the Soft-PLC when the process should idle.';
  } else if (status === 'stopped') {
    headline.textContent = 'Stopped';
    support.textContent = 'Runtime is reachable but not scanning. Start to resume control, or open Program to edit the block graph.';
  } else {
    headline.textContent = 'Offline';
    support.textContent = 'No live MQTT scan yet — local fallback image is shown. Start attempts a scan; signals update when the runtime connects.';
  }

  const tags = (data && data.tags) || {};
  const tank = tagOf(tags, 'LT_TANK');
  const res = tagOf(tags, 'LT_RES');
  const flow = tagOf(tags, 'FT_INLET');
  const speed = tagOf(tags, 'CMD_SPEED');
  const spLevel = tagOf(tags, 'SP_LEVEL') || tagOf(tags, 'SP_LEVEL_REQ');
  const spFlow = tagOf(tags, 'SP_FLOW');

  // Tank fill: assume ~0–1 m typical; clamp visually 0–100% of tank height
  const tankH = 184, tankBottom = 61 + tankH;
  const tankFrac = clamp01(numOr(tank, 0) / Math.max(numOr(spLevel, 1), 0.01));
  const tankFillH = tankFrac * tankH;
  const tankEl = document.getElementById('tank-fill');
  tankEl.setAttribute('height', tankFillH);
  tankEl.setAttribute('y', tankBottom - tankFillH);
  document.getElementById('tank-label').textContent = fmtVal(tank, 2);

  const resH = 136, resBottom = 90 + resH;
  const resFrac = clamp01(numOr(res, 0) / 1.0);
  const resFillH = resFrac * resH;
  const resEl = document.getElementById('res-fill');
  resEl.setAttribute('height', resFillH);
  resEl.setAttribute('y', resBottom - resFillH);
  document.getElementById('res-label').textContent = fmtVal(res, 2);

  // Flow needle: map 0–100 L/min-ish to -90..+90 deg
  const flowN = numOr(flow, 0);
  const flowAngle = -90 + clamp01(flowN / 100) * 180;
  const needle = document.getElementById('flow-needle');
  needle.style.transform = 'rotate(' + flowAngle + 'deg)';
  document.getElementById('flow-label').textContent = fmtVal(flow, 1);

  const spd = clamp01(numOr(speed, 0) / 100);
  document.getElementById('speed-fill').setAttribute('width', spd * 200);
  document.getElementById('speed-label').textContent = fmtVal(speed, 1);

  document.getElementById('sp-level-val').textContent = fmtVal(spLevel, 2);
  const spLQ = document.getElementById('sp-level-q');
  spLQ.textContent = qualityClass(spLevel);
  spLQ.className = 'q ' + qualityClass(spLevel);

  document.getElementById('sp-flow-val').textContent = fmtVal(spFlow, 1);
  const spFQ = document.getElementById('sp-flow-q');
  spFQ.textContent = qualityClass(spFlow);
  spFQ.className = 'q ' + qualityClass(spFlow);

  const strip = document.getElementById('signal-strip');
  const seen = new Set();
  const order = [];
  for (const k of SIGNAL_KEYS) {
    if (tags[k] && !seen.has(k)) { order.push(k); seen.add(k); }
  }
  // Prefer SP_LEVEL over SP_LEVEL_REQ in strip if both present
  if (seen.has('SP_LEVEL') && seen.has('SP_LEVEL_REQ')) {
    const i = order.indexOf('SP_LEVEL_REQ');
    if (i >= 0) order.splice(i, 1);
  }
  strip.innerHTML = order.map(k => {
    const t = tags[k];
    const q = qualityClass(t);
    return `<div class="sig"><span class="sig-name">${esc(k)}</span>` +
      `<span class="sig-val">${esc(fmtVal(t, 2))}</span>` +
      `<span class="q ${esc(q)}">${esc(q)}</span></div>`;
  }).join('');
}

function numOr(tag, fallback) {
  if (!tag || tag.value === null || tag.value === undefined) return fallback;
  const n = Number(tag.value);
  return Number.isFinite(n) ? n : fallback;
}
function clamp01(x) { return Math.max(0, Math.min(1, x)); }

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
  if (!wl || !bl) return;
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
  if (currentView !== 'program') showView('program');
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
