#!/usr/bin/env bash
# =====================================================================
# Installation "clé en main" du bot de scalping.
#   ./setup.sh
# Crée un environnement virtuel, installe les dépendances, prépare .env.
# =====================================================================
set -e

PY=${PYTHON:-python3}

echo "🔧 Création de l'environnement virtuel (.venv)..."
$PY -m venv .venv

echo "📦 Installation des dépendances..."
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
./.venv/bin/pip install --quiet pytest

if [ ! -f .env ]; then
  cp .env.example .env
  echo "📝 .env créé depuis .env.example — pense à y mettre tes clés Alpaca."
else
  echo "📝 .env déjà présent (inchangé)."
fi

echo ""
echo "✅ Installation terminée."
echo "   Active l'environnement :   source .venv/bin/activate"
echo "   Lance un test rapide   :   python run_backtest.py --synthetic --bars 3000"
echo "   (ou via make : make test / make backtest)"
