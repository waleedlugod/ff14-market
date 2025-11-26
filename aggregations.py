from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import OperationFailure

conn = MongoClient("mongodb://localhost:27017")
db = conn["market"]


def compute_sales_summary():
    pipeline = [
        {
            "$group": {
                "_id": "$itemName",
                "totalSold": {"$sum": "$amountSold"},
                "totalRevenue": {"$sum": {"$multiply": ["$amountSold", "$itemPrice"]}}
            }
        },
        {
            "$sort": {"totalSold": -1}
        }
    ]
    results = list(db["postingHistory"].aggregate(pipeline))

    total_sold_all = sum(r["totalSold"] for r in results)
    for r in results:
        r["totalSoldPercent"] = (
            r["totalSold"] / total_sold_all * 100) if total_sold_all else 0

    return results


def daily_trade_volume():
    """
    Returns a list of daily trade volumes as dictionaries:
    [{ "date": "YYYY-MM-DD", "volume": total_quantity_sold }, ...]
    """
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

    # Format output
    daily_volumes = [{"date": r["_id"], "volume": r["volume"]} for r in result]
    return daily_volumes


def price_volatility(trailing_hours: int = 24, min_sales: int = 2):
    """
    Compute Price Volatility Index (population standard deviation σ) per item
    over a trailing window (in hours).

    sigma = sqrt( sum( (pi - p_avg)^2 ) / N )

    Args:
      trailing_hours: lookback window in hours (default 24).
      min_sales: minimum number of sales required to include an item.

    Returns:
      List of dicts sorted by sigma desc:
      [{ "itemName": ..., "sigma": float, "avgPrice": float, "count": int }, ...]
    """
    cutoff = datetime.utcnow() - timedelta(hours=trailing_hours)

    # Try to use MongoDB's $stdDevPop. If the server/version doesn't support it,
    # fall back to fetching prices and computing sigma in Python.
    try:
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff}}},
            {
                "$group": {
                    "_id": "$itemName",
                    "avgPrice": {"$avg": "$itemPrice"},
                    "sigma": {"$stdDevPop": "$itemPrice"},
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gte": min_sales}}},
            {"$sort": {"sigma": -1}}
        ]
        agg = list(db["postingHistory"].aggregate(pipeline))

        results = []
        for r in agg:
            results.append({
                "itemName": r["_id"],
                "sigma": float(r["sigma"]) if r.get("sigma") is not None else 0.0,
                "avgPrice": float(r.get("avgPrice", 0.0)),
                "count": int(r.get("count", 0))
            })
        return results

    except OperationFailure:
        # Fallback: gather prices per item and compute sigma in Python
        pipeline = [
            {"$match": {"timestamp": {"$gte": cutoff}}},
            {
                "$group": {
                    "_id": "$itemName",
                    "prices": {"$push": "$itemPrice"},
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gte": min_sales}}}
        ]
        agg = list(db["postingHistory"].aggregate(pipeline))

        results = []
        for r in agg:
            prices = r.get("prices", [])
            n = len(prices)
            if n == 0:
                continue
            avg = sum(prices) / n
            variance = sum((p - avg) ** 2 for p in prices) / \
                n  # population variance
            sigma = variance ** 0.5
            results.append({
                "itemName": r["_id"],
                "sigma": float(sigma),
                "avgPrice": float(avg),
                "count": n
            })

        # sort by sigma descending
        results.sort(key=lambda x: x["sigma"], reverse=True)
        return results
