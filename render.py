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

def render_revenue(rev_list):
    if not rev_list:
        return "<h2>🧱 Company Revenue</h2><p>本月營收數據尚未公佈或暫無持股資料。</p>"
        
    html = "<h2>🧱 持股營收爆發雷達 (月報)</h2><table border='1' style='border-collapse:collapse; width:100%; text-align:left;'>"
    html += "<tr style='background:#E0F2F1;'><th>公司</th><th>資料月份</th><th>當月營收 (千元)</th><th>年增率 (YoY)</th><th>月增率 (MoM)</th><th>營收狀態</th></tr>"
    for r in rev_list:
        color = "red" if "🔥" in r['signal'] else "blue" if "📉" in r['signal'] else "black"
        html += f"<tr><td>{r['name']} ({r['code']})</td><td>{r['month']}</td><td>{int(r['rev']):,}</td><td>{r['yoy']}</td><td>{r['mom']}</td><td style='color:{color}; font-weight:bold;'>{r['signal']}</td></tr>"
    html += "</table>"
    return html


def render_flow(flow_data):
    """
    將 get_flow() 得到的證交所大盤多空 JSON 數據，完美轉換為網頁上的 HTML5 彩色動態長條圖！
    """
    bid_value = flow_data.get("bid", 0)
    ask_value = flow_data.get("ask", 0)
    imbalance = flow_data.get("imbalance_ratio", "0%")
    signal = flow_data.get("signal", "無訊號")

    # 🟢 核心工程優化：萬一清晨或假日尚未開盤 (買賣量皆為 0)，自動吐出高質感的盤前降級提示
    if bid_value == 0 and ask_value == 0:
        return f"""
        <div style="background: #ECEFF1; border: 1px solid #CFD8DC; padding: 15px; margin: 15px 0; border-radius: 5px; width: 450px;">
            <h3>📊 當日市場資金流向圖 (Market Flow)</h3>
            <p style="color:#546E7A; font-weight:bold; margin: 10px 0;">☕ 目前為非開盤時間或官方數據已初始化。</p>
            <p style="color:#78909C; font-size:13px;">系統將於每週一至週五 <b>09:00 開盤後</b> 自動捕捉每5秒動態多空買賣壓。</p>
        </div>
        """

    # 正常開盤時間的 Chart.js 渲染 HTML (精確對齊 cdn.jsdelivr 網址)
    chart_html = f"""
    <h2>📊 當日市場資金流向圖 (Market Flow)</h2>
    <div style="background: #FFF3E0; border: 1px solid #FFE0B2; padding: 15px; margin: 15px 0; border-radius: 5px; width: 450px;">
        <ul>
            <li><b>多空量能失衡比：</b><span style="color:red; font-weight:bold;">{imbalance}</span></li>
            <li><b>量化動態指標：</b><span style="background:#FF9800; color:white; padding:2px 6px; border-radius:3px;">{signal}</span></li>
        </ul>
        <div style="width: 400px; margin: 10px 0;">
            <canvas id="marketFlowChart"></canvas>
        </div>
    </div>
    
    <script src="https://jsdelivr.net"></script>
    <script>
        const ctx = document.getElementById('marketFlowChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['買進 (Bid)', '賣出 (Ask)'],
                datasets: [{{
                    label: '大盤累積資金流量 (張)',
                    data: [{bid_value}, {ask_value}],
                    backgroundColor: ['rgba(255, 99, 132, 0.7)', 'rgba(54, 162, 235, 0.7)'],
                    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});
    </script>
    """
    return chart_html



def render_news(news):
    html = "<h2>📰 News</h2><ul>"
    for n in news:
        html += f"<li>[{n['company']}] {n['text']}</li>"
    html += "</ul>"
    return html