from enum import Enum

class OrderType(Enum):
    BUY = 1
    SELL = 2

    def __str__(self):
        if self.value == 1:
            return "BUY"
        elif self.value == 2:
            return "SELL"


class OrderBookEntry:
    """
    id, 
    timestamp (utc) use time.time(), 
    type (buy/sell), 
    price, 
    size
    """
    def __init__(self, id : int, timestamp : float, type : OrderType, price : float, quantity : float):
        self.id = id
        self.timestamp = timestamp
        self.type = type
        self.price = price
        self.quantity = quantity
    

    def __str__(self):
        return f"{self.type} {self.quantity}@{self.price} [{self.id}; {self.timestamp}]" 