import requests, json
from pathlib import Path

try:
    current_dir = Path(__file__).resolve().parent
except NameError:
    current_dir = Path.cwd().resolve()

BASE = "https://openapi.twse.com.tw/v1"
STATE_FILE = current_dir / "state.json"
WATCHLIST = ["2330", "2317", "2454"]
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -------------------
# STATE ENGINE (FIXED)
# -------------------
def load_state():
    if not STATE_FILE.exists():
        return set()
    try:
        return set(json.load(open(STATE_FILE, "r", encoding="utf-8")))
    except:
        return set()

def save_state(state):
    json.dump(list(state)[-500:], open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False)

# -------------------
# MARKET
# -------------------
def get_market():
    r = requests.get(BASE + "/exchangeReport/MI_INDEX", headers=HEADERS).json()
    last = r[-1]
    return {
        "index": last.get("收盤指數"),
        "change": last.get("漲跌"),
        "date": last.get("日期")
    }

# -------------------
# STOCK
# -------------------
def get_stock(code):
    r = requests.get(BASE + "/exchangeReport/STOCK_DAY_ALL", headers=HEADERS).json()
    rows = [x for x in r if x["Code"] == code]
    if not rows:
        return None

    last = rows[-1]
    return {
        "code": code,
        "name": last["Name"],
        "close": float(last["ClosingPrice"]),
        "volume": int(last["TradeVolume"]),
        "change": last["Change"]
    }

# -------------------
# FLOW (BUY/SELL PRESSURE)
# -------------------
def get_flow():
    r = requests.get(BASE + "/exchangeReport/MI_5MINS", headers=HEADERS).json()[0]

    bid = int(r.get("AccBidVolume", 0))
    ask = int(r.get("AccAskVolume", 0))

    return {
        "bid": bid,
        "ask": ask,
        "pressure": bid - ask
    }

# -------------------
# ETF
# -------------------
def get_etf():
    r = requests.get(BASE + "/exchangeReport/STOCK_DAY_ALL", headers=HEADERS).json()
    rows = [x for x in r if x["Code"] == "0050"]
    if not rows:
        return None

    last = rows[-1]
    return {
        "price": float(last["ClosingPrice"]),
        "volume": int(last["TradeVolume"])
    }