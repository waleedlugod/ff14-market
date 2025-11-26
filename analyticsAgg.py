from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import OperationFailure
from math import *
import numpy as np

conn = MongoClient("mongodb://localhost:27017")
db = conn["market"]


def compute_sales_summary():
    pipeline = [
        {
            "$group": {
                "_id": "$itemName",
                "totalSold": {"$sum": "$amountSold"},
                "totalRevenue": {"$sum": {"$multiply": ["$amountSold", "$itemPrice"]}},
            }
        },
        {"$sort": {"totalSold": -1}},
    ]
    results = list(db["postingHistory"].aggregate(pipeline))

    total_sold_all = sum(r["totalSold"] for r in results)
    for r in results:
        r["totalSoldPercent"] = (
            (r["totalSold"] / total_sold_all * 100) if total_sold_all else 0
        )

    return results


def item_price_statistics():
    pipeline = [
        {
            "$group": {
                "_id": "$itemName",
                "highestPrice": {"$max": "$itemPrice"},
                "lowestPrice": {"$min": "$itemPrice"},
                "averagePrice": {"$avg": "$itemPrice"},
                "totalTransactions": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    try:
        results = list(db["postingHistory"].aggregate(pipeline))
        return results
    except OperationFailure as e:
        print(f"MongoDB aggregation failed: {e}")
        return []


### NEW STATISTICAL FEATURES
def price_volatility_index(itemName):
    pipeline = [
        {"$match": {"itemName": itemName}},
        {
            "$group": {
                "_id": "$itemName",
                "averagePrice": {"$avg": "$itemPrice"},
                "totalTransactions": {"$sum": 1},
            }
        },
    ]
    try:
        agg_stats = list(db["postingHistory"].aggregate(pipeline))[0]
        history = list(db["postingHistory"].find({"itemName": itemName}))
        prices = [entry["itemPrice"] for entry in history]
        sum = 0
        for p in prices:
            sum += (p - agg_stats["averagePrice"]) ** 2
        pvi = sqrt(sum / (agg_stats["totalTransactions"] - 1))
        return pvi
    except OperationFailure as e:
        print(f"MongoDB aggregation failed: {e}")
        return []


def daily_trade_volume():
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "volume": {"$sum": "$amountSold"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    result = list(db["postingHistory"].aggregate(pipeline))

    daily_volumes = [{"date": r["_id"], "volume": r["volume"]} for r in result]
    return daily_volumes


def price_velocity():
    pass


def weighted_moving_average(itemName):
    pass


def volume_weight_price_volatility():
    pass


def buy_pressure_index():
    pass


def price_acceleration():
    pass


def demand_stability_score():
    volumes = [day["volume"] for day in daily_trade_volume()]
    return np.std(volumes)
