import json
from dotenv import load_dotenv
import os

# 加載測試環境配置
load_dotenv(dotenv_path='.env.testing')

import sys
import datetime
import requests
from data_engine import BASE, HEADERS, WATCHLIST, load_state, save_state

BLACKLIST = ["代子公司", "更正", "公告說明", "澄清媒體"]

def get_news():
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

    state_data = load_state()
    # 確保持久化層級為 Dict 或 Set (相容 v3.1 差分持久化)
    state = set(state_data) if isinstance(state_data, list) else set()
    new_state = set(state)
    result = []

    for x in r:
        # 規格校正：精確對齊官方手冊中文鍵名
        code = x.get("公司代號", "").strip()

        # 過濾持股清單
        if code not in WATCHLIST:
            continue

        # 規格校正：精確對齊發言日期與時間
        uid = f"{code}_{x.get('發言日期')}_{x.get('發言時間')}"

        if uid in state:
            continue

        # 規格校正：手冊上寫著 "主旨 " 後方確實帶有一個半形空格！
        title = x.get("主旨 ", "").strip()

        if any(b in title for b in BLACKLIST):
            continue

        result.append({
            "company": x.get("公司名稱", "未知公司").strip(),
            "text": title
        })

        new_state.add(uid)

    save_state(list(new_state))
    return result[:5]


# -------------------
# 每月營收雷達
# -------------------
def get_monthly_revenue():
    """
    依據手冊新增：/opendata/t187ap05_P 公發公司每月營收彙總
    自動監控持股是否有「最新營收爆發」的重磅信號！
    """
    url = f"{BASE}/opendata/t187ap05_P"
    revenue_signals = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        for x in r:
            code = x.get("公司代號", "").strip()
            if code in WATCHLIST:
                yoy = x.get("營業收入-去年同月增減(%)", "0")
                mom = x.get("營業收入-上月比較增減(%)", "0")
                
                # 判定營收爆發訊號 (年增率大於 20% 為成長股特徵)
                if float(yoy) > 20:
                    status = "growth"
                    signal = "營收強勁成長"
                elif float(yoy) > -5:
                    status = "flat"
                    signal = "營收持平"
                else:
                    status = "decline"
                    signal = "營收衰退"
                
                revenue_signals.append({
                    "code": code,
                    "name": x.get("公司名稱", "").strip(),
                    "month": x.get("資料年月", ""),
                    "rev": x.get("營業收入-當月營收", ""),
                    "yoy": f"{yoy}%",
                    "mom": f"{mom}%",
                    "signal": status
                })
    except:
        pass
    return revenue_signals



# -------------------
# 2026 官方標準：LINE Messaging API 主動推播模組 (Push Message)，對齊官方 cURL 規格
# -------------------
def send_line_messaging_api(flow_data):
    channel_access_token = os.environ.get("LINE_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not channel_access_token or not user_id:
        print(" 提示：未偵測到 LINE_TOKEN 或 LINE_USER_ID，跳過 LINE 官方帳號發信步驟。")
        return

    # 訊息一：大盤動態力道 (獨立框)
    msg_market = f"【大盤資金流向監報】\n"
    msg_market += f" 多空失衡比：{flow_data.get('imbalance_ratio', '0%')}\n"
    msg_market += f" 量化動態指標：{flow_data.get('signal', '暫無訊號')}"

    # 訊息二：即時動作指引 (獨立框)
    msg_action = f"【Fin-Engine 動能突破提示】\n"
    msg_action += f"持股價量差分追蹤、最新中文重大訊息與每月營收爆發雷達已全部編譯完成！\n"
    msg_action += f" 請即刻查收專屬網頁看板！"

    # 2026 官方正統規格：精確對齊 api.line.me 的 JSON 請求矩陣
    url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}"
    }
    
    # 依據官方文件範例：將兩個訊息物件同時塞進 messages 清單中，手機會收到兩封分開的漂亮對話框！
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": msg_market
            },
            {
                "type": "text",
                "text": msg_action
            }
        ]
    }

    try:
        print("正在發送 2026 Messaging API 企業級推播...")
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            print(" 【抵達終點】LINE 官方帳號機器人已成功將日報推送到你的手機！")
        else:
            print(f" LINE 發送失敗，錯誤回應：{res.text}")
    except Exception as e:
        print(f" LINE API 連線發生異常: {e}")
