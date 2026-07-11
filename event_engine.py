import json
from dotenv import load_dotenv
import os

# 加載測試環境配置
load_dotenv(dotenv_path='.env.testing')

import requests
from data_engine import BASE, HEADERS
from storage import load_news_state, save_news_state

BLACKLIST = ["代子公司", "更正", "公告說明", "異動", "聘任", "改選", "澄清媒體"]

def safe_float(v):
    try:
        return float(str(v).replace(",", ""))
    except:
        return 0
        
# -------------------
# -------------------

def get_news(WATCHLIST_SET):
    """
    上市公司每日重大訊息 (OpenAPI 規格校正版)
    依據官方 Swagger 手冊：此端點欄位為『純中文』
    """
    url = f"{BASE}/opendata/t187ap04_L"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f" 警告：重大訊息 OpenAPI 連線失敗: {e}")
        return []

    state = load_news_state()
    new_state = set(state)
    result = []

    for x in r:
        # 規格校正：精確對齊官方手冊中文鍵名
        code = x.get("公司代號", "").strip()
        # 過濾持股清單
        if code not in WATCHLIST_SET:
            continue
            
        # 規格校正：API 手冊上寫著 "主旨 "，後方確實帶有一個半形空格！(傻眼)
        title = x.get("主旨 ", "").strip() + ("..." if len(x.get("主旨 ", "").strip()) > 9  else "")
        if any(b in title for b in BLACKLIST):
            continue

        # 規格校正：精確對齊發言日期與時間
        uid = f"{code}_{x.get('發言日期')}_{x.get('發言時間')}_{title}"
        if uid in state:
            continue

        new_state.add(uid)
        result.append({
            "company": x.get("公司名稱", "未知公司").strip(),
            "text": title
        })

    save_news_state(new_state)
    return result[:5]


# -------------------
# 每月營收雷達
# -------------------
def get_monthly_revenue(WATCHLIST_SET):
    """
    依據手冊新增：/opendata/t187ap05_P 公發公司每月營收彙總
    自動監控持股是否有「最新營收爆發」的重磅信號！
    """
    url = f"{BASE}/opendata/t187ap05_P"
    revenue_signals = {}
    
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        
        print(len(r))
        print(r[0])
        found = []

        for x in r:
            code = x.get("公司代號", "").strip()
            if code not in WATCHLIST_SET:
                continue
            
            if code in WATCHLIST_SET:
                found.append(code)
                
            yoy = safe_float(
                x.get("營業收入-去年同月增減(%)", 0)
            )

            mom = safe_float(
                x.get("營業收入-上月比較增減(%)", 0)
            )
            if abs(yoy) < 0.01:
                yoy = 0
            if abs(mom) < 0.01:
                mom = 0
                
            # 判定營收爆發訊號 (年增率大於 20% 為成長股特徵)
            if yoy > 50 and mom > 10:
                status = "revenue_surge"
                signal = "營收爆發"
            elif yoy > 20:
                if mom > 0:
                    status = "growth"
                    signal = "營收成長加速"
                elif mom < 0:
                    status = "growth_warning"
                    signal = "營收成長但動能降溫"
                else:
                    status = "growth_flat"
                    signal = "營收成長但月變化持平"
            elif yoy < 0 and mom < 0:
                status = "decline"
                signal = "營收衰退"
            else:
                status = "flat"
                signal = "營收持平"
                
            revenue_signals[code] = {
                "code": code,
                "name": x.get("公司名稱", "").strip(),
                "month": x.get("資料年月", ""),
                "rev": x.get("營業收入-當月營收", ""),
                "yoy": f"{yoy}%",
                "mom": f"{mom}%",
                "status": status,
                "signal": signal
            }
            
            print("營收找到持股:", found)

    except Exception as e:
        print(
            f"營收資料取得失敗: {e}"
        )
    return revenue_signals


# -------------------
# 2026 官方標準：LINE Messaging API 主動推播模組 (Push Message)，對齊官方 cURL 規格
# -------------------
def send_line_messaging_api(flow_data):
    channel_access_token = os.environ.get("LINE_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    web_url = os.environ.get("WEB_URL")
    
    if not channel_access_token or not user_id:
        print(" 提示：未偵測到 LINE_TOKEN 或 LINE_USER_ID，跳過 LINE 官方帳號發信步驟。")
        return

    # 訊息一：大盤動態力道 (獨立框)
    msg_market = f"【大盤資金流向監報】\n"
    msg_market += f" 多空失衡比：{flow_data.get('imbalance_ratio', '0%')}\n"
    msg_market += f" 量化動態指標：{flow_data.get('market_sentiment', '暫無訊號')}\n"
    msg_market += f" 請即刻查收專屬網頁看板！\n {web_url}"
    
    # 訊息二：即時動作指引 (獨立框)
    # msg_action = f"【Fin-Engine 動能突破提示】\n"
    # msg_action += f"持股價量差分追蹤、最新中文重大訊息與每月營收爆發雷達已全部編譯完成！\n"

    # 2026 官方正統規格：精確對齊 api.line.me 的 JSON 請求矩陣
    url = "https://api.line.me/v2/bot/message/push"
    
    LINE_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}"
    }
    
    # 依據官方文件範例，可將兩個訊息物件同時塞進 messages 清單中，手機會收到兩封分開的對話框
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": msg_market
            }
        ]
    }

    try:
        print("正在發送 LINE 訊息...")
        res = requests.post(url, headers=LINE_headers, json=payload, timeout=10)
        if res.status_code == 200:
            print(" 【抵達終點】 已成功將日報發送到 LINE！")
        else:
            print(f" LINE 發送失敗，錯誤回應：{res.text}")
    except Exception as e:
        print(f" LINE API 連線發生異常: {e}")
