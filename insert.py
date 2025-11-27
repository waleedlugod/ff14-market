from pymongo import *
import json
from datetime import datetime

# change to appropriate value
HOST = "mongodb://localhost:27017"


def create_posting(db, posting: dict):
    return db["postings"].insert_one(posting)


def create_history(db, entry: dict):
    entry = {**entry, "timestamp": datetime.fromisoformat(entry["timestamp"])}
    return db["postingHistory"].insert_one(entry)


def delete_posting(db, item: dict):
    return db["postings"].delete_one(item)


def delete_many_postings(db, items: dict):
    return db["postings"].delete_many(items)


def delete_history_entry(db, user_entry: dict):
    return db["postingHistory"].delete_one(user_entry)


def add_item(db, username, title, price, quantity):
    item = {
        "itemID": str(datetime.now().timestamp()),
        "username": username,
        "title": title,
        "price": price,
        "quantity": quantity,
        "timestamp": datetime.now()
    }
    return create_posting(db, item)


def update_item(db, username, itemID, title=None, price=None, quantity=None):
    update_fields = {}
    if title:
        update_fields["title"] = title
    if price:
        update_fields["price"] = price
    if quantity:
        update_fields["quantity"] = quantity
    return db["postings"].update_one({"itemID": itemID, "username": username}, {"$set": update_fields})


def list_all_items(db):
    return list(db["postings"].find({"quantity": {"$gt": 0}}).sort("price", 1))


def list_recent_items(db):
    return list(db["postings"].find({"quantity": {"$gt": 0}}).sort("timestamp", -1))


def list_user_items(db, username):
    return list(db["postings"].find({"username": username}).sort("timestamp", -1))


def remove_item(db, username, itemID):
    return delete_posting(db, {"itemID": itemID, "username": username})


def buy_item(db, buyer_username, itemID, quantity):
    item = db["postings"].find_one(
        {"itemID": itemID, "quantity": {"$gte": quantity}})
    if not item:
        return False

    db["postings"].update_one(
        {"itemID": itemID}, {"$inc": {"quantity": -quantity}})

    history_entry = {
        "timestamp": datetime.now(),
        "itemName": item["title"],
        "itemPrice": item["price"],
        "amountSold": quantity,
        "userCustomer": buyer_username
    }
    create_history(db, history_entry)
    return True


def get_sales_history(db):
    return list(db["postingHistory"].find().sort("timestamp", -1))


if __name__ == "__main__":
    # insert into database
    conn = MongoClient(HOST)
    if "market" in conn.list_database_names():
        conn.drop_database("market")
    db = conn["market"]

    f = open("postings.json")
    postings = json.load(f)
    db["postings"].insert_many(postings)

    f = open("history.json")
    sales_history = json.load(f)
    sales_history = [
        {**entry, "timestamp": datetime.fromisoformat(entry["timestamp"])}
        for entry in sales_history
    ]
    db["postingHistory"].insert_many(sales_history)

    conn.close()
