from datamodel import *
from dataimport import *
from Runscript import *
from datetime import datetime
import matplotlib.pyplot as plt

class Portfolio:
    def __init__(self) -> None:
        self.cash = 0
        self.quantity = 0

portfolio = Portfolio()

filepath = "prices_round_1_day_-1.csv"
product = "AMETHYSTS"
pos_limit = 20
df = read_file(filepath, product)
ticks = len(df)

from examplealgo import Trader

vis = []
start = datetime.now()
for tick in range(0, ticks):
    #print(tick)
    market_listings = extract_orders(df, tick)
    sell_orders = market_listings[1]
    buy_orders = market_listings[0]

    algo = Trader()
    orders = algo.run(market_listings)
    if orders != []:
        bid_prices = list(buy_orders.keys()) # market buy orders aka the price we can sell at
        bid_quantities = list(buy_orders.values())
        bid_quantities = [value.iloc[0] for value in bid_quantities]

        ask_prices = list(sell_orders.keys())
        ask_quantities = list(sell_orders.values())
        ask_quantities = [value.iloc[0] for value in ask_quantities]

        # order matching
        for order in orders: 
            if order.quantity < 0: # Selling
                #match order with a buy order
                quantity = order.quantity
                for i in range(len(buy_orders)):
                    if bid_quantities[i] > 0:
                        if bid_prices[i] >= order.price:
                            fulfilled_amount = min(int(pos_limit + portfolio.quantity), -quantity, bid_quantities[i]) #quantity before order limit, order quantity remaining, quantity avaliable, 
                            portfolio.quantity -= fulfilled_amount
                            bid_quantities[i] -= fulfilled_amount
                            portfolio.cash += fulfilled_amount * bid_prices[i]
                            quantity += fulfilled_amount
                            #print(f"selling {fulfilled_amount} at {buy_prices[i]}")
                    if quantity == 0 or bid_prices[i] < order.price:
                        break
                    #print(f"quantity left = {quantity}")

            elif order.quantity > 0: # Buying
                quantity = order.quantity
                for i in range(0,len(sell_orders)):
                    if ask_quantities[i] > 0:
                        #print(f"sell price = {sell_prices[i]}, our order = {order.price}")
                        if ask_prices[i] <= order.price:
                            #print(f"Quantity at {sell_prices[i]} = {sell_quantities[i]}")
                            fulfilled_amount = min(int(pos_limit - portfolio.quantity), quantity, ask_quantities[i])
                            #print(f"ffd amt:{fulfilled_amount} out of qty: {quantity}")
                            portfolio.quantity += fulfilled_amount
                            ask_quantities[i] -= fulfilled_amount
                            portfolio.cash -= fulfilled_amount * ask_prices[i]
                            quantity -= fulfilled_amount
                            #print(f"buying {fulfilled_amount} at {sell_prices[i]}")
                    if quantity == 0 or ask_prices[i] > order.price:
                        break
    midprice = (bid_prices[0] + ask_prices[0]) /2
    pnl = portfolio.cash + (midprice* portfolio.quantity)

    vis.append(pnl)
    #vis.append(portfolio.quantity)

end = datetime.now()

# roughly 0:00:00.001054 per tick
# roughly 10 seconds per day
# 9.35
# 3 seconds with no printing
print((end-start))

print(portfolio.quantity)
plt.plot(vis)
plt.show()