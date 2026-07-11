# -*- coding: utf-8 -*-
import requests
import json
import time
from datetime import datetime
from signal_engine import calculate_momentum, calculate_volume_signal

BASE = "https://openapi.twse.com.tw/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 獨立的 TTL 快取儲存庫，避免互相覆蓋
_CACHE = {
    "STOCK_DAY": {"data": None,"ts": 0,"fetch_time": None},
    "BWIBBU": {"data": None,"ts": 0,"fetch_time": None}
}
# 緩衝避免重複呼叫
CACHE_TTL = {
    "STOCK_DAY": 60,
    "BWIBBU": 300,
    "MI_INDEX": 10,
    "MI_5MINS": 5,
}

# -------------------
#  LAYER 1 — DATA LAYER (WITH CACHE TTL)
# -------------------
def _preload_market_data(endpoint, cache_key):
    """通用 TTL 快取網路抓取工具"""
    now = time.time()
    global _CACHE
    if cache_key not in _CACHE:
        _CACHE[cache_key] = {
            "data": None,
            "ts": 0,
            "fetch_time": None
        }
    cache_entry = _CACHE[cache_key]
    
    ttl = CACHE_TTL.get(cache_key,60)
    if (
        cache_entry["data"]
        and now-cache_entry["ts"] < ttl
    ):
        return cache_entry["data"]              # 直接從快取回傳
        
    try:
        url = f"{BASE}{endpoint}"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        cache_entry["data"] = r
        cache_entry["ts"] = now
        cache_entry["fetch_time"] = datetime.now()
    except Exception as e:
        print(f" 預載證交所 {endpoint} 異常: {e}")
        if cache_entry["data"] is None:
            cache_entry["data"] = []
            
    return cache_entry["data"]

# -------------------
#  LAYER 3 — NORMALIZED ENGINE & SIGNAL DETECTION
# -------------------
def get_stock(code):
    """
    一鍵打包：融合『日成交資訊』與『本益比/殖利率/淨值比』的乾淨版函式
    """
    # 1. 同步加載兩份不同的證交所全市場快照
    day_all = _preload_market_data("/exchangeReport/STOCK_DAY_ALL", "STOCK_DAY")
    valuation_all = _preload_market_data("/exchangeReport/BWIBBU_ALL", "BWIBBU")
    
    # 2. 過濾出該代碼的資料列
    day_rows = [x for x in day_all if x.get("Code") == code]
    val_rows = [x for x in valuation_all if x.get("Code") == code]
    
    if not day_rows:
        return None  # 如果連交易資料都沒有，代表代碼可能輸入錯誤
        
    day_data = day_rows[-1]
    day_data.get("Date")
    # 財務估值表可能沒有某些權證或特定 ETF 的資料，給予空字典防呆
    val_data = val_rows[-1] if val_rows else {}

    # 3. 日成交資訊清洗與轉換
    close_str = str(day_data.get("ClosingPrice", "0")).strip().replace(",", "")
    volume_str = str(day_data.get("TradeVolume", "0")).strip().replace(",", "")
    change_str = str(day_data.get("Change", "0.0")).strip().replace(",", "")
    
    close = float(close_str) if close_str and close_str != "維護中" else 0.0
    volume = int(volume_str) if volume_str else 0
    
    try:
        change_val = float(change_str)
    except ValueError:
        change_val = 0.0
        
    prev_close = close - change_val
    price_change_ratio = change_val / prev_close if prev_close > 0 else 0.0
    momentum = calculate_momentum(price_change_ratio)
    
    # 揉合產出最終的資訊字典
    return {
        "type": "stock",
        "code": code,
        "name": day_data.get("Name", "未知名稱"),
        "date": day_data.get("Date", val_data.get("Date", "")),
        "market_data": {
            "close": close,
            "volume": volume,
            "change": change_val,
            "change_ratio_pct": round(price_change_ratio * 100, 2)
        },
        "valuation_data": {
            "pe_ratio": val_data.get("PEratio", "N/A"),          # 本益比
            "yield_pct": val_data.get("DividendYield", "N/A"),   # 殖利率
            "pb_ratio": val_data.get("PBratio", "N/A")           # 股價淨值比
        },
        "signals": {
            "momentum": momentum
        }
    }

# -------------------
#  LAYER 4 — QUANT SIGNAL ENGINE (市場多空買賣壓)
# -------------------
def get_etf(ETF_CODE):
    all_data = _preload_market_data("/exchangeReport/STOCK_DAY_ALL","STOCK_DAY")
    rows = [x for x in all_data if x.get("Code") == ETF_CODE]
    if not rows:
        return None
    last = rows[-1]
    return {
        "price": float(last.get("ClosingPrice", 0)) if last.get("ClosingPrice") else 0.0,
        "volume": int(last.get("TradeVolume", 0)) if last.get("TradeVolume") else 0
    }


def get_market():
    r = _preload_market_data("/exchangeReport/MI_INDEX", "MI_INDEX")
    
    if not r:
        return {"index": "未公佈", "change": "-", "date": "-"}

    last = r[-1]
    return {
        "index": last.get("收盤指數"),
        "change": last.get("漲跌"),
        "date": last.get("日期")
    }
    
# -------------------
# FLOW (BUY/SELL PRESSURE)
# -------------------
def get_flow():
    r = _preload_market_data("/exchangeReport/MI_5MINS", "MI_5MINS")

    if r:
        first_row = r[0]
        bid = int(first_row.get("AccBidVolume", 0))
        ask = int(first_row.get("AccAskVolume", 0))
        
        # 工程校正：導入極值分母防護 (max 防 0)，計算出標準化多空 Imbalance 比例
        imbalance_ratio = (bid - ask) / max(bid + ask, 1)
        
        # 定義量化訊號強度
        signal_strength = calculate_volume_signal(imbalance_ratio)
        
        return {
            "status": "成功",
            "bid": bid,
            "ask": ask,
            "pressure": bid - ask,
            "imbalance_ratio": f"{round(imbalance_ratio * 100, 2)}%",
            "market_sentiment": signal_strength
        }
        
    return {"status": "失敗", "bid": 0, "ask": 0, "pressure": 0, "imbalance_ratio": "0%", "market_sentiment": "無訊號"}

