import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orderbook.orderbook import Order, OrderDirection
from time import time


test_order = Order(1, time(), OrderDirection.BUY, 1000, 5)

print(test_order)