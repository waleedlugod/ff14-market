from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import OperationFailure

conn = MongoClient("mongodb://localhost:27017")
db = conn["market"]


def daily_trade_volume():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "volume": {"$sum": "$amountSold"}
            }
        },
        {"$sort": {"_id": 1}}
    ]

    result = list(db["postingHistory"].aggregate(pipeline))

    daily_volumes = [{"date": r["_id"], "volume": r["volume"]} for r in result]
    return daily_volumes


def item_price_statistics():
    pipeline = [
        {
            "$group": {
                "_id": "$itemName",
                "highestPrice": {"$max": "$itemPrice"},
                "lowestPrice": {"$min": "$itemPrice"},
                "averagePrice": {"$avg": "$itemPrice"},
                "totalTransactions": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    try:
        results = list(db["postingHistory"].aggregate(pipeline))
        return results
    except OperationFailure as e:
        print(f"MongoDB aggregation failed: {e}")
        return []
