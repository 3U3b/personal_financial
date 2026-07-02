from config import BLACKLIST
from config import WATCHLIST
from config import HEADERS
import requests
import json
import os
from pathlib import Path

try:
    current_dir = Path(__file__).resolve().parent
except NameError:
    current_dir = Path.cwd().resolve()

STATE_FILE = current_dir / "state.json"

def get_market():
    url = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        # 取最後一筆（大盤）
        last = data[-1]

        return {
            "index": last.get("收盤指數", "-"),
            "change": last.get("漲跌", "-"),
            "pct": last.get("漲跌百分比", "-"),
            "date": last.get("日期", "-")
        }
    except:
        return {"index": "-", "change": "-", "pct": "-", "date": "-"}
        
def get_stock(stock_id):
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        rows = [x for x in data if x["Code"] == stock_id]

        if not rows:
            return None

        last = rows[-1]

        return {
            "code": stock_id,
            "name": last.get("Name"),
            "close": float(last.get("ClosingPrice", 0)),
            "volume": last.get("TradeVolume", "-"),
            "change": last.get("Change", "-")
        }

    except:
        return None
        
        
def get_fundamentals(stock_id):
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        rows = [x for x in data if x["Code"] == stock_id]
        if not rows:
            return None

        last = rows[-1]

        return {
            "pe": last.get("PEratio"),
            "yield": last.get("DividendYield"),
            "pb": last.get("PBratio")
        }

    except:
        return None
        


def load_state():
    if not os.path.exists(STATE_FILE):
        return []
    try:
        return json.load(open(STATE_FILE, "r", encoding="utf-8"))
    except:
        return []


def save_state(state):
    json.dump(state[-300:], open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def get_news():
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        history = load_state()
        new_state = list(history)

        result = []

        for item in data:
            
            if item["公司代號"] not in WATCHLIST:
                continue
    
            uid = f"{item.get('公司代號')}_{item.get('發言日期')}_{item.get('發言時間')}"

            if uid in history:
                continue

            text = item.get("主旨 ", "")  # 注意 TWSE 有空白
            
            if any(b in text for b in BLOCK_KEYWORDS):
                continue

            if not any(k in text for k in ALLOW_KEYWORDS):
                continue

            new_state.append(uid)

            result.append({
                "company": item.get("公司名稱"),
                "title": text
            })
            

                
            if len(result) >= 5:
                break

        save_state(new_state)
        return result

    except:
        return []
        
def get_etf(etf="0050"):
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        rows = [x for x in data if x["Code"] == etf]
        if not rows:
            return None

        last = rows[-1]

        return {
            "price": last.get("ClosingPrice"),
            "volume": last.get("TradeVolume")
        }

    except:
        return None