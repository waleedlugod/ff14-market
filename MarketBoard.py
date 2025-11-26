from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import json
import insert
from aggregations import compute_sales_summary, daily_trade_volume, price_volatility

HOST = "mongodb://localhost:27017"

MarketBoard = Flask(__name__)
CORS(MarketBoard)

conn = MongoClient(HOST)
db = conn["market"]


@MarketBoard.route("/")
def home():
    return send_from_directory('.', 'index.html')


def load_data():
    if "postings" not in db.list_collection_names():
        with open("postings.json") as f:
            postings = json.load(f)
        db["postings"].insert_many(postings)

    if "postingHistory" not in db.list_collection_names():
        with open("history.json") as f:
            sales_history = json.load(f)
        sales_history = [
            {**entry, "timestamp": datetime.fromisoformat(entry["timestamp"])}
            for entry in sales_history
        ]
        db["postingHistory"].insert_many(sales_history)


load_data()


@MarketBoard.route("/postings")
def get_items():
    search_query = request.args.get("search", "").strip()

    if search_query:
        items = list(db["postings"].find({
            "itemName": {"$regex": search_query, "$options": "i"},
            "itemQuantity": {"$gt": 0}
        }))
    else:
        items = list(db["postings"].find({"itemQuantity": {"$gt": 0}}))

    # items = list(db["postings"].find())
    for i in items:
        i["_id"] = str(i["_id"])
        if isinstance(i.get("timestamp"), datetime):
            i["timestamp"] = i["timestamp"].isoformat()
    return jsonify(items)


@MarketBoard.route("/history")
def get_history():
    history = list(db["postingHistory"].find())
    for h in history:
        h["_id"] = str(h["_id"])
        if isinstance(h.get("timestamp"), datetime):
            h["timestamp"] = h["timestamp"].isoformat()
    return jsonify(history)


@MarketBoard.route("/buy", methods=["POST"])
def buy():
    data = request.json
    itemID = data["itemID"]
    quantity = data["quantity"]
    buyer = data["buyer"]

    obj_id = ObjectId(itemID)
    item = db["postings"].find_one(
        {"_id": obj_id, "quantity": {"$gte": quantity}})
    if not item:
        return jsonify({"success": False, "message": "Not enough quantity"}), 400

    db["postings"].update_one(
        {"_id": obj_id}, {"$inc": {"quantity": -quantity}})
    history_entry = {
        "timestamp": datetime.now(),
        "itemName": item["itemName"],
        "itemPrice": item["itemPrice"],
        "amountSold": quantity,
        "userCustomer": buyer
    }
    db["postingHistory"].insert_one(history_entry)
    return jsonify({"success": True})


@MarketBoard.route("/add", methods=["POST"])
def add_item_endpoint():
    data = request.json
    try:
        item = {
            "itemName": data["itemName"],
            "itemPrice": float(data["itemPrice"]),
            "itemQuantity": int(data["itemQuantity"]),
            "timestamp": datetime.now()
        }
        db["postings"].insert_one(item)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@MarketBoard.route("/add_history", methods=["POST"])
def add_history_endpoint():
    data = request.json
    try:
        entry = {
            "timestamp": datetime.now(),
            "itemName": data["itemName"],
            "itemPrice": float(data["itemPrice"]),
            "amountSold": int(data["amountSold"]),
            "userCustomer": data["userCustomer"]
        }
        db["postingHistory"].insert_one(entry)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@MarketBoard.route("/delete", methods=["POST"])
def delete_item_endpoint():
    data = request.json
    itemID = data.get("itemID")
    if not itemID:
        return jsonify({"success": False, "message": "Missing itemID"}), 400
    try:
        db["postings"].delete_one({"_id": ObjectId(itemID)})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@MarketBoard.route("/delete_history", methods=["POST"])
def delete_history_endpoint():
    data = request.json
    entryID = data.get("entryID")
    if not entryID:
        return jsonify({"success": False, "message": "Missing entryID"}), 400
    try:
        db["postingHistory"].delete_one({"_id": ObjectId(entryID)})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@MarketBoard.route("/daily_volume")
def get_daily_volume():
    volumes = daily_trade_volume()
    return jsonify(volumes)


@MarketBoard.route("/sales_summary")
def get_sales_summary():
    summary = compute_sales_summary()
    return jsonify(summary)


@MarketBoard.route("/price_volatility")
def get_price_volatility():
    # optional query params: trailing_hours and min_sales
    try:
        trailing_hours = int(request.args.get("trailing_hours", 24))
    except (TypeError, ValueError):
        trailing_hours = 24
    try:
        min_sales = int(request.args.get("min_sales", 2))
    except (TypeError, ValueError):
        min_sales = 2

    # compute cutoff for debugging
    cutoff = datetime.utcnow() - timedelta(hours=trailing_hours)

    # call aggregation
    volatility = price_volatility(
        trailing_hours=trailing_hours, min_sales=min_sales)

    # if empty, return debug information to help diagnose
    if not volatility:
        # count matching documents in the time window
        matches = db["postingHistory"].count_documents(
            {"timestamp": {"$gte": cutoff}})
        # return a small sample of documents in that window (convert timestamps to ISO)
        sample_cursor = db["postingHistory"].find(
            {"timestamp": {"$gte": cutoff}}).limit(10)
        sample = []
        for doc in sample_cursor:
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()
            sample.append(doc)

        return jsonify({
            "volatility": volatility,
            "debug": {
                "trailing_hours": trailing_hours,
                "min_sales": min_sales,
                "cutoff": cutoff.isoformat(),
                "matching_docs": matches,
                "sample": sample,
                "note": "No volatility rows computed — check timestamps/fields and that there are at least `min_sales` sales per item in the window."
            }
        })

    return jsonify(volatility)


if __name__ == "__main__":
    MarketBoard.run(debug=True)
