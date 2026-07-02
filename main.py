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
    etf = get_etf()
    html += f"<h2>📦 ETF</h2><ul><li>{etf}</li></ul>"

    # flow chart
    flow = get_flow()
    html += render_flow(flow)

    # news
    news = get_news()
    html += render_news(news)

    print(html)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()