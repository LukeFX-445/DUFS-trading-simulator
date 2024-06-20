#Import data from CSV orderbook
# define class for each day
#    day needs to contain each price and corresponding quantity

import pandas as pd
def read_file(file_path, product):
    df = pd.read_csv(file_path,sep=";")
    df = df[df['product'] == product]
    return df

# def read_file(file_path, product):
#     df = pd.read_csv(file_path)
#     df = df[df['product'] == product]
#     return df


def extract_orders(df, tick):
    row = df[df["timestamp"] == tick*100]
    bid_orders = {} #price:quantity pairs
    ask_orders = {} #price:quantity pairs
    for i in range(1, 4):
        price = row[f"bid_price_{i}"].iloc[0]
        bid_orders[price] = row[f"bid_volume_{i}"]
    for i in range(1,4):
        price = row[f"ask_price_{i}"].iloc[0]
        ask_orders[price] = row[f"ask_volume_{i}"]
    
    return [bid_orders, ask_orders]