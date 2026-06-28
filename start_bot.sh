#!/usr/bin/env bash
# ============================================================
#  Lancement du bot de trading en arrière-plan permanent
#
#  Usage :
#    ./start_bot.sh            # alerte Telegram seulement
#    ./start_bot.sh --execute  # + ordres Alpaca Paper
#    ./start_bot.sh stop       # arrêter le bot
#    ./start_bot.sh logs       # voir les dernières lignes du log
#    ./start_bot.sh status     # vérifier si le bot tourne
# ============================================================

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$BOT_DIR/bot.log"
PID_FILE="$BOT_DIR/bot.pid"
PYTHON="${PYTHON:-python3}"

# --- Arrêt ---
if [[ "$1" == "stop" ]]; then
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "✅ Bot arrêté (PID $PID)" || echo "⚠️  Process introuvable"
        rm -f "$PID_FILE"
    else
        echo "ℹ️  Aucun bot en cours (pas de $PID_FILE)"
    fi
    exit 0
fi

# --- Logs ---
if [[ "$1" == "logs" ]]; then
    tail -50 "$LOG_FILE" 2>/dev/null || echo "Aucun log trouvé."
    exit 0
fi

# --- Status ---
if [[ "$1" == "status" ]]; then
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✅ Bot actif (PID $PID)"
            echo "   Log : $LOG_FILE"
        else
            echo "⚠️  PID file trouvé mais process mort — relance avec ./start_bot.sh"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Bot arrêté"
    fi
    exit 0
fi

# --- Vérif déjà lancé ---
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "⚠️  Bot déjà en cours (PID $PID). Utilise './start_bot.sh stop' d'abord."
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# --- Démarrage ---
cd "$BOT_DIR"
nohup $PYTHON run_live.py "$@" >> "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

echo "✅ Bot démarré en arrière-plan (PID $PID)"
echo "   Log en direct : tail -f $LOG_FILE"
echo "   Arrêter       : ./start_bot.sh stop"
echo "   Status        : ./start_bot.sh status"
