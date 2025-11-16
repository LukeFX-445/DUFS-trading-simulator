from datamodel import *
from typing import List, Dict
from collections import defaultdict
import math


class Trader:
    def __init__(self):
        # Rolling midprice history per product
        self.mid_history: Dict[str, List[float]] = defaultdict(list)

        # Parameters you can tune
        self.window: int = 80        # longer window for smoother mean/std
        self.z_entry: float = 1.5    # keep 1.5 for now; you can try 1.3 or 1.7 later

        self.mm_size: int = 3        # market-making size (was 2)
        self.dir_size: int = 7       # directional mean-reversion size (was 5)

        # When |pos| > limit * this, start aggressively flattening
        self.inv_aggressive: float = 0.7

    def _get_best_bid_ask(self, listings: Listing):
        if not listings.buy_orders or not listings.sell_orders:
            return None, None
        best_bid = max(listings.buy_orders.keys())
        best_ask = min(listings.sell_orders.keys())
        return best_bid, best_ask

    def _update_history_and_z(self, product: str, mid: float):
        hist = self.mid_history[product]
        hist.append(mid)
        if len(hist) > self.window:
            hist.pop(0)

        if len(hist) < 10:
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

            # Remaining capacity
            cap_buy = max(0, limit - pos)
            cap_sell = max(0, limit + pos)

            # ==========================
            # 1) Mean-reversion overlay
            # ==========================
            if std > 0 and abs(z) > self.z_entry:
                # Too high -> short
                if z > 0 and cap_sell > 0:
                    size = min(self.dir_size, cap_sell)
                    orders.append(Order(product, int(best_bid), -size))
                # Too low -> long
                elif z < 0 and cap_buy > 0:
                    size = min(self.dir_size, cap_buy)
                    orders.append(Order(product, int(best_ask), size))

                # Skip MM in extreme regime
                continue

            # ==========================
            # 2) Spread / bot-capture MM
            # ==========================
            mm_buy_size = min(self.mm_size, cap_buy)
            mm_sell_size = min(self.mm_size, cap_sell)

            # Light tilt: if long, buy less; if short, sell less
            if pos > 0:
                mm_buy_size = max(0, mm_buy_size - 1)
            elif pos < 0:
                mm_sell_size = max(0, mm_sell_size - 1)

            # Aggressive flatten if close to limits
            if limit > 0 and abs(pos) > self.inv_aggressive * limit:
                if pos > 0:
                    # Large long -> prioritise sells, no new buys
                    mm_buy_size = 0
                else:
                    # Large short -> prioritise buys, no new sells
                    mm_sell_size = 0

            if mm_buy_size == 0 and mm_sell_size == 0:
                continue

            # Choose quotes
            spread = best_ask - best_bid
            bid_quote = best_bid
            ask_quote = best_ask

            if spread >= 2:
                # Step inside to attract bots
                bid_quote = best_bid + 1
                ask_quote = best_ask - 1
            # If spread == 1, we just quote at touch

            # Fair value safety band slightly relaxed: +/-2 ticks
            fv_band = 2

            # Resting buy
            if mm_buy_size > 0:
                if bid_quote <= mean + fv_band:
                    orders.append(Order(product, int(bid_quote), mm_buy_size))

            # Resting sell
            if mm_sell_size > 0:
                if ask_quote >= mean - fv_band:
                    orders.append(Order(product, int(ask_quote), -mm_sell_size))

        return orders
