# btc-race-bot

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/skwanz001/btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/skwanz001/btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A patient long-only bot that trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by minute, on the make.fun bars-replay/v1 protocol. It buys once, in full, on the second batch and then manages the position with a wide trailing stop (250 bps below the highest close since entry). No re-entry after the stop: at most one round trip, so fees stay bounded.

## Run it

```sh
python3 -P -s main.py
```

Standard library only. No network, no wall clock, no environment reads: every decision is a pure function of the bars seen so far, so two runs on the same data produce byte-identical replies.

## Why this shape

The dev window is one slow grind (+363 bps over 24 hours, per-minute noise stdev 8 bps) plus a single +2.3% jump. A full-size round trip costs ~41 bps on this pool (4 bps fee + 2 bps slippage + ~17 bps impact per leg), so 1-minute signals are mostly noise once costs are paid. Everything active that was swept against the dev window lost to buy-and-hold:

| Strategy (dev window, 1,440 bars) | Net PnL | Trades | Max DD |
| --- | --- | --- | --- |
| buy-and-hold (house baseline) | +$32.17 | 1 | 1.98% |
| momentum (house baseline) | +$34.94 | 1 | 1.98% |
| **this bot: buy seq 1 + 250 bps trailing stop** | **+$32.33** | **1** | **1.98%** |
| EMA-cross 8/21 (baseline-like) | -$114.83 | 76 | 11.65% |
| Donchian 60/30, trail 80, TP 150 | +$2.14 | 18 | 2.74% |
| EMA-trend 12/48, momentum filter | -$25.00 | 24 | 3.91% |

The trailing stop is what earns its keep outside the dev window: on a mirrored (falling) rebuild of the dev window this bot loses -$24.62 where buy-and-hold loses -$38.90, and on a demeaned (flat) rebuild it makes +$2.59 where buy-and-hold loses -$3.96. Delayed/dip-buy entries were tested and rejected: they gain on dev (+$34.94 buying at bar 24, +$36.55 buying the dip) but lose on the mirror (-$27.52 / -$30.41) and on 24 block-bootstrap windows (mean $36.23 / $35.45 vs $37.16 for buying at bar 1) — the dev gain is timing luck on the window's early dip, not a robust edge.

Dev-window figures were reproduced exactly (to the cent) by the official kit grader on the buy-and-hold baseline (net PnL $32.167313, 1 trade, max drawdown 0.019778194, fees $0.813033), which validates the local replica used to score this bot; the kit's `grade-local --driver process` cannot run Python bots (Node only, no Docker here), so the bot itself was scored with that validated replica.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
