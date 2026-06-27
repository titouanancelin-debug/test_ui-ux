# Bot de scalping crypto — patterns & cassures S/R

Boîte à outils Python pour le **scalping crypto**, basée sur :

- les **patterns de chandeliers** japonais (~30 figures),
- les **figures chartistes** (double top/bottom, triangles, têtes-épaules, biseaux, drapeaux),
- les **niveaux de support/résistance et leurs cassures** (breakouts) — l'approche que tu privilégies,
- une **gestion du risque** sérieuse,
- un **backtester réaliste** (frais + slippage + anti-lookahead) pour *prouver* ce qui marche.

> ⚠️ **Avertissement.** Ceci est un outil de **recherche et de paper trading**. Le trading comporte un risque de perte en capital. Aucun pattern n'est fiable à 100 % ; en scalping, frais et spread mangent les petits gains. **Ne mets pas d'argent réel** avant d'avoir validé une stratégie en backtest **puis** en paper sur une période significative.

---

## 1. Analyse du prototype d'origine

Le fichier de départ (`trading_bot_alpaca_2.py`) était une bonne base, mais comportait plusieurs problèmes corrigés ici :

| Problème | Impact | Correction |
|---|---|---|
| **Clés API en dur** dans le code | Fuite de secrets dès le commit | Clés via `.env` / variables d'environnement, `.gitignore` |
| **Pas de plafond de notionnel** | Avec un stop serré, la taille calculée pouvait dépasser le capital (levier involontaire) | `max_notional_pct` dans `risk.py` |
| **SL et TP envoyés séparément** (pas d'OCO) | Si le TP passe, le SL reste actif → position fantôme | Ordre **bracket (OCO)** dans `broker_alpaca.py` |
| **Trailing stop factice** | La fonction *affichait* un nouveau stop sans jamais le poser | Trailing réel et testé dans le backtester |
| **Décisions sur bougie non clôturée** | « Repaint » : signaux qui changent après coup | On retire la bougie en cours ; décision sur bougies **clôturées** uniquement |
| **Aucun backtest** | Impossible de savoir si la stratégie est rentable | Backtester événementiel avec métriques |
| **Peu de patterns** (hammer, engulfing) | Couverture limitée | ~30 chandeliers + 13 figures chartistes |
| **Frais/slippage ignorés** | Résultats trop optimistes | Modélisés à l'entrée et à la sortie |

---

## 2. Architecture

```
scalping/
├── config.py          # Paramètres + secrets (via .env)
├── data.py            # Binance / CSV / données synthétiques (OHLCV)
├── indicators.py      # EMA, RSI(Wilder), MACD, ATR, ADX, Bollinger, VWAP
├── candlesticks.py    # ~30 patterns de chandeliers (vectorisés)
├── chart_patterns.py  # double/triple top-bottom, H&S, triangles, wedges, flags
├── levels.py          # support/résistance + détection de cassure
├── risk.py            # position sizing, SL/TP, plafond de notionnel
├── strategy.py        # moteur de signaux (combine tout + score de confiance)
├── backtest.py        # backtester réaliste + métriques
└── broker_alpaca.py   # exécution Alpaca Paper (ordres bracket OCO)
run_backtest.py        # CLI backtest
run_live.py            # CLI live (alertes paper, ou exécution Alpaca)
```

Tout fonctionne à partir d'un **DataFrame OHLCV standard** (`time, open, high, low, close, volume`) → agnostique à la source de données.

---

## 3. Installation

```bash
pip install -r requirements.txt
cp .env.example .env      # puis renseigne tes clés Alpaca Paper
```

---

## 4. Utilisation

### Backtest

```bash
# Données synthétiques (hors-ligne, pour tester la mécanique)
python run_backtest.py --synthetic --bars 3000

# Depuis un CSV (time,open,high,low,close,volume)
python run_backtest.py --csv data/btc_5m.csv --capital 200 --risk 1 --rr 2

# Données Binance (si le réseau l'autorise)
python run_backtest.py --symbol BTCUSDT --interval 5m --limit 1000 --plot
```

### Live (paper)

```bash
# Mode ALERTE seulement (aucun ordre envoyé) — recommandé pour commencer
python run_live.py --interval 5m --once

# Exécution réelle sur Alpaca Paper (après validation en backtest)
python run_live.py --interval 5m --execute
```

---

## 5. La stratégie

La cassure de S/R est le **signal principal** (pondération forte), filtrée contre les faux breakouts :

- la **clôture** (pas seulement la mèche) dépasse le niveau d'au moins `buffer_atr × ATR` ;
- le **volume** dépasse `breakout_volume_mult ×` sa moyenne.

Viennent ensuite, en **confirmation/contexte** :

- **tendance** (EMA 20/50) et **MACD** ;
- **patterns de chandeliers** et **figures chartistes** ;
- **garde-fou RSI** (on ne sur-achète pas en zone de surachat).

Chaque signal porte un **score de confiance (0..1)** et la **liste des raisons** (transparence en alerte et au debug). Le `stop` se place au-delà du niveau cassé (ou via l'ATR), le `take-profit` suit le ratio R/R borné par le prochain niveau S/R.

> La **même** logique (`strategy.generate_signal`) sert au backtest **et** au live : ce qui est testé est exactement ce qui est exécuté.

---

## 6. Patterns intégrés

**Chandeliers (~30)** : doji (+ dragonfly / gravestone / long-legged), spinning top, marubozu (haussier/baissier), hammer, inverted hammer, hanging man, shooting star, engulfing (haussier/baissier), harami (haussier/baissier), piercing line, dark cloud cover, tweezer top/bottom, kicker (haussier/baissier), morning/evening star, three white soldiers, three black crows, three inside up/down, three outside up/down, abandoned baby (haussier/baissier).

**Figures chartistes (13)** : double top, double bottom, triple top, triple bottom, tête-épaules, tête-épaules inversée, triangle ascendant/descendant/symétrique, biseau ascendant/descendant, drapeau haussier/baissier.

---

## 7. Sécurité

- **Jamais** de clés dans le code : elles passent par `.env` (ignoré par git).
- Si tu as déjà exposé des clés (même paper), **régénère-les** dans ton dashboard Alpaca.

---

## 8. Recommandations / suite possible

1. **Valider sur données réelles** (CSV historiques de plusieurs mois, plusieurs régimes de marché) avant tout. Le résultat sur synthétique ne prouve que la mécanique.
2. **Walk-forward / out-of-sample** : optimiser sur une période, valider sur une autre, pour éviter le sur-apprentissage.
3. **Mesurer chaque pattern séparément** : garder ceux qui ont une vraie espérance positive *sur tes données*, désactiver les autres.
4. **Multi-timeframe** : confirmer la tendance sur un TF supérieur (15m) avant d'entrer sur un TF inférieur (5m/1m).
5. **Filtre de régime** : ne trader les cassures que quand l'ADX (force de tendance) est suffisant ; éviter les marchés trop plats.
6. **Coûts** : recalibrer `fee_rate` et `slippage` sur les frais réels de ton exchange — c'est décisif en scalping.
7. **Tests unitaires** sur les détecteurs de patterns (cas connus) pour éviter les régressions.
