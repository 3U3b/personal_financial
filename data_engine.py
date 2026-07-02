import requests
import json
import time
import datetime
from pathlib import Path

try:
    current_dir = Path(__file__).resolve().parent
except NameError:
    current_dir = Path.cwd().resolve()

BASE = "https://openapi.twse.com.tw/v1"
STATE_FILE = current_dir / "state.json"
WATCHLIST = ["2330", "2317", "2454"]
ETF_CODE = "0050"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 💡 V3.1 核心：加入內建時間戳記的生存時間 (TTL) 快取架構
_CACHE = {"stocks": None, "ts": 0}
CACHE_TTL = 60  # 60 秒緩衝，防高頻併發打爆 API，同時兼顧每小時/每分鐘盤中即時性


# -------------------
# 🧩 LAYER 1 — DATA LAYER (WITH CACHE TTL)
# -------------------
def _preload_market_data():
    global _CACHE
    now = time.time()
    
    # 如果快取存在且未超過 60 秒，直接從記憶體回傳，拒絕無謂的網路開銷
    if _CACHE["stocks"] and (now - _CACHE["ts"] < CACHE_TTL):
        return _CACHE["stocks"]
        
    try:
        url = f"{BASE}/exchangeReport/STOCK_DAY_ALL"
        r = requests.get(url, headers=HEADERS, timeout=10)
        _CACHE["stocks"] = r.json()
        _CACHE["ts"] = now
    except Exception as e:
        print(f"⚠️ 預載證交所 OpenAPI 異常: {e}")
        if _CACHE["stocks"] is None:
            _CACHE["stocks"] = []
            
    return _CACHE["stocks"]


# -------------------
# 🧩 LAYER 2 — STATEFUL ENGINE (真正有意義的狀態差分持久化)
# -------------------
def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}


def save_state(state_dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, ensure_ascii=False, indent=4)


# -------------------
# 🧩 LAYER 3 — NORMALIZED ENGINE & SIGNAL DETECTION
# -------------------
def get_stock(code):
    all_data = _preload_market_data()
    rows = [x for x in all_data if x.get("Code") == code]
    if not rows:
        return None

    last = rows[-1]
    curr_close = float(last.get("ClosingPrice", 0)) if last.get("ClosingPrice") else 0.0
    curr_volume = int(last.get("TradeVolume", 0)) if last.get("TradeVolume") else 0
    
    # 載入上一次歷史狀態，進行「差分信號比對 (Event & Signal Tracking)」
    history = load_state()
    stock_hist = history.get(code, {})
    
    prev_close = stock_hist.get("last_close", curr_close)
    prev_volume = stock_hist.get("last_volume", curr_volume)
    
    # 💡 訊號演算法一：量能暴增偵測 (Volume Spike) -> 當前成交量超越上次 1.5 倍
    volume_spike = "🔥 量能異常爆發" if curr_volume > (prev_volume * 1.5) and prev_volume > 0 else "⚪ 均量穩定"
    
    # 💡 訊號演算法二：價差突破偵測 (Price Breakout)
    price_signal = "🔺 動能轉強" if curr_close > prev_close else "🔻 動能轉弱" if curr_close < prev_close else "⚪ 盤整"
    
    # 更新當前快照到狀態記憶體中，交由自動化工作流 Push 持久化
    history[code] = {
        "last_close": curr_close,
        "last_volume": curr_volume,
        "last_signal": price_signal,
        "updated_at": str(datetime.datetime.now())
    }
    save_state(history)

    return {
        "type": "stock",
        "code": code,
        "name": last.get("Name", "未知名稱"),
        "close": curr_close,
        "volume": curr_volume,
        "change": last.get("Change", "0.0"),
        "signals": {
            "momentum": price_signal,
            "volume_spike": volume_spike
        }
    }


# -------------------
# 🧩 LAYER 4 — QUANT SIGNAL ENGINE (市場多空買賣壓)
# -------------------
def get_pressure_signal():
    try:
        r = requests.get(f"{BASE}/exchangeReport/MI_5MINS", headers=HEADERS, timeout=10).json()
        if isinstance(r, list) and len(r) > 0:
            first_row = r[0]
            bid = int(first_row.get("AccBidVolume", 0))
            ask = int(first_row.get("AccAskVolume", 0))
            
            # 💡 工程校正：導入極值分母防護 (max 防 0)，計算出標準化多空 Imbalance 比例
            imbalance_ratio = (bid - ask) / max(bid + ask, 1)
            
            # 定義量化訊號強度
            signal_strength = (
                "🚀 強烈買盤拉抬" if imbalance_ratio > 0.15 
                else "📈 買盤略大於賣盤" if imbalance_ratio > 0.02 
                else "📉 賣壓湧現" if imbalance_ratio < -0.05 
                else "⚪ 買賣力道均衡"
            )
            
            return {
                "status": "成功",
                "bid": bid,
                "ask": ask,
                "pressure": bid - ask,
                "imbalance_ratio": f"{round(imbalance_ratio * 100, 2)}%",
                "signal": signal_strength
            }
    except:
        pass
    return {"status": "失敗", "bid": 0, "ask": 0, "pressure": 0, "imbalance_ratio": "0%", "signal": "無訊號"}


def get_etf():
    all_data = _preload_market_data()
    rows = [x for x in all_data if x.get("Code") == ETF_CODE]
    if not rows:
        return None
    last = rows[-1]
    return {
        "price": float(last.get("ClosingPrice", 0)) if last.get("ClosingPrice") else 0.0,
        "volume": int(last.get("TradeVolume", 0)) if last.get("TradeVolume") else 0
    }


def get_market():
    try:
        r = requests.get(f"{BASE}/exchangeReport/MI_INDEX", headers=HEADERS, timeout=10).json()
        if isinstance(r, list) and len(r) > 0:
            last = r[-1]
            return {
                "index": last.get("收盤指數"),
                "change": last.get("漲跌"),
                "date": last.get("日期")
            }
    except:
        pass
    return {"index": "未公佈", "change": "-", "date": "-"}

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
