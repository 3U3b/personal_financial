import json
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
        print(f"⚠️ 警告：重大訊息 OpenAPI 連線失敗: {e}")
        return []

    state_data = load_state()
    # 確保持久化層級為 Dict 或 Set (相容 v3.1 差分持久化)
    state = set(state_data) if isinstance(state_data, list) else set()
    new_state = set(state)
    result = []

    for x in r:
        # 🟢 規格校正：精確對齊官方手冊中文鍵名
        code = x.get("公司代號", "").strip()

        # 過濾持股清單
        if code not in WATCHLIST:
            continue

        # 🟢 規格校正：精確對齊發言日期與時間
        uid = f"{code}_{x.get('發言日期')}_{x.get('發言時間')}"

        if uid in state:
            continue

        # 🟢 規格校正：手冊上寫著 "主旨 " 後方確實帶有一個半形空格！
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
# 🚀 V3.2 升級模組：每月營收雷達
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
                status = "🔥 營收強勁成長" if float(yoy) > 20.0 else "⚪ 營收持平" if float(yoy) > -5.0 else "📉 營收衰退"
                
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
