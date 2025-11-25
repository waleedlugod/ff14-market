from pymongo import *
import json
from datetime import datetime

### change to appropriate value
HOST = "mongodb://localhost:27018"


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
