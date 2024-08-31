import logging
from datamodel import Listing, Order, Portfolio
from dataimport import read_file, extract_orders, extract_bot_orders
from ordermatching import match_order
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List
from examplealgo import Trader
from datetime import datetime


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Constants
FILE_PATH = "Round Data/Options/Option_round_test.csv"
BOT_FILE_PATH = "Round Data/Options/Option_round_test_bots.csv"
POSITION_LIMIT = 20
MAX_TICKS = 1000

def initialize_portfolio(products: List[str]) -> Portfolio:
    portfolio = Portfolio()
    for product in products:
        portfolio.quantity[product] = 0
    return portfolio

def add_bot_orders(orderbook: Dict[str, Dict], bot_orders: Dict[str, Dict]) -> None:
    """
    Add bot orders to the existing orderbook.
    
    :param orderbook: The current orderbook
    :param bot_orders: Bot orders in the same format as the orderbook
    """
    for product, sides in bot_orders.items():
        for side, pricepoints in sides.items():
            if product not in orderbook:
                orderbook[product] = {"BUY": {}, "SELL": {}}
            if side not in orderbook[product]:
                orderbook[product][side] = {}
            
            for price, quantity in pricepoints.items():
                if price in orderbook[product][side]:
                    orderbook[product][side][price] += quantity
                else:
                    orderbook[product][side][price] = quantity

def process_tick(tick: int, orderbook: Dict[str, Dict], algo: Trader, portfolio: Portfolio, products: List[str], pos_limit: Dict[str, int], bot_orders: Dict[str, Dict]) -> None:
    try:
        # Get orders from the trader 
        algo_orders = algo.run(orderbook, products)

        # Add bot orders to the orderbook
        add_bot_orders(orderbook, bot_orders)

        # Process algo orders
        if algo_orders:
            for order in algo_orders:
                # if order.is_valid():
                #     print(order)
                match_order(order, orderbook, portfolio, pos_limit)

        portfolio.pnl = portfolio.cash
        for product in products:
            portfolio.pnl += portfolio.quantity[product] * next(iter(orderbook[product]["SELL"]))
    except Exception as e:
        logging.error(f"Error processing tick {tick}: {str(e)}")

def update_quantity_data(quantity_data: pd.DataFrame, tick: int, portfolio: Portfolio, products: List[str]) -> None:
    quantity_data.loc[tick, "PnL"] = portfolio.pnl
    quantity_data.loc[tick, "Cash"] = portfolio.cash
    for product in products:
        quantity_data.loc[tick, f"{product}_quantity"] = portfolio.quantity[product]

def main():
    products, ticks, df = read_file(FILE_PATH)
    bot_df = pd.read_csv(BOT_FILE_PATH)
    
    portfolio = initialize_portfolio(products)
    pos_limit = {product: POSITION_LIMIT for product in products}

    quantity_data = pd.DataFrame(index=range(1, ticks), columns=[f"{product}_quantity" for product in products] + ["PnL", "Cash"])
    algo = Trader()

    start = datetime.now()
    for tick in range(1, MAX_TICKS):
        print(tick)
        orderbook = {product: extract_orders(df, tick, product) for product in products}
        bot_orders = {product: extract_bot_orders(bot_df, tick, product) for product in products}
        process_tick(tick, orderbook, algo, portfolio, products, pos_limit, bot_orders)
        update_quantity_data(quantity_data, tick, portfolio, products)

    end = datetime.now()
    print(f"Time per tick: {(end-start)/MAX_TICKS}")
    print(quantity_data)

    # Plotting
    quantity_data["PnL"].plot(legend=True)
    quantity_data["Cash"].plot(legend=True)
    plt.show()

if __name__ == "__main__":
    main()