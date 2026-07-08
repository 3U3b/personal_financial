import data_engine
import event_engine
import storage
import render
import datetime

WATCHLIST = [
    "2330",
    "2317",
    "2454"
]
WATCHLIST_SET = set(WATCHLIST)
ETF_CODE = "0050"

def main():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Financial Engine v3</title>
    </head>
    <body>

    <h1>Financial Engine v3</h1>

    """
    
    # market
    m = data_engine.get_market()
    html += f"<h2>大盤</h2><ul><li>{m}</li></ul>"

    # stocks
    history = storage.load_stock_state()
    revenue_map = event_engine.get_monthly_revenue(WATCHLIST_SET)
    for c in WATCHLIST:
        s = data_engine.get_stock(c, history)

        if s:
            s["revenue"] = revenue_map.get(c)
            html += render.render_stock(s)
    storage.save_stock_state(history)
    
    # ETF
    # 假設這是一個 dict {'price': 108.8, 'volume': 73421155}
    etf = data_engine.get_etf(ETF_CODE) or {}
    
    html += f"""
    <h2>ETF 現況</h2>
    <ul>
    <li><b>最新價格：</b>{etf.get('price', '-')} 元</li>
    <li><b>今日成交量：</b>{etf.get('volume', '-')} 股</li>
    </ul>
    """
    
    # flow chart
    try:
        flow = data_engine.get_flow()
    except Exception:
        flow = {
            "status": "失敗",
            "bid": 0,
            "ask": 0,
            "pressure": 0,
            "imbalance_ratio": "0%",
            "market_sentiment": "資料暫停"
        }
    html += render.render_flow(flow)

    # news
    news = event_engine.get_news(WATCHLIST_SET)
    html += render.render_news(news)
    
    # html += render.render_revenue_rader(get_monthly_revenue() LIST)

    html += f"""
    </body>
    <footer>
    更新時間：
    {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </footer>
    </html>
    """
    
    # 4. 寫入實體 HTML 檔案（提供給 GitHub Pages 渲染網頁）
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(" 網頁檔案 index.html 編譯成功！")
        
    event_engine.send_line_messaging_api(flow)

if __name__ == "__main__":
    main()
