from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import json
import insert
from analyticsAgg import daily_trade_volume, item_price_statistics

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


@MarketBoard.route("/item_price_stats")
def get_item_price_stats():
    try:
        stats = item_price_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    MarketBoard.run(debug=True)
