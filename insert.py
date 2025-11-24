import os
import json
from pymongo import *
from dotenv import load_dotenv
import requests as r


ITEM_TYPES_CNT = 2

item_types = [
    str(_)
    for _ in r.get("https://universalis.app/api/v2/marketable").json()[:ITEM_TYPES_CNT]
]

f = open("test.json", "w")
json.dump(
    r.get(
        f"https://universalis.app/api/v2/Excalibur/{','.join(item_types)}?fields=itemID,items.listings.pricePerUnit,items.listings.quantity,items.listings.retainerCity,items.listings.retainerName,currentAveragePrice,averagePrice,minPrice,maxPrice"
    ).json(),
    f,
)

# load_dotenv()
# HOST = os.getenv("HOST")

# conn = MongoClient(HOST)
# db = conn["market"]

# userPostings = db["userPostings"]
# postingHistory = db["postingHistory"]

# conn.close()
