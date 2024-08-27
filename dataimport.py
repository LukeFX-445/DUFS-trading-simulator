import pandas as pd

def read_file(file_path):
    df = pd.read_csv(file_path)
    return df

def extract_orders(df, tick, product):
    row = df[df["timestamp"] == tick*100]
    row = row[row["product"] == product]
    bid_orders = {} #price:quantity pairs
    ask_orders = {} #price:quantity pairs
    for i in range(1, 4):
        price = row[f"bid_price_{i}"].iloc[0]
        bid_orders[price] = row[f"bid_volume_{i}"]
    for i in range(1, 4):
        price = row[f"ask_price_{i}"].iloc[0]
        ask_orders[price] = row[f"ask_volume_{i}"]
    
    return [bid_orders, ask_orders]