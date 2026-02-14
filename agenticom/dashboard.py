"""
Agenticom Web Dashboard - Beautiful UI for non-technical users
Run with: agenticom dashboard
"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser

# Import core functions
try:
    from agenticom.state import StateManager
    from agenticom.core import AgenticomCore
except ImportError:
    from .state import StateManager
    from .core import AgenticomCore


DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agenticom Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #FFFBF5;
  --bg-card: #fff;
  --bg-header: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  --text: #3D3229;
  --text-muted: #8B7355;
  --border: #E8DDD0;
  --accent: #D4A574;
  --accent-dark: #B8956A;
  --success: #6B8E4E;
  --success-bg: rgba(107,142,78,0.1);
  --warning: #E8845C;
  --warning-bg: rgba(232,132,92,0.1);
  --info: #5B8FA8;
  --info-bg: rgba(91,143,168,0.1);
  --shadow: 0 2px 8px rgba(61,50,41,0.08);
  --shadow-lg: 0 8px 24px rgba(61,50,41,0.12);
}

[data-theme="dark"] {
  --bg: #1C1917;
  --bg-card: #262220;
  --bg-header: linear-gradient(135deg, #8B6B4A 0%, #6B5A3E 100%);
  --text: #F5EDE5;
  --text-muted: #A89B8C;
  --border: #3D3632;
  --accent: #D4A574;
  --accent-dark: #E8B584;
  --success: #8FAF6E;
  --success-bg: rgba(143,175,110,0.15);
  --warning: #E8955F;
  --warning-bg: rgba(232,149,95,0.15);
  --info: #7AAFCA;
  --info-bg: rgba(122,175,202,0.15);
  --shadow: 0 2px 8px rgba(0,0,0,0.2);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.3);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

/* Header */
header {
  background: var(--bg-header);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}
.logo { display: flex; align-items: center; gap: 12px; }
.logo h1 { font-size: 24px; font-weight: 700; color: #fff; letter-spacing: -0.5px; }
.logo span { font-weight: 400; opacity: 0.8; }
.header-actions { display: flex; align-items: center; gap: 12px; }
select, button {
  background: rgba(255,255,255,0.2);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
select:hover, button:hover { background: rgba(255,255,255,0.3); }
select option { background: var(--bg-card); color: var(--text); }
.theme-btn { padding: 8px 12px; font-size: 16px; }

/* Stats */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow);
}
.stat-label { font-size: 12px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; color: var(--text); }
.stat-value.success { color: var(--success); }
.stat-value.warning { color: var(--warning); }

/* New Run Input */
.new-run {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px 24px;
}
.new-run-form {
  display: flex;
  gap: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  box-shadow: var(--shadow);
}
.new-run-form input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  color: var(--text);
}
.new-run-form input:focus { outline: none; border-color: var(--accent); }
.new-run-form input::placeholder { color: var(--text-muted); }
.new-run-form select {
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  min-width: 160px;
}
.new-run-form button {
  background: var(--accent);
  color: #fff;
  border: none;
  font-weight: 600;
  padding: 12px 24px;
}
.new-run-form button:hover { background: var(--accent-dark); }

/* Board */
.board {
  display: flex;
  gap: 16px;
  padding: 0 24px 24px;
  overflow-x: auto;
  max-width: 1400px;
  margin: 0 auto;
}
.column {
  min-width: 260px;
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 380px);
}
.column-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.column-title {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent-dark);
}
.column-count {
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.cards {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Cards */
.card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.card:hover { border-color: var(--accent); box-shadow: var(--shadow); }
.card.done { border-left: 3px solid var(--success); }
.card.running { border-left: 3px solid var(--info); }
.card.failed { border-left: 3px solid var(--warning); }
.card-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
}
.badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}
.badge-done, .badge-completed { background: var(--success-bg); color: var(--success); }
.badge-running { background: var(--info-bg); color: var(--info); }
.badge-pending { background: var(--border); color: var(--text-muted); }
.badge-failed { background: var(--warning-bg); color: var(--warning); }

/* Card Actions */
.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.card-actions button {
  flex: 1;
  background: var(--bg-card);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 500;
}
.card-actions button:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

/* Expanded Card */
.card-expanded {
  background: var(--bg-card);
  border: 2px solid var(--accent);
  box-shadow: var(--shadow-lg);
}
.card-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.step-list { display: flex; flex-direction: column; gap: 6px; }
.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--bg);
  border-radius: 6px;
  font-size: 12px;
}
.step-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
}
.step-icon.done { background: var(--success-bg); color: var(--success); }
.step-icon.running { background: var(--info-bg); color: var(--info); }
.step-icon.pending { background: var(--border); color: var(--text-muted); }
.step-icon.failed { background: var(--warning-bg); color: var(--warning); }
.step-name { flex: 1; font-weight: 500; color: var(--text); }
.step-agent { color: var(--text-muted); font-size: 11px; }

/* Empty state */
.empty { color: var(--text-muted); font-size: 13px; text-align: center; padding: 24px; }

/* Responsive */
@media (max-width: 768px) {
  .board { flex-direction: column; }
  .column { min-width: unset; max-height: none; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .new-run-form { flex-direction: column; }
  .new-run-form select { min-width: unset; }
}
</style>
</head>
<body>
<header>
  <div class="logo">
    <h1>🤖 Agenticom <span>Dashboard</span></h1>
  </div>
  <div class="header-actions">
    <select id="workflow-select"><option value="">Loading...</option></select>
    <button class="theme-btn" id="theme-toggle" title="Toggle theme">☀️</button>
  </div>
</header>

<div class="stats" id="stats">
  <div class="stat-card">
    <div class="stat-label">Total Runs</div>
    <div class="stat-value" id="stat-total">-</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Success Rate</div>
    <div class="stat-value success" id="stat-success">-</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Running Now</div>
    <div class="stat-value" id="stat-running">-</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Failed</div>
    <div class="stat-value warning" id="stat-failed">-</div>
  </div>
</div>

<div class="new-run">
  <form class="new-run-form" id="new-run-form">
    <input type="text" id="task-input" placeholder="Describe your task... e.g., 'Create a marketing strategy for my SaaS product'" required>
    <select id="run-workflow-select"><option value="feature-dev">feature-dev</option><option value="marketing-campaign">marketing-campaign</option></select>
    <button type="submit">▶ Start Run</button>
  </form>
</div>

<div class="board" id="board">
  <div class="empty" style="margin:auto;padding:48px">Select a workflow to view runs</div>
</div>

<script>
let workflows = [];
let runs = [];
let currentWf = null;
let expandedCard = null;

async function api(endpoint) {
  try {
    console.log('Fetching:', '/api' + endpoint);
    const r = await fetch('/api' + endpoint);
    if (!r.ok) {
      console.error('API error:', r.status, r.statusText);
      return null;
    }
    const data = await r.json();
    console.log('API response:', endpoint, data);
    return data;
  } catch (err) {
    console.error('API fetch error:', err);
    return null;
  }
}

async function apiPost(endpoint, data) {
  const r = await fetch('/api' + endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return r.json();
}

async function loadWorkflows() {
  console.log('Loading workflows...');
  workflows = await api('/workflows');
  console.log('Workflows loaded:', workflows);

  if (!workflows || !Array.isArray(workflows)) {
    console.error('Failed to load workflows');
    return;
  }

  const sel = document.getElementById('workflow-select');
  const runSel = document.getElementById('run-workflow-select');

  sel.innerHTML = '<option value="">— All Workflows —</option>' +
    workflows.map(w => `<option value="${w.id}">${w.name}</option>`).join('');

  runSel.innerHTML = workflows.map(w => `<option value="${w.id}">${w.id}</option>`).join('');

  // Load all runs initially
  loadRuns();
}

async function loadRuns() {
  const wfId = document.getElementById('workflow-select').value;
  const url = wfId ? `/runs?workflow=${wfId}` : '/runs';
  runs = await api(url);

  currentWf = wfId ? workflows.find(w => w.id === wfId) : null;

  updateStats();
  renderBoard();
}

function updateStats() {
  const total = runs.length;
  const done = runs.filter(r => r.status === 'done' || r.status === 'completed').length;
  const running = runs.filter(r => r.status === 'running').length;
  const failed = runs.filter(r => r.status === 'failed' || r.status === 'error').length;
  const rate = total > 0 ? Math.round((done / total) * 100) : 0;

  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-success').textContent = rate + '%';
  document.getElementById('stat-running').textContent = running;
  document.getElementById('stat-failed').textContent = failed;
}

function getSteps() {
  if (currentWf && currentWf.steps) return currentWf.steps;
  // Default steps for feature-dev
  return [
    { id: 'plan', name: 'Plan' },
    { id: 'implement', name: 'Implement' },
    { id: 'verify', name: 'Verify' },
    { id: 'test', name: 'Test' },
    { id: 'review', name: 'Review' }
  ];
}

function getActiveStep(run) {
  if (!run.steps || !run.steps.length) return 'plan';
  const active = run.steps.find(s => s.status !== 'done' && s.status !== 'skipped');
  return active ? active.step_id : run.steps[run.steps.length - 1].step_id;
}

function renderBoard() {
  const board = document.getElementById('board');
  const steps = getSteps();

  // Group runs by their active step
  const columns = {};
  steps.forEach(s => { columns[s.id] = []; });

  runs.forEach(run => {
    const stepId = getActiveStep(run);
    if (columns[stepId]) {
      columns[stepId].push(run);
    } else {
      columns[steps[steps.length - 1].id].push(run);
    }
  });

  board.innerHTML = steps.map(step => {
    const cards = columns[step.id] || [];
    const cardHTML = cards.length === 0
      ? '<div class="empty">No runs</div>'
      : cards.map(run => renderCard(run)).join('');

    return `<div class="column">
      <div class="column-header">
        <span class="column-title">${step.id}</span>
        <span class="column-count">${cards.length}</span>
      </div>
      <div class="cards">${cardHTML}</div>
    </div>`;
  }).join('');
}

function renderCard(run) {
  const status = run.status || 'pending';
  const title = run.task.length > 80 ? run.task.slice(0, 77) + '...' : run.task;
  const time = run.updated_at ? new Date(run.updated_at).toLocaleDateString() : '';
  const isExpanded = expandedCard === run.id;
  const artifactCount = run.artifact_count || 0;

  console.log('renderCard:', run.id, 'expanded:', isExpanded, 'has steps:', !!run.steps, 'step count:', run.steps && run.steps.length, 'artifacts:', artifactCount);

  let detailsHTML = '';
  if (isExpanded && run.steps) {
    const icons = { done: '✓', completed: '✓', running: '●', pending: '○', failed: '✗' };
    const stepsHTML = run.steps.map(s => {
      const icon = icons[s.status] || '○';
      const output = s.output || '';
      const previewText = output.length > 150 ? output.substring(0, 150) + '...' : output;
      const escapedPreview = previewText.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      const escapedError = s.error ? s.error.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;') : '';

      let html = '<div class="step-item" style="flex-direction: column; align-items: flex-start;">';
      html += '<div style="display: flex; align-items: center; gap: 10px; width: 100%;">';
      html += '<div class="step-icon ' + s.status + '">' + icon + '</div>';
      html += '<span class="step-name">' + s.step_id + '</span>';
      html += '<span class="step-agent">' + (s.agent || '') + '</span>';
      html += '<span class="badge badge-' + s.status + '">' + s.status + '</span>';
      html += '</div>';
      if (escapedPreview) {
        html += '<div style="margin-left: 30px; margin-top: 8px; font-size: 11px; color: var(--text-muted); font-family: monospace; background: var(--bg); padding: 8px; border-radius: 4px; max-width: 100%; overflow: hidden; white-space: pre-wrap;">' + escapedPreview + '</div>';
      }
      if (escapedError) {
        html += '<div style="color: var(--warning); font-size: 11px; margin-top: 4px;">⚠️ ' + escapedError + '</div>';
      }
      html += '</div>';
      return html;
    }).join('');

    // Artifacts section
    let artifactsHTML = '';
    if (run.artifacts && run.artifacts.length > 0) {
      artifactsHTML = `
        <div style="margin-top: 16px; padding: 12px; background: var(--bg); border-radius: 6px; border: 1px solid var(--border);">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-weight: 600; color: var(--text);">📦 Generated Files (${run.artifacts.length})</span>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            ${run.artifacts.map(f => `<span style="font-size: 11px; padding: 4px 8px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 4px; font-family: monospace;">${f}</span>`).join('')}
          </div>
        </div>
      `;
    }

    detailsHTML = `
      <div class="card-details">
        <div class="step-list">${stepsHTML}</div>
        ${artifactsHTML}
        <div class="card-actions">
          ${status === 'failed' ? `<button onclick="resumeRun('${run.id}'); event.stopPropagation();">↺ Resume</button>` : ''}
          <button onclick="viewLogs('${run.id}'); event.stopPropagation();">📋 View Full Logs</button>
          ${run.artifacts && run.artifacts.length > 0 ? `<button onclick="viewArtifacts('${run.id}'); event.stopPropagation();">📂 View Code</button>` : ''}
        </div>
      </div>
    `;
  }

  return `<div class="card ${status} ${isExpanded ? 'card-expanded' : ''}" onclick="toggleCard('${run.id}')">
    <div class="card-title" title="${run.task.replace(/"/g, '&quot;')}">${title}</div>
    <div class="card-meta">
      <span class="badge badge-${status}">${status}</span>
      <span>${time}</span>
      ${artifactCount > 0 ? `<span style="font-size: 11px; color: var(--text-muted);">📦 ${artifactCount} files</span>` : ''}
    </div>
    ${detailsHTML}
  </div>`;
}

async function toggleCard(runId) {
  console.log('toggleCard called:', runId);
  if (expandedCard === runId) {
    console.log('Collapsing card');
    expandedCard = null;
  } else {
    console.log('Expanding card, fetching details...');
    // Fetch full run details
    const run = await api(`/runs/${runId}`);
    console.log('Run details:', run);
    console.log('Run has steps:', run && run.steps, 'count:', run && run.steps && run.steps.length);
    const idx = runs.findIndex(r => r.id === runId);
    if (idx >= 0) {
      console.log('Updating run in array at index:', idx);
      runs[idx] = run;
    }
    expandedCard = runId;
  }
  console.log('Rendering board...');
  renderBoard();
}

async function resumeRun(runId) {
  await apiPost(`/runs/${runId}/resume`, {});
  loadRuns();
}

async function viewLogs(runId) {
  const run = await api(`/runs/${runId}`);
  if (!run || !run.steps) {
    alert('No logs available for this run');
    return;
  }

  // Create logs modal
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
  `;

  const content = document.createElement('div');
  content.style.cssText = `
    background: var(--bg-card);
    border-radius: 12px;
    max-width: 900px;
    max-height: 80vh;
    overflow-y: auto;
    padding: 24px;
    box-shadow: var(--shadow-lg);
  `;

  let logsHtml = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="color: var(--text); margin: 0;">Workflow Logs</h2>
      <button onclick="this.closest('[style*=fixed]').remove()" style="
        background: transparent;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: var(--text);
      ">&times;</button>
    </div>
    <div style="color: var(--text-muted); margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border);">
      <strong>Task:</strong> ${run.task}<br>
      <strong>Status:</strong> <span class="badge badge-${run.status}">${run.status}</span><br>
      <strong>Steps:</strong> ${run.current_step}/${run.total_steps}
    </div>
  `;

  run.steps.forEach((step, idx) => {
    const statusColor = {
      'completed': 'var(--success)',
      'failed': 'var(--warning)',
      'running': 'var(--info)',
      'pending': 'var(--text-muted)'
    }[step.status] || 'var(--text-muted)';

    const output = step.output || 'No output';
    const outputPreview = output.length > 500 ? output.substring(0, 500) + '... (truncated)' : output;
    const escapedOutput = outputPreview.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const escapedError = step.error ? step.error.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';

    logsHtml += '<div style="margin-bottom: 20px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;">';
    logsHtml += '<div style="background: var(--bg); padding: 12px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">';
    logsHtml += '<div><strong style="color: ' + statusColor + ';">Step ' + (idx + 1) + ': ' + step.step_id + '</strong>';
    logsHtml += '<span style="color: var(--text-muted); margin-left: 12px;">Agent: ' + step.agent + '</span></div>';
    logsHtml += '<span class="badge badge-' + step.status + '">' + step.status + '</span>';
    logsHtml += '</div>';
    logsHtml += '<div style="padding: 16px;">';
    logsHtml += '<pre style="background: var(--bg); padding: 12px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; font-size: 12px; line-height: 1.5; color: var(--text); margin: 0; max-height: 300px; overflow-y: auto;">' + escapedOutput + '</pre>';
    if (escapedError) {
      logsHtml += '<div style="background: var(--warning-bg); border-left: 3px solid var(--warning); padding: 12px; margin-top: 12px; border-radius: 4px; color: var(--warning);"><strong>Error:</strong> ' + escapedError + '</div>';
    }
    logsHtml += '</div></div>';
  });

  content.innerHTML = logsHtml;
  modal.appendChild(content);
  document.body.appendChild(modal);

  // Close on background click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

async function viewArtifacts(runId) {
  const artifactsData = await api(`/runs/${runId}/artifacts`);

  if (!artifactsData || !artifactsData.artifacts || artifactsData.artifacts.length === 0) {
    alert('No artifacts available for this run');
    return;
  }

  // Create artifacts modal
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
  `;

  const content = document.createElement('div');
  content.style.cssText = `
    background: var(--bg-card);
    border-radius: 12px;
    max-width: 900px;
    max-height: 80vh;
    overflow-y: auto;
    padding: 24px;
    box-shadow: var(--shadow-lg);
  `;

  let artifactsHtml = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="color: var(--text); margin: 0;">Generated Code</h2>
      <button onclick="this.closest('[style*=fixed]').remove()" style="
        background: transparent;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: var(--text);
      ">&times;</button>
    </div>
    <div style="color: var(--text-muted); margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border);">
      <strong>Run ID:</strong> ${runId}<br>
      <strong>Files:</strong> ${artifactsData.count}<br>
      <strong>Location:</strong> <code style="font-size: 11px; background: var(--bg); padding: 2px 6px; border-radius: 3px;">${artifactsData.output_dir}</code>
    </div>
  `;

  // Add file list and copy instructions
  artifactsHtml += `
    <div style="margin-bottom: 20px;">
      <h3 style="color: var(--text); margin: 0 0 12px 0;">Files Generated:</h3>
      <div style="display: grid; gap: 8px;">
  `;

  artifactsData.artifacts.forEach((filename) => {
    artifactsHtml += `
      <div style="display: flex; align-items: center; gap: 8px; padding: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px;">
        <span style="font-family: monospace; font-size: 13px; color: var(--text);">${filename}</span>
      </div>
    `;
  });

  artifactsHtml += `
      </div>
    </div>
    <div style="background: var(--info-bg); border-left: 3px solid var(--info); padding: 12px; border-radius: 4px; margin-top: 16px;">
      <strong style="color: var(--info);">💡 How to use the code:</strong><br>
      <code style="font-size: 12px; background: var(--bg); padding: 2px 6px; border-radius: 3px; margin-top: 8px; display: inline-block;">
        cp -r ${artifactsData.output_dir}/* ./my-project/
      </code>
    </div>
  `;

  content.innerHTML = artifactsHtml;
  modal.appendChild(content);
  document.body.appendChild(modal);

  // Close on background click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// New run form
document.getElementById('new-run-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const task = document.getElementById('task-input').value;
  const workflow = document.getElementById('run-workflow-select').value;

  if (!task.trim()) return;

  const result = await apiPost('/runs', { workflow, task });
  if (result.run_id) {
    document.getElementById('task-input').value = '';
    document.getElementById('workflow-select').value = workflow;
    loadRuns();
  }
});

// Workflow selector
document.getElementById('workflow-select').addEventListener('change', loadRuns);

// Theme toggle
(function initTheme() {
  const btn = document.getElementById('theme-toggle');
  const root = document.documentElement;

  function getTheme() {
    return localStorage.getItem('agenticom-theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    btn.textContent = theme === 'dark' ? '🌙' : '☀️';
  }

  applyTheme(getTheme());

  btn.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem('agenticom-theme', next);
    applyTheme(next);
  });
})();

// Initial load
loadWorkflows();

// Auto-refresh every 10 seconds
setInterval(loadRuns, 10000);
</script>
</body>
</html>
'''


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the Agenticom dashboard"""

    def __init__(self, *args, state=None, core=None, **kwargs):
        self.state = state
        self.core = core
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Suppress request logs
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())

        elif path == '/api/workflows':
            workflows = self.core.list_workflows()
            self.send_json(workflows)

        elif path == '/api/runs':
            query = parse_qs(parsed.query)
            workflow_id = query.get('workflow', [None])[0]
            runs = self.state.list_runs(workflow_id=workflow_id)
            self.send_json([r.to_dict() for r in runs])

        elif path.startswith('/api/runs/') and path.endswith('/artifacts'):
            # Get artifacts for a run
            run_id = path.split('/')[-2]
            from orchestration.artifact_manager import ArtifactManager
            from pathlib import Path

            artifact_manager = ArtifactManager()
            artifacts = artifact_manager.list_artifacts(run_id)

            if artifacts:
                self.send_json({
                    'run_id': run_id,
                    'artifacts': artifacts,
                    'count': len(artifacts),
                    'output_dir': str(artifact_manager.get_run_dir(run_id))
                })
            else:
                self.send_json({
                    'run_id': run_id,
                    'artifacts': [],
                    'count': 0
                })

        elif path.startswith('/api/runs/') and not path.endswith('/resume'):
            run_id = path.split('/')[-1]
            run = self.state.get_run(run_id)
            if run:
                # Get step results and include them
                steps = self.state.get_step_results(run_id)
                run_dict = run.to_dict()
                run_dict['steps'] = [s.to_dict() for s in steps]

                # Add artifact information
                from orchestration.artifact_manager import ArtifactManager
                artifact_manager = ArtifactManager()
                artifacts = artifact_manager.list_artifacts(run_id)
                run_dict['artifacts'] = artifacts
                run_dict['artifact_count'] = len(artifacts)

                self.send_json(run_dict)
            else:
                self.send_error(404, 'Run not found')

        else:
            self.send_error(404, 'Not found')

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'

        try:
            data = json.loads(body)
        except:
            data = {}

        if path == '/api/runs':
            workflow = data.get('workflow', 'feature-dev')
            task = data.get('task', '')

            if not task:
                self.send_json({'error': 'Task required'}, status=400)
                return

            result = self.core.run_workflow(workflow, task)
            self.send_json(result)

        elif path.endswith('/resume'):
            run_id = path.split('/')[-2]
            result = self.core.resume_run(run_id)
            self.send_json(result)

        else:
            self.send_error(404, 'Not found')

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def create_handler(state, core):
    """Create handler class with state and core injected"""
    class Handler(DashboardHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, state=state, core=core, **kwargs)
    return Handler


def start_dashboard(port=8080, open_browser=True):
    """Start the dashboard server"""
    state = StateManager()
    core = AgenticomCore()

    handler = create_handler(state, core)
    server = HTTPServer(('localhost', port), handler)

    print(f"🚀 Agenticom Dashboard running at http://localhost:{port}")
    print("   Press Ctrl+C to stop")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
        server.shutdown()


if __name__ == '__main__':
    start_dashboard()
