from typing import Dict

class Listing: # potentially separate buyprice and sell price
    def __init__(self, orderbook: Dict[str, Dict[int, int]], product: str) -> None:
        self.buy_orders = orderbook["BUY"] #dict of {price: quantity} top is lowest price
        self.sell_orders = orderbook["SELL"] #dict of {price: quantity} top is highest price
        self.product = product
        
class Order:
    def __init__(self, product: str, price: int, quantity: int):
        self.product = product
        self.price = price
        self.quantity = quantity

    def is_valid(self) -> bool:
        return (isinstance(self.product, str) and self.product and
                isinstance(self.quantity, int) and self.quantity != 0 and
                isinstance(self.price, int) and self.price > 0)

    def __str__(self):
        return f"Order(product={self.product}, price={self.price}, quantity={self.quantity})"

class Portfolio:
    def __init__(self):
        self.cash: float = 0
        self.quantity: Dict[str, int] = {}
        self.pnl: float = 0

    def __str__(self):
        return f"Portfolio(cash={self.cash}, quantity={self.quantity}, pnl={self.pnl})"

class Market:
    def __init__(self, traderData, tick, listings, order_depths, own_trades, market_trades, position, observations):
        self.tick = tick
        self.listings = listings
