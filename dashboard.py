#!/usr/bin/env python3
"""
Dashboard web de monitoring du bot de trading.

Démarre un serveur web local sur http://localhost:5000

Usage :
    python dashboard.py
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

BASE_DIR  = Path(__file__).parent
LOG_FILE  = BASE_DIR / "trades_log.csv"
BOT_PID   = BASE_DIR / "bot.pid"

# ---------------------------------------------------------------------------
# HTML + JS (tout en un seul fichier, pas de dépendance externe)
# ---------------------------------------------------------------------------
_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trading Bot — Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; }
  header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d;
           display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 1.2rem; font-weight: 600; }
  .badge { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
  .badge.on  { background: #1a4731; color: #3fb950; }
  .badge.off { background: #3d1f1f; color: #f85149; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 16px; padding: 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
  .card .label { font-size: 0.75rem; color: #8b949e; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .5px; }
  .card .value { font-size: 1.6rem; font-weight: 700; }
  .card .value.green { color: #3fb950; }
  .card .value.red   { color: #f85149; }
  .card .value.blue  { color: #58a6ff; }
  .card .value.yellow{ color: #d29922; }
  .section { padding: 0 24px 24px; }
  .section h2 { font-size: 0.9rem; color: #8b949e; text-transform: uppercase;
                letter-spacing: .5px; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { text-align: left; padding: 8px 12px; background: #161b22;
       border-bottom: 1px solid #30363d; color: #8b949e; font-weight: 500; }
  td { padding: 8px 12px; border-bottom: 1px solid #21262d; }
  tr:hover td { background: #161b22; }
  .buy  { color: #3fb950; font-weight: 600; }
  .sell { color: #f85149; font-weight: 600; }
  .exec { color: #58a6ff; }
  .alert { color: #8b949e; }
  canvas { width: 100%; height: 200px; }
  .chart-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
               padding: 20px; margin: 0 24px 24px; }
  .fr-table td, .fr-table th { padding: 6px 12px; }
  .neutral { color: #8b949e; }
  .bullish { color: #3fb950; }
  .bearish { color: #f85149; }
  footer { text-align: center; padding: 16px; color: #484f58; font-size: 0.75rem; }
</style>
</head>
<body>
<header>
  <h1>🤖 Trading Bot</h1>
  <span id="bot-status" class="badge off">Vérification...</span>
  <span style="margin-left:auto; font-size:0.8rem; color:#8b949e" id="last-update"></span>
</header>

<!-- KPIs -->
<div class="grid" id="kpis">
  <div class="card"><div class="label">Signaux total</div><div class="value blue" id="total">—</div></div>
  <div class="card"><div class="label">Exécutés (Alpaca)</div><div class="value" id="executed">—</div></div>
  <div class="card"><div class="label">Alertes Telegram</div><div class="value" id="alerts">—</div></div>
  <div class="card"><div class="label">Objectif validation</div><div class="value yellow" id="progress">—</div></div>
  <div class="card"><div class="label">Actif le + actif</div><div class="value" id="top-sym">—</div></div>
</div>

<!-- Courbe signaux -->
<div class="chart-box">
  <h2 style="margin-bottom:12px">Signaux cumulés dans le temps</h2>
  <canvas id="chart"></canvas>
</div>

<!-- Funding Rates -->
<div class="section">
  <h2>💹 Funding Rates (live)</h2>
  <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden">
    <table class="fr-table">
      <thead><tr><th>Symbole</th><th>Funding Rate</th><th>Biais</th></tr></thead>
      <tbody id="fr-body"><tr><td colspan="3" style="color:#8b949e">Chargement...</td></tr></tbody>
    </table>
  </div>
</div>

<!-- Derniers signaux -->
<div class="section" style="margin-top:16px">
  <h2>Derniers signaux</h2>
  <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden">
    <table>
      <thead>
        <tr><th>Date</th><th>Symbole</th><th>TF</th><th>Stratégie</th>
            <th>Direction</th><th>Entrée</th><th>TP</th><th>Mode</th></tr>
      </thead>
      <tbody id="trades-body">
        <tr><td colspan="8" style="color:#8b949e">Aucun signal enregistré.</td></tr>
      </tbody>
    </table>
  </div>
</div>

<footer>Actualisation automatique toutes les 60s · Données paper trading uniquement</footer>

<script>
async function refresh() {
  const r = await fetch('/api/data');
  const d = await r.json();

  // Status bot
  const el = document.getElementById('bot-status');
  el.textContent = d.bot_running ? '● Bot actif' : '● Bot arrêté';
  el.className = 'badge ' + (d.bot_running ? 'on' : 'off');

  document.getElementById('last-update').textContent =
    'Mis à jour : ' + new Date().toLocaleTimeString('fr-FR');

  // KPIs
  document.getElementById('total').textContent    = d.total;
  document.getElementById('executed').textContent = d.executed;
  document.getElementById('alerts').textContent   = d.alerts;
  document.getElementById('progress').textContent =
    d.total + ' / 30 (' + Math.round(d.total/30*100) + '%)';
  document.getElementById('top-sym').textContent  = d.top_sym || '—';

  // Tableau trades
  const tbody = document.getElementById('trades-body');
  if (d.trades.length === 0) return;
  tbody.innerHTML = d.trades.slice(-20).reverse().map(t => `
    <tr>
      <td style="color:#8b949e">${t.timestamp}</td>
      <td><b>${t.symbol}</b></td>
      <td style="color:#8b949e">${t.interval}</td>
      <td style="color:#8b949e">${t.strategy}</td>
      <td class="${t.direction.toLowerCase()}">${t.direction}</td>
      <td>${parseFloat(t.entry).toFixed(4)}</td>
      <td>${parseFloat(t.tp).toFixed(4)}</td>
      <td class="${t.executed==='1'?'exec':'alert'}">${t.executed==='1'?'✅ Auto':'📱 Alerte'}</td>
    </tr>`).join('');

  // Courbe cumulée
  const labels = d.trades.map((_, i) => i + 1);
  drawChart(labels);

  // Funding rates
  const frBody = document.getElementById('fr-body');
  frBody.innerHTML = d.funding.map(f => `
    <tr>
      <td><b>${f.symbol}</b></td>
      <td class="${f.cls}">${f.rate}</td>
      <td class="${f.cls}">${f.biais}</td>
    </tr>`).join('') || '<tr><td colspan="3" style="color:#8b949e">N/A</td></tr>';
}

function drawChart(labels) {
  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth * window.devicePixelRatio || 800;
  canvas.height = 200 * (window.devicePixelRatio || 1);
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
  const w = canvas.offsetWidth, h = 200;
  ctx.clearRect(0, 0, w, h);
  if (labels.length < 2) return;
  const step = w / (labels.length - 1);
  ctx.beginPath();
  ctx.strokeStyle = '#58a6ff';
  ctx.lineWidth = 2;
  labels.forEach((v, i) => {
    const x = i * step;
    const y = h - (v / labels[labels.length-1]) * (h - 20) - 10;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
  // Fill
  ctx.lineTo((labels.length-1)*step, h);
  ctx.lineTo(0, h);
  ctx.closePath();
  ctx.fillStyle = 'rgba(88,166,255,0.08)';
  ctx.fill();
}

refresh();
setInterval(refresh, 60000);
</script>
</body>
</html>
"""


def _load_trades() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE) as f:
        return list(csv.DictReader(f))


def _bot_running() -> bool:
    if not BOT_PID.exists():
        return False
    try:
        pid = int(BOT_PID.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _funding_data() -> list[dict]:
    from scalping.market_regime import get_funding_rate, FR_HIGH, FR_LOW, FR_EXTREME_HIGH, FR_EXTREME_LOW
    symbols = ["BTCUSDT", "SOLUSDT", "LINKUSDT", "AAVEUSDT",
               "ARBUSDT", "INJUSDT", "OPUSDT", "SUIUSDT"]
    rows = []
    for sym in symbols:
        fr = get_funding_rate(sym)
        if fr is None:
            continue
        fr_pct = fr * 100
        if fr >= FR_EXTREME_HIGH:
            cls, biais = "bearish", "🔴 Très long → SELL favorisé"
        elif fr >= FR_HIGH:
            cls, biais = "bearish", "🟠 Long → prudence BUY"
        elif fr <= FR_EXTREME_LOW:
            cls, biais = "bullish", "🟢 Très short → BUY favorisé"
        elif fr <= FR_LOW:
            cls, biais = "bullish", "🟡 Short → prudence SELL"
        else:
            cls, biais = "neutral", "⚪ Neutre"
        rows.append({"symbol": sym[:-4], "rate": f"{fr_pct:+.4f}%", "biais": biais, "cls": cls})
    return rows


@app.route("/")
def index():
    return render_template_string(_HTML)


@app.route("/api/data")
def api_data():
    trades  = _load_trades()
    total   = len(trades)
    executed = sum(1 for t in trades if t.get("executed") == "1")
    alerts   = total - executed

    by_sym: dict[str, int] = {}
    for t in trades:
        s = t["symbol"]
        by_sym[s] = by_sym.get(s, 0) + 1
    top_sym = max(by_sym, key=by_sym.get) if by_sym else ""

    return jsonify({
        "bot_running": _bot_running(),
        "total":       total,
        "executed":    executed,
        "alerts":      alerts,
        "top_sym":     top_sym,
        "trades":      trades,
        "funding":     _funding_data(),
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    print("🌐 Dashboard disponible sur http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
