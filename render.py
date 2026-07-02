import json

def render_stock(s):
    return f"""
    <h2>📈 {s['name']} ({s['code']})</h2>
    <ul>
        <li>收盤: {s['close']}</li>
        <li>成交量: {s['volume']}</li>
        <li>漲跌: {s['change']}</li>
    </ul>
    """

def render_flow(flow):
    chart = {
        "chartType": "bar",
        "meta": {"title": "Market Flow"},
        "data": [
            {"type": "Bid", "value": flow["bid"]},
            {"type": "Ask", "value": flow["ask"]}
        ]
    }
    return f"<pre>{json.dumps(chart, indent=2)}</pre>"

def render_news(news):
    html = "<h2>📰 News</h2><ul>"
    for n in news:
        html += f"<li>[{n['company']}] {n['text']}</li>"
    html += "</ul>"
    return html