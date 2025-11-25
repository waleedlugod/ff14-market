from pymongo import *
import json
from datetime import datetime

### change to appropriate value
HOST = "mongodb://localhost:27018"

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
