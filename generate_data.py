import json
import requests as r
from datetime import datetime


ITEM_TYPES_CNT = 100
SALES_ENTRIES_CNT = 1000

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


# generate postings data
def generate_postings():
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


# generate postings history data
def generate_sales():
    # query for recent sales history
    # past_month = datetime(datetime.now().year, datetime.now().month - 1, 1)
    res = r.get(
        f"https://universalis.app/api/v2/history/Excalibur/{','.join(item_types)}?entriesToReturn={SALES_ENTRIES_CNT}"
    ).json()

    # create document
    history = []
    for item in res["items"]:
        for entry in res["items"][item]["entries"]:
            document = {
                "timestamp": str(datetime.fromtimestamp(entry["timestamp"])),
                "itemName": item_names[item],
                "itemPrice": entry["pricePerUnit"],
                "amountSold": entry["quantity"],
                "userCustomer": entry["buyerName"],
            }
            history.append(document)
    f = open("history.json", "w")
    json.dump(history, f)


if __name__ == "__main__":
    generate_postings()
    generate_sales()
