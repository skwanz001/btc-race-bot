"""cbBTC trend rider for make.fun btc-race-24h-20261123-0511.

Strategy (v2): patient long-only rider on the 1-minute cbBTC/USDC replay.
Buys once, in full, on the second batch (seq >= 1) and then manages the
position with a wide trailing stop. Deliberately different from the
house buy-and-hold bot, which buys on batch 0 with uncapped slippage
and never sells: this bot waits one bar, caps its buy slippage at
150 bps, and exits the whole position when the close falls 250 bps
below the highest close seen since entry. No re-entry after the stop:
one round trip at most, so fees stay bounded (a full-size round trip
costs ~41 bps on this pool) and the bot can never whipsaw itself to
death in chop. The stop is wide on purpose: on the dev window the
largest peak-to-trough pullback is 197 bps, so it never fires there
and the bot keeps the full up-move; in a falling window it caps the
loss near 250 bps plus fill costs instead of riding the whole decline.

Why this shape: the dev window is one slow grind (+363 bps over 24h,
per-minute noise stdev 8 bps) plus a single +2.3% jump. Every active
strategy swept against it lost to buy-and-hold (EMA-cross 8/21:
-$114.83 on 76 trades; Donchian 60/30: about breakeven on 18 trades),
because each round trip costs ~41 bps and 1-minute signals are mostly
noise. The winning shape is therefore buy-early, trade once, and let
the stop - not a signal - decide the exit. Verified on the dev window
and on mirrored (falling) and demeaned (flat) rebuilds of it; see
README for the numbers.

Protocol: agent-fun/bars-replay/v1, spoken through the vendored shim
(vendor/makefun_bars.py, a byte-identical copy of the kit SDK shim).
Standard library only. No wall clock, no network, no environment reads:
every decision is a pure function of the bars seen so far, so two runs
on the same data produce byte-identical replies.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
BUY_SLIPPAGE_BPS = 150
SELL_SLIPPAGE_BPS = 300
# Trailing stop: exit when the close is this far below the highest close
# seen since entry (basis points). 250 bps clears the dev window's worst
# pullback (197 bps) with room to spare.
TRAIL_BPS = 250

# Whether the one full-size buy has been placed (set when the position
# first appears, so a rejected buy is retried on the next bar).
_bought = False
# Whether the trailing stop has fired; after it, the bot never re-enters.
_stopped_out = False
# Highest close seen while holding, in raw price units (price_scale 5).
_peak_close = None


def on_batch(state, batch):
    global _bought, _stopped_out, _peak_close
    # Only decide on batches that carry a fresh CBBTC bar; a minute the
    # recorder missed carries no bar and no decision.
    if not any(bar["symbol"] == SYMBOL for bar in batch["bars"]):
        return []
    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    held = state.positions.get(SYMBOL)
    if held is not None:
        _bought = True
        if _peak_close is None or close > _peak_close:
            _peak_close = close
        # Trailing stop, integer math: close * 10000 <= peak * (10000 - 250).
        if close * 10000 <= _peak_close * (10000 - TRAIL_BPS):
            _stopped_out = True
            _peak_close = None
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": SELL_SLIPPAGE_BPS,
            }]
        return []
    if _bought or _stopped_out:
        return []
    # One full-size buy, from the second batch on, capped by the cash held.
    if state.seq < 1:
        return []
    amount = state.cash
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []
    _peak_close = close
    return [{
        "side": "buy",
        "symbol": SYMBOL,
        "notional_quote_units": amount,
        "max_slippage_bps": BUY_SLIPPAGE_BPS,
    }]


makefun_bars.run(on_batch)
