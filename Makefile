PYTHON ?= python3
SYMBOL ?= BTCUSDT
INTERVAL ?= 5m
BARS ?= 8000

.PHONY: help setup install test backtest analyze walkforward fetch live clean

help:
	@echo "Cibles disponibles :"
	@echo "  make setup        Installe tout (venv + dépendances + .env)"
	@echo "  make test         Lance les tests unitaires"
	@echo "  make backtest     Backtest de démo (données synthétiques)"
	@echo "  make analyze      Classe les patterns par espérance (synthétique)"
	@echo "  make walkforward  Validation walk-forward (synthétique)"
	@echo "  make fetch        Télécharge des données réelles -> data/ (SYMBOL/INTERVAL/BARS)"
	@echo "  make live         Une analyse live en mode alerte"
	@echo "  make clean        Nettoie les fichiers temporaires"

setup:
	./setup.sh

install:
	$(PYTHON) -m pip install -r requirements.txt pytest

test:
	$(PYTHON) -m pytest -q

backtest:
	$(PYTHON) run_backtest.py --synthetic --bars 3000

analyze:
	$(PYTHON) analyze_patterns.py --synthetic --bars 4000

walkforward:
	$(PYTHON) run_walkforward.py --synthetic --bars 8000

fetch:
	$(PYTHON) fetch_data.py --symbol $(SYMBOL) --interval $(INTERVAL) --bars $(BARS)

live:
	$(PYTHON) run_live.py --interval $(INTERVAL) --once

clean:
	rm -rf __pycache__ scalping/__pycache__ tests/__pycache__ .pytest_cache
	rm -f equity_curve.png
	@echo "Nettoyé."
