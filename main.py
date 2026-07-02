from data_engine import *
from event_engine import *
from render import *

WATCH = ["2330", "2317", "2454"]

def main():
    html = "<h1>📈 Financial Engine v3</h1>"

    # market
    m = get_market()
    html += f"<h2>📊 Market</h2><ul><li>{m}</li></ul>"

    # stocks
    for c in WATCH:
        s = get_stock(c)
        if s:
            html += render_stock(s)

    # ETF
    # 💡 在 main.py 中，將 ETF 橫列修改為易讀的排版
    etf = get_etf()  # 假設這是一個 dict {'price': 108.8, 'volume': 73421155}
    html += f"<h2> ETF 現況</h2>"
    html += f"<ul><li><b>最新價格：</b>{etf.get('price', '-')} 元</li>"
    html += f"<li><b>今日成交量：</b>{etf.get('volume', '-')} 股</li></ul>"

    # flow chart
    flow = get_flow()
    html += render_flow(flow)

    # news
    news = get_news()
    html += render_news(news)
    
    rev = get_monthly_revenue()
    html += render_revenue(rev)

    # 4. 寫入實體 HTML 檔案（提供給 GitHub Pages 渲染網頁）
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("🎉 網頁檔案 index.html 編譯成功！")
        
    send_line_messaging_api(flow)


def send_line_messaging_api(flow_data):
    """
    2026 官方標準：LINE Messaging API 主動推播推播模組 (Push Message)
    """
    # 提取 GitHub 保險箱裡的兩把核心資安鑰匙
    channel_access_token = os.environ.get("LINE_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not channel_access_token or not user_id:
        print("⚠️ 提示：未偵測到 LINE_TOKEN 或 LINE_USER_ID，跳過 LINE 官方帳號發信步驟。")
        return
        
    # 組合出最新型態的純文字推播格式
    msg_text = f"🚨【Fin-Engine V3.2 盤中即時監報】\n"
    msg_text += f"🔥大盤多空失衡比：{flow_data.get('imbalance_ratio', '0%')}\n"
    msg_text += f"📊動態力道訊號：{flow_data.get('signal', '暫無訊號')}\n"
    msg_text += f"👉 請即刻查收專屬 GitHub Pages 視覺化看板！"

    # 🟢 2026 正統規格：精確對準 LINE 官方帳號主動推播的 JSON API 端點
    url = "https://line.me"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}"
    }
    
    # 規格校正：符合 LINE 官方規定的 messages array 結構
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": msg_text
            }
        ]
    }
    
    try:
        print("正在發送 2026 Messaging API 企業級推播...")
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            print("🎉 【抵達終點】LINE 官方帳號機器人已成功將日報推送到你的手機！")
        else:
            print(f"❌ LINE 發送失敗，錯誤回應：{res.text}")
    except Exception as e:
        print(f"❌ LINE API 連線發生異常: {e}")


if __name__ == "__main__":
    main()
