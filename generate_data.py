import os
import json
from pymongo import *
from dotenv import load_dotenv
import requests as r


ITEM_TYPES_CNT = 100

# query for marketable items
item_types = [
    str(_)
    for _ in r.get("https://universalis.app/api/v2/marketable").json()[:ITEM_TYPES_CNT]
]
# query for the names of each item
item_names = {
    str(item["row_id"]): item["fields"]["Name"]
    for item in r.get(
        f"https://v2.xivapi.com/api/sheet/Item?rows={','.join(item_types)}&fields=Name"
    ).json()["rows"]
}

# query for the current market board for items
res = r.get(
    f"https://universalis.app/api/v2/Excalibur/{','.join(item_types)}?fields=itemID,items.listings.pricePerUnit,items.listings.quantity,items.listings.retainerCity,items.listings.retainerName,items.currentAveragePrice,items.averagePrice,items.minPrice,items.maxPrice"
).json()


# create document
postings = []
for item in res["items"]:
    for listing in res["items"][item]["listings"]:
        document = {
            "itemName": item_names[item],
            "itemPrice": listing["pricePerUnit"],
            "itemQuantity": listing["quantity"],
        }
        postings.append(document)
f = open("postings.json", "w")
json.dump(postings, f)


# conn = MongoClient(HOST)
# db = conn["market"]

# postings = db["postings"]
# postingHistory = db["postingHistory"]

# conn.close()
