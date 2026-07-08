import json

def render_stock(s):
    return f"""
    <h2> {s['name']} ({s['code']})</h2>
    <ul>
        <li>收盤: {s['close']}</li>
        <li>成交量: {s['volume']}</li>
        <li>漲跌: {s['change']}</li>
        <li>
            營收狀態：
            {s['signals']['momentum'] or '無資料'}
        </li>
    </ul>
    """
    
'''def render_revenue_rader(rev_list):
    color_map = {
        "breakout": "#DC2626",        # 深紅色 / 亮紅 (強勢突破、漲停鎖死)
        "growth": "#EF4444",          # 紅色 (穩定上漲、紅K棒)
        "growth_warning": "#F59E0B",  # 橘黃色 (在上漲但高檔震盪、需注意)
        "growth_flat": "#FBBF24",     # 淡黃色 (漲勢停滯、高檔橫盤)
        "flat": "#6B7280",            # 灰色 (平盤、無漲跌)
        "decline": "#22C55E"          # 綠色 (下跌、綠K棒)
    }
    """
英文版
    color_map = {
        "breakout": "#8B5CF6",        # 亮紫色 (突破、爆發)
        "growth": "#10B981",          # 綠色 (穩定成長)
        "growth_warning": "#FBBF24",  # 黃色 (成長但有警訊)
        "growth_flat": "#F59E0B",     # 橘黃色 (成長趨緩)
        "flat": "#6B7280",            # 灰色 (持平中性)
        "decline": "#EF4444"          # 紅色 (衰退警告)
    }
    """
    if not rev_list:
        return "<h2> Company Revenue</h2><p>本月營收數據尚未公佈或暫無持股資料。</p>"
        
    html = "<h2> 持股營收爆發雷達 (月報)</h2><table border='1' style='border-collapse:collapse; width:100%; text-align:left;'>"
    for r in rev_list:
        color = color_map.get(r["status"], "black")
        html += f"""
        <tr>
            <td>{r['name']} ({r['code']})</td>
            <td>{r['month']}</td>
            <td>{int(r['rev']):,}</td>
            <td>{r['yoy']}</td>
            <td>{r['mom']}</td>
            <td style="color:{color}; font-weight:bold;">{r['signal']}</td>
        </tr>
        """
    
    html += "</table>"
    return html
'''

def render_flow(flow_data):
    """
    將 get_flow() 得到的證交所大盤多空 JSON 數據，
    轉換為 Chart.js 買賣壓比例圖。
    """
    bid_value = flow_data.get("bid", 0)
    ask_value = flow_data.get("ask", 0)
    imbalance = flow_data.get("imbalance_ratio", "0%")
    market_sentiment = flow_data.get("market_sentiment", "無訊號")
    if "買" in market_sentiment:
        sentiment_color="#1E88E543A047"
    elif "賣" in market_sentiment:
        sentiment_color="#43A047"
    else:
        sentiment_color="#FF9800"
        
    pressure = flow_data.get("pressure",0)
    pressure_text = (
        f"+{pressure:,} 張"
        if pressure > 0
        else f"{pressure:,} 張"
    )
    
    if bid_value == 0 and ask_value == 0:
        return f"""
        <div style="background:#ECEFF1;border:1px solid #CFD8DC;
        padding:15px;margin:15px 0;border-radius:5px;width:450px;">
            <h3>當日市場資金流向圖 (Market Flow)</h3>
            <p style="color:#546E7A;font-weight:bold;">
            ☕ 目前為非開盤時間或官方數據尚未更新。
            </p>
        </div>
        """
    # 計算買賣壓比例
    total = bid_value + ask_value
    buy_percent = round((bid_value / total) * 100, 1) if total else 50
    sell_percent = round((ask_value / total) * 100, 1) if total else 50
    

    chart_html = f"""
    <h2>當日市場資金流向圖 (Market Flow)</h2>
    <div style="
        background:#FFF3E0;
        border:1px solid #FFE0B2;
        padding:15px;
        margin:15px 0;
        border-radius:5px;
        width:450px;
    ">
        <ul>
            <li>
                <b>買壓：</b>
                <span style="color:#E53935;font-weight:bold;">
                    {buy_percent}%
                </span>
            </li>
            <li>
                <b>賣壓：</b>
                <span style="color:#1E88E5;font-weight:bold;">
                    {sell_percent}%
                </span>
            </li>
            <li>
                <b>淨買賣壓：</b>
                <span style="font-weight:bold;">
                {pressure_text}
                </span>
            </li>
            <li>
                <b>買賣差：</b>
                <span style="font-weight:bold;">
                    {pressure:,} 張
                </span>
                <b>多空失衡：</b>
                <span style="font-weight:bold;">
                    {imbalance}
                </span>
            </li>
            <li>
                <b>量化動態：</b>
                <span style="
                    background:{sentiment_color};
                    color:white;
                    padding:2px 6px;
                    border-radius:3px;">
                    {market_sentiment}
                </span>
            </li>
        </ul>

        <div style="width:400px;margin:10px auto;">
            <canvas id="marketFlowChart"></canvas>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.min.js"></script>
    <script>
    const ctx = document
        .getElementById('marketFlowChart')
        .getContext('2d');

    new Chart(ctx, {{
        type: "doughnut",
        data: {{
            labels:[
                "買壓",
                "賣壓"
            ],
            datasets:[{{
                data:[
                    {buy_percent},
                    {sell_percent}
                ],
                backgroundColor:[
                    "#E53935",
                    "#1E88E5"
                ],
                borderWidth:2
            }}]
        }},

        options:{{
            responsive:true,
            plugins:{{
                legend:{{
                    position:"bottom"
                }}
            }}
        }}
    }});
    </script>
    """
    return chart_html
    
def render_news(news):
    html = "<h2> News</h2><ul>"
    for n in news:
        html += f"<li>[{n['company']}] {n['text']}</li>"
    html += "</ul>"
    return html