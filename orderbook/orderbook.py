from enum import Enum
from collections import deque
from sortedcontainers import SortedDict
from typing import *

class OrderType(Enum):
    BUY = 1
    SELL = 2

    def __str__(self):
        if self.value == 1:
            return "BUY"
        elif self.value == 2:
            return "SELL"
        else:
            return ""


class PricePoint:
    def __init__(self):
        self.limit_price: Optional[int] = None
        self.size: int = 0
        self.total_volume: int = 0

        self.head_order: Optional[OrderBookEntry] = None
        self.tail_order: Optional[OrderBookEntry] = None


class OrderBookEntry:
    """
    id, 
    timestamp (utc) use time.time(), 
    type (buy/sell), 
    price, 
    size
    """
    def __init__(self, id : int, timestamp : float, type : OrderType, price : int, quantity : int, parent_pricepoint = None):  
        self.id: int = id
        self.timestamp: float = timestamp
        self.type: OrderType = type
        self.price: int = price
        self.quantity: int = quantity

        self.next_order = None
        self.prev_order = None
        self.parent_pricepoint = parent_pricepoint
    

    def __str__(self):
        return f"{self.type} {self.quantity}@{self.price} [{self.id}; {self.timestamp}]" 



class OrderBookTree:
    """
    This would be the buy / sell orders in the order book.

    https://quant.stackexchange.com/questions/3783/what-is-an-efficient-data-structure-to-model-order-book

    https://web.archive.org/web/20110219163448/http://howtohft.wordpress.com/2011/02/15/how-to-build-a-fast-limit-order-book/

    For each price point save a list of orders (in order of arrival).
    """
    def __init__(self):
        self.price_points = SortedDict() # Price: int -> PricePoint



class OrderBook:
    def __init__(self):
        self.history = deque()
        self.orders: dict[int, OrderBookEntry] = dict() # Maps order id -> order

        self.buy_book = OrderBookTree()
        self.sell_book = OrderBookTree()

    
    def process_order(self, order):
        # Add new order to books
        ...
