from datamodel import *
from dataimport import *
from Runscript import *
from datetime import datetime

"""
we only trade one good in each round
initialise portfolio with 100k
    quantity = 0
    value = 100,000
    

for each timestamp,

    for each product at that time stamp,
        set the listing price, quantity, symbol

    run the trader class
    for each order:
        check that the price and direction exists:
            check that order is not greater than quantity avaliable
        
                update portfolio with outcome
"""
class Portfolio:
    def __init__(self) -> None:
        self.cash = 100000
        self.quantity = 0

portfolio = Portfolio()

filepath = "trading comp\prices_round_1_day_-1.csv"
product = "AMETHYSTS"
pos_limit = 20
df = read_file(filepath, product)
ticks = len(df)
# for each trader id in list
#from trader_id import Trader

from examplealgo import Trader

start = datetime.now()
for tick in range(0, ticks):
    market_listings = extract_orders(df, tick)
    sell_orders = market_listings[1]
    buy_orders = market_listings[0]

    algo = Trader()
    orders = algo.run(market_listings)
    # order matching
    for order in orders: ### market listing still exists so woudl be vulnerable to someon just sending hundreds of orders
        if order.quantity < 0: # sell orders
            #match order with a buy order
            quantity = order.quantity ###################### listing is not an object, figure out how to get the listing's price and quantity
            for listing in buy_orders:
                print("---")
                print(pos_limit - abs(portfolio.quantity))
                print(order.quantity)
                print(buy_orders[listing].iloc[0])
                print("---")
                if listing > order.price:
                    fulfilled_amount = min(int(pos_limit - abs(portfolio.quantity)), -order.quantity, buy_orders[listing].iloc[0])
                    print(fulfilled_amount)
                    portfolio.quantity -= fulfilled_amount
                    portfolio.cash += fulfilled_amount * order.price
                    quantity += fulfilled_amount
                if quantity == 0 or listing < order.price:
                    print("OUT")
                    break
                print(f"quantity left = {quantity}")
        elif order.quantity > 0: # buy orders
            pass
    # portfolio tracking
    break

end = datetime.now()

print(end-start)

print(portfolio.quantity)
    