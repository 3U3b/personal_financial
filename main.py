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

if __name__ == "__main__":
    main()
