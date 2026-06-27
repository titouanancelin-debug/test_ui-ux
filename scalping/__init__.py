"""
Paquet `scalping` — boîte à outils de scalping crypto basée sur :
  - les patterns de chandeliers japonais (candlesticks),
  - les figures chartistes (double top/bottom, triangles, H&S, drapeaux...),
  - les niveaux de support/résistance et leurs cassures (breakouts),
  - la gestion du risque,
  - un backtester pour valider tout ça sur données historiques.

Conçu pour être agnostique à la source de données : tout fonctionne à
partir d'un DataFrame OHLCV standard (colonnes : time, open, high, low,
close, volume).
"""

__version__ = "0.1.0"
