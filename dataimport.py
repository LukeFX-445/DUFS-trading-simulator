import pandas as pd
from typing import Dict

def extract_orders(df: pd.DataFrame, tick: int, product: str) -> Dict[str, Dict[float, int]]:
    """
    Create an orderbook for the specified tick from dataframe.
    If no data exists for that tick/product, return empty books.
    """
    row = df[(df["timestamp"] == tick * 100) & (df["product"] == product)]

    bid_orders: Dict[float, int] = {}
    ask_orders: Dict[float, int] = {}

    if row.empty:
        return {"BUY": bid_orders, "SELL": ask_orders}

    row = row.iloc[0]

    for i in range(1, 4):
        price_col = f"bid_price_{i}"
        vol_col = f"bid_volume_{i}"
        if price_col in row and vol_col in row:
            price = row[price_col]
            vol = row[vol_col]
            if pd.notna(price) and pd.notna(vol) and vol != 0:
                bid_orders[float(price)] = int(vol)

    for i in range(1, 4):
        price_col = f"ask_price_{i}"
        vol_col = f"ask_volume_{i}"
        if price_col in row and vol_col in row:
            price = row[price_col]
            vol = row[vol_col]
            if pd.notna(price) and pd.notna(vol) and vol != 0:
                ask_orders[float(price)] = int(vol)

    return {"BUY": bid_orders, "SELL": ask_orders}


def extract_bot_orders(df: pd.DataFrame, tick: int, product: str) -> Dict[str, Dict[float, int]]:
    """
    Create an orderbook for the specified tick from bot order dataframe.
    If no data exists for that tick/product, return empty books.
    """
    row = df[(df["timestamp"] == tick * 100) & (df["product"] == product)]

    bid_orders: Dict[float, int] = {}
    ask_orders: Dict[float, int] = {}

    if row.empty:
        return {"BUY": bid_orders, "SELL": ask_orders}

    row = row.iloc[0]

    if "bid_price_1" in row and "bid_volume_1" in row:
        bid_price = row["bid_price_1"]
        bid_volume = row["bid_volume_1"]
        if pd.notna(bid_price) and pd.notna(bid_volume) and bid_volume > 0:
            bid_orders[float(bid_price)] = int(bid_volume)

    if "ask_price_1" in row and "ask_volume_1" in row:
        ask_price = row["ask_price_1"]
        ask_volume = row["ask_volume_1"]
        if pd.notna(ask_price) and pd.notna(ask_volume) and ask_volume > 0:
            ask_orders[float(ask_price)] = int(ask_volume)

    return {"BUY": bid_orders, "SELL": ask_orders}
