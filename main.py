from engine import (
    get_market,
    get_stock,
    get_fundamentals,
    get_news,
    get_etf
)

from config import STOCKS


def render_stock(stock_id):
    s = get_stock(stock_id)
    f = get_fundamentals(stock_id)

    if not s:
        return f"<h2>{stock_id} - no data</h2>"

    return f"""
    <h2>📈 {s['name']} ({stock_id})</h2>
    <ul>
        <li>收盤價: {s['close']}</li>
        <li>漲跌: {s['change']}</li>
        <li>成交量: {s['volume']}</li>
        <li>PE: {f['pe'] if f else '-'}</li>
        <li>殖利率: {f['yield'] if f else '-'}</li>
    </ul>
    """


def render_market():
    m = get_market()

    return f"""
    <h2>📊 整體大盤</h2>
    <ul>
        <li>指數: {m['index']}</li>
        <li>漲跌: {m['change']}</li>
        <li>幅度: {m['pct']}</li>
        <li>日期: {m['date']}</li>
    </ul>
    """


def render_news():
    news = get_news()

    html = "<h2>📢 News</h2><ul>"

    if not news:
        html += "<li>no new events</li>"
    else:
        for n in news:
            html += f"<li>[{n['company']}] {n['title']}</li>"

    html += "</ul>"
    return html


def render_etf():
    e = get_etf()

    if not e:
        return "<h2>ETF error</h2>"

    return f"""
    <h2>📦 ETF 0050</h2>
    <ul>
        <li>價格: {e['price']}</li>
        <li>成交量: {e['volume']}</li>
    </ul>
    """


def main():
    html = "<h1>📈 Financial Engine v1</h1>"

    html += render_market()

    for s in STOCKS:
        html += render_stock(s)

    html += render_etf()
    html += render_news()

    print(html)


if __name__ == "__main__":
    main()