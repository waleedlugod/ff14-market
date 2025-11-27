from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import OperationFailure
from math import *
import numpy as np

conn = MongoClient("mongodb://localhost:27017")
db = conn["market"]


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


def demand_stability_score(itemName):
    try:
        pipeline = [
            {"$match": {"itemName": itemName}},
            {"$project": {"date": {"$dateToString": {
                "format": "%Y-%m-%d", "date": "$timestamp"}}, "amountSold": 1}},
            {"$group": {"_id": "$date", "volume": {"$sum": "$amountSold"}}},
            {"$sort": {"_id": 1}}
        ]
        agg = list(db["postingHistory"].aggregate(pipeline))
        daily = [{"date": r["_id"], "volume": int(
            r.get("volume", 0))} for r in agg]
        if not daily:
            return {"item": itemName, "score": 0.0, "daily": []}
        volumes = [d["volume"] for d in daily]
        score = float(np.std(volumes))
        return {"item": itemName, "score": score, "daily": daily}
    except OperationFailure as e:
        print(f"MongoDB aggregation failed: {e}")
        return {"item": itemName, "score": 0.0, "daily": []}
