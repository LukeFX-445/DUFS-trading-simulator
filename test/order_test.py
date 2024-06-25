import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orderbook.orderbook import OrderBookEntry, OrderType
from time import time

test_order = OrderBookEntry(1, time(), "AAPL", OrderType.BUY, 1000, 5)

print(test_order)