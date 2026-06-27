# Guide de mise en place (pas à pas)

Ce guide te fait passer de zéro à un bot de scalping **backtesté et en paper
trading**, dans l'ordre. Suis les étapes une par une.

> ⏱️ Compte ~15 minutes pour l'installation + premiers résultats.
> ⚠️ Rappel : argent réel = risque de perte. On reste en **paper** tant que
> la stratégie n'est pas validée.

---

## Prérequis

- **Python 3.10+** (`python3 --version`)
- **git**
- Un compte **Alpaca** (gratuit) pour le paper trading — étape 3.

---

## Étape 1 — Récupérer le projet

Si ce n'est pas déjà fait :

```bash
git clone <url-du-repo>
cd test_ui-ux
git checkout claude/trading-scalping-patterns-jbgsgz
```

---

## Étape 2 — Installer

Le plus simple (crée un environnement isolé `.venv`, installe tout, prépare `.env`) :

```bash
./setup.sh
source .venv/bin/activate
```

> Sous Windows (PowerShell) : `python -m venv .venv` puis
> `.venv\Scripts\activate` puis `pip install -r requirements.txt pytest`.

Vérifie que tout marche :

```bash
make test          # 21 tests doivent passer
make backtest      # backtest de démo sur données synthétiques
```

---

## Étape 3 — Configurer Alpaca (paper)

Nécessaire **seulement** pour passer des ordres paper (étape 8). Pour le
backtest et l'analyse, tu peux sauter cette étape.

1. Crée un compte sur https://app.alpaca.markets/ et bascule en **Paper**.
2. Génère une **API Key** + **Secret** (compte Paper).
3. Ouvre le fichier `.env` (créé par `setup.sh`) et remplis :

```
ALPACA_API_KEY=ta_cle
ALPACA_API_SECRET=ton_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

> 🔒 `.env` est ignoré par git : il ne sera jamais commité. **Ne partage
> jamais** ces clés. Si tu en as déjà exposé (même paper), **régénère-les**.

---

## Étape 4 — Récupérer des données réelles

C'est la donnée la plus importante : sans vraies données, impossible de
savoir si une stratégie marche.

```bash
python fetch_data.py --symbol BTCUSDT --interval 5m --bars 8000
# -> crée data/BTCUSDT_5m.csv
```

> Si Binance est bloqué dans ton pays (erreur HTTP 451), deux options :
> - utiliser un VPN, ou
> - récupérer un CSV OHLCV ailleurs (colonnes : `time,open,high,low,close,volume`)
>   et le placer dans `data/`.

---

## Étape 5 — Quels patterns ont un vrai edge ?

```bash
python analyze_patterns.py --csv data/BTCUSDT_5m.csv --save stats.csv
```

Lis le tableau (trié par `expectancy_R`). **Garde** les patterns à espérance
positive avec assez d'occurrences (`n`), **méfie-toi** des autres. C'est ta
première sélection objective.

---

## Étape 6 — Backtester la stratégie complète

```bash
# Cassure simple
python run_backtest.py --csv data/BTCUSDT_5m.csv --capital 200 --risk 1 --rr 2

# Version plus sereine : entrée au retest + filtre de tendance multi-TF
python run_backtest.py --csv data/BTCUSDT_5m.csv --retest --mtf
```

Regarde surtout : **profit factor > 1**, **espérance > 0**, **drawdown**
supportable. Si c'est négatif, ne passe pas à la suite : ajuste (patterns
sélectionnés, `--adx-min`, `--rr`, `--min-confidence`).

---

## Étape 7 — Valider en walk-forward (anti-illusion)

Un bon backtest peut être un coup de chance / du sur-apprentissage. Le
walk-forward choisit les réglages sur une période et les teste sur la
**suivante, jamais vue** :

```bash
python run_walkforward.py --csv data/BTCUSDT_5m.csv --is 2000 --oos 500
```

Ce qui compte : que la **majorité des fenêtres OOS soient profitables** et
que le net OOS cumulé soit positif. Si l'OOS s'effondre → la stratégie ne
généralise pas, on ne la trade pas.

---

## Étape 8 — Passer en paper trading

D'abord en **alerte seule** (aucun ordre) :

```bash
python run_live.py --interval 5m --once          # une passe
python run_live.py --interval 5m                 # boucle continue
```

Quand tu es confiant et que `.env` est rempli, **exécution paper** :

```bash
python run_live.py --interval 5m --execute --retest
```

Laisse tourner plusieurs jours/semaines en paper et compare au backtest
**avant** d'envisager quoi que ce soit en réel.

---

## Workflow résumé

```
fetch_data  →  analyze_patterns  →  run_backtest  →  run_walkforward  →  run_live (alerte)  →  run_live --execute (paper)
```

---

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| `Binance HTTP 451` | Restriction géographique : VPN ou CSV externe (étape 4) |
| `ModuleNotFoundError` | Environnement non activé : `source .venv/bin/activate` |
| `--execute demandé mais clés Alpaca absentes` | Remplir `.env` (étape 3) |
| Backtest négatif | Normal sur du bruit / sans edge : sélectionner les patterns, ajuster filtres |
| Aucun signal en live | Marché calme ou filtres stricts : baisser `--min-confidence`, vérifier `--no-adx` |

---

## Rappel important

Aucun bot ne garantit de gains. Cet outil sert à **mesurer et décider avec
méthode**, pas à promettre des profits. Ne risque que ce que tu peux perdre,
et seulement après une validation sérieuse (backtest + walk-forward + paper).
