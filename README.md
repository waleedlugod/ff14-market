# ff14-market

### Generate Data

Run `generate_data.py` to pull data from the Universalis API

If `history.json` or `postings.json` already has data, you don't need to run the script

### Insert Data

Run `insert.py` to insert the json data into your mongodb database (make sure to change the `HOST` value in the file)


# MarketBoard

MarketBoard interface made using Flask, MongoDB, and JavaScript. 

---

## Features

- Add new items for sale and track details (name, price, quantity, seller).  
- Add sales history entries (buyer, item, price, quantity).  
- Sort sales history by **latest** or **oldest** timestamp.  
- Delete items or sales history entries.  
- Search and filter items or history in real-time.    

---

## Setup

1. **Install Python dependencies**

```
pip install flask flask-cors pymongo
```

2. **Install MongoDB (macOS)**

```
brew tap mongodb/brew
brew install mongodb-community@7.0
```

3. **Start the Flask app**
```
python3 MarketBoard.py
```

4.  **Now you can drag your index.html into your browser and the data should load.**

---

## Pictures

![Selling Items](pictures/img2.png)
- Items for sale.

![Trade History Items](pictures/img3.png)
- Trade history by various users.

![Adding entrys](pictures/img4.png)
- Creating new entries.

![Adding entrys](pictures/img1.png)
- Filter to find items.

