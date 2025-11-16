from datamodel import *
from typing import List, Dict
from collections import defaultdict
import math


class Trader:
    def __init__(self):
        # Rolling midprice history per product
        self.mid_history: Dict[str, List[float]] = defaultdict(list)
        self.window: int = 50          # lookback window for mean/std
        self.z_entry: float = 1.5      # z-score threshold

        # Sizes
        self.mm_size: int = 2          # base size for market-making
        self.dir_size: int = 5         # size for directional mean-reversion trades

    def _get_best_bid_ask(self, listings: Listing):
        """Safely get best bid and best ask from Listing."""
        if not listings.buy_orders or not listings.sell_orders:
            return None, None

        # Dicts preserve insertion order, but be explicit:
        best_bid = max(listings.buy_orders.keys())
        best_ask = min(listings.sell_orders.keys())
        return best_bid, best_ask

    def _update_history_and_z(self, product: str, mid: float):
        """Update mid history and return (mean, std, z-score)."""
        hist = self.mid_history[product]
        hist.append(mid)
        if len(hist) > self.window:
            hist.pop(0)

        if len(hist) < 10:
            # Not enough data, treat as no deviation
            return mid, 0.0, 0.0

        mean = sum(hist) / len(hist)
        var = sum((x - mean) ** 2 for x in hist) / len(hist)
        std = math.sqrt(var) if var > 0 else 0.0
        z = (mid - mean) / std if std > 0 else 0.0
        return mean, std, z

    def run(self, state: State) -> List[Order]:
        orders: List[Order] = []

        for product in state.products:
            listings = Listing(state.orderbook[product], product)
            best_bid, best_ask = self._get_best_bid_ask(listings)
            if best_bid is None or best_ask is None:
                continue

            mid = (best_bid + best_ask) / 2
            mean, std, z = self._update_history_and_z(product, mid)

            pos = state.positions[product]
            limit = state.pos_limit[product]

            # Remaining capacity on each side
            cap_buy = max(0, limit - pos)   # how much more we can buy
            cap_sell = max(0, limit + pos)  # how much more we can sell (if pos is negative)

            # ==========================
            # 1) Mean-reversion overlay
            # ==========================
            if std > 0 and abs(z) > self.z_entry:
                # We think price is "too high" -> short
                if z > 0 and cap_sell > 0:
                    size = min(self.dir_size, cap_sell)
                    # Cross or trade at best bid to get filled
                    orders.append(Order(product, int(best_bid), -size))
                # We think price is "too low" -> long
                elif z < 0 and cap_buy > 0:
                    size = min(self.dir_size, cap_buy)
                    orders.append(Order(product, int(best_ask), size))

                # In extreme regimes we don't market-make further on this product
                continue

            # Inventory-aware sizes
            mm_buy_size = min(self.mm_size, cap_buy)
            mm_sell_size = min(self.mm_size, cap_sell)

            # Light inventory tilt: if long, quote less on buy; if short, quote less on sell
            if pos > 0:
                # Already long, reduce further buying
                mm_buy_size = max(0, mm_buy_size - 1)
            elif pos < 0:
                # Already short, reduce further selling
                mm_sell_size = max(0, mm_sell_size - 1)

            # If no capacity, skip
            if mm_buy_size == 0 and mm_sell_size == 0:
                continue

            # Choose prices:
            # Try to quote *inside* the spread if possible,
            # so bots improving prices or crossing may hit us.
            bid_quote = best_bid
            ask_quote = best_ask

            # If there is at least 2 ticks of spread, step inside by 1
            if best_ask - best_bid >= 2:
                bid_quote = best_bid + 1
                ask_quote = best_ask - 1

            # 2a) Post a resting buy (provide liquidity)
            if mm_buy_size > 0:
                # Only quote if we are not paying above our idea of fair value too much
                if bid_quote <= mean + 1:  # small safety buffer
                    orders.append(Order(product, int(bid_quote), mm_buy_size))

            # 2b) Post a resting sell (provide liquidity)
            if mm_sell_size > 0:
                # Only quote if we are not selling far below fair value
                if ask_quote >= mean - 1:
                    orders.append(Order(product, int(ask_quote), -mm_sell_size))

        return orders
