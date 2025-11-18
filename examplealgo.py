from collections import deque

class Order:
    def __init__(self, product, price, volume):
        self.product = product
        self.price = price
        self.volume = volume

class Trader:
    def __init__(self):
        # Strategy parameters
        self.short_window = 20                 # short EMA lookback in ticks
        self.long_window = 100                # long EMA lookback in ticks
        self.z_score_window = 30             # window for moving average & Z-score
        self.z_entry_threshold = 2.0         # Z-score threshold to trigger trades
        self.z_exit_threshold = 0.5          # Z-score to exit (if using position unwinding)
        # EMA smoothing factors for short and long windows
        self.alpha_short = 2 / (self.short_window + 1)
        self.alpha_long = 2 / (self.long_window + 1)
        # Per-asset state
        self.history = {}    # recent price history for each asset (for Z-score)
        self.short_ema = {}  # current short EMA values per asset
        self.long_ema = {}   # current long EMA values per asset
        self.position = {}   # current net position per asset for risk management

    def run(self, state):
        """
        Decide trade orders for each asset based on live order book and price history.
        This function is called each simulation tick by main.py.
        """
        orders = []  # gather all orders to return
        # Iterate over each asset's order book in the provided state
        for asset, order_book in state.get("order_books", state).items():
            # Initialize tracking for new asset if not seen before
            if asset not in self.history:
                self.history[asset] = deque(maxlen=self.z_score_window)
                self.short_ema[asset] = None
                self.long_ema[asset] = None
                self.position[asset] = 0

            # Get top-of-book prices and volumes
            best_bid_price = order_book["bids"][0][0] if order_book["bids"] else None
            best_bid_vol   = order_book["bids"][0][1] if order_book["bids"] else 0
            best_ask_price = order_book["asks"][0][0] if order_book["asks"] else None
            best_ask_vol   = order_book["asks"][0][1] if order_book["asks"] else 0
            if best_bid_price is None or best_ask_price is None:
                continue  # skip this asset if no valid market data

            mid_price = (best_bid_price + best_ask_price) / 2.0  # mid-price as average of best bid/ask

            # Update or initialize exponential moving averages for trend detection
            if self.short_ema[asset] is None:
                # On first tick for this asset, set EMA to mid_price
                self.short_ema[asset] = mid_price
                self.long_ema[asset] = mid_price
            else:
                # Update EMAs with smoothing
                self.short_ema[asset] = (self.alpha_short * mid_price 
                                         + (1 - self.alpha_short) * self.short_ema[asset])
                self.long_ema[asset]  = (self.alpha_long * mid_price 
                                         + (1 - self.alpha_long) * self.long_ema[asset])

            # Append current price to history and compute adaptive Z-score
            self.history[asset].append(mid_price)
            z_score = 0.0
            if len(self.history[asset]) >= self.z_score_window:
                avg_price = sum(self.history[asset]) / len(self.history[asset])
                # Compute standard deviation over the window
                variance = sum((p - avg_price) ** 2 for p in self.history[asset]) / len(self.history[asset])
                std_dev = variance ** 0.5
                if std_dev > 1e-9:  # avoid division by zero
                    z_score = (mid_price - avg_price) / std_dev

            # Determine if the asset is trending or mean-reverting
            trend_dir = 0   # +1 for uptrend, -1 for downtrend, 0 for no clear trend
            if self.short_ema[asset] is not None and self.long_ema[asset] is not None:
                if self.short_ema[asset] > self.long_ema[asset]:
                    trend_dir = 1   # short-term price above long-term average → uptrend bias
                elif self.short_ema[asset] < self.long_ema[asset]:
                    trend_dir = -1  # short-term price below long-term average → downtrend bias
            # We flag a trend as significant if there is a clear direction
            trending = (trend_dir != 0)
            
            # (Optional) Evaluate order book imbalance or bot orders for regime hints
            # e.g., if one side’s volume is much larger, or bots’ top orders are only on one side.
            book_imbalance = best_bid_vol - best_ask_vol
            # If bots' order data is available in state (e.g., state['bot_orders']), one could use it:
            # bot_bid = state['bot_orders'][asset]['bid_price_1']; bot_ask = state['bot_orders'][asset]['ask_price_1'] (etc.)
            # Presence of bot quotes on both sides (liquidity) vs pulled liquidity can adjust the strategy.

            # Decide orders based on identified regime and signals
            asset_orders = []  # list to collect orders for this asset
            # Base order size (could be tuned per asset volatility or price scale)
            base_size = 5
            if "NOTE" in asset:  # example: smaller trades for less volatile assets like bonds/notes
                base_size = 2

            if trending and trend_dir == 1:
                # **Uptrend regime** – follow momentum (prefer long positions)
                # If price dipped significantly (Z-score low), treat as a pullback – buy the dip
                if z_score < -self.z_entry_threshold:
                    asset_orders.append(Order(asset, best_bid_price, base_size))  # buy at best bid price
                # Always maintain a buy order slightly below current bid to catch minor dips
                dip_buy_price = best_bid_price - 1
                if dip_buy_price > 0:
                    asset_orders.append(Order(asset, dip_buy_price, base_size))
                # If we already hold a long position and price is somewhat high, set a sell to take profit
                if self.position.get(asset, 0) > 0 and z_score > 0:
                    sell_vol = min(base_size, self.position[asset])
                    if sell_vol > 0:
                        asset_orders.append(Order(asset, best_ask_price, -sell_vol))  # sell at best ask to take profit
            elif trending and trend_dir == -1:
                # **Downtrend regime** – follow momentum (prefer short positions)
                # If price popped up (Z-score high) in a downtrend, treat as a rally to sell into
                if z_score > self.z_entry_threshold:
                    asset_orders.append(Order(asset, best_ask_price, -base_size))  # sell at best ask price
                # Keep a sell order slightly above current ask to short into any small rally
                spike_sell_price = best_ask_price + 1
                asset_orders.append(Order(asset, spike_sell_price, -base_size))
                # If we hold a short position and price has fallen back down, place a buy to cover some shorts (profit take)
                if self.position.get(asset, 0) < 0 and z_score < 0:
                    cover_vol = min(base_size, -self.position[asset])
                    if cover_vol > 0:
                        asset_orders.append(Order(asset, best_bid_price, cover_vol))  # buy at best bid to cover shorts
            else:
                # **Range-bound regime** – mean reversion & spread capturing
                # Place passive orders on both sides of the order book to earn spread (market making)
                asset_orders.append(Order(asset, best_bid_price, base_size))    # buy at current bid
                asset_orders.append(Order(asset, best_ask_price, -base_size))   # sell at current ask
                # If price is at a statistical extreme, execute contrarian trade:
                if z_score > self.z_entry_threshold:
                    # Price significantly above recent mean → sell expecting reversion
                    asset_orders.append(Order(asset, best_ask_price, -(base_size * 2)))
                if z_score < -self.z_entry_threshold:
                    # Price significantly below mean → buy expecting a rebound
                    asset_orders.append(Order(asset, best_bid_price, base_size * 2))

            # (Risk management: e.g., limit total position size per asset, adjust orders if needed.)
            # In a complete implementation, we would update self.position[asset] after trades fill.

            # Collect orders for this asset
            orders.extend(asset_orders)
        return orders
