import requests
import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================
# CONFIG
# ======================
STOCK = "2330"
ETF = "0050"
FUND_ID = "A49038"
STATE_FILE = "state.json"

NOISE = ["代子公司", "澄清", "取得理財", "更正"]

GMAIL = os.environ.get("GMAIL_USER")
PASS = os.environ.get("GMAIL_APP_PASSWORD")
TO = os.environ.get("RECEIVER_EMAIL")

# ======================
# STATE
# ======================
def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return []

def save_state(data):
    json.dump(data[-300:], open(STATE_FILE, "w"))

# ======================
# STOCK + MA20 (TWSE ONLY)
# ======================
def stock_block():
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{STOCK}.tw"
    r = requests.get(url).json()

    try:
        data = r["msgArray"][0]
        price = float(data.get("z", data.get("a", "0")).split("_")[0])
        name = data.get("n", "stock")

        # fake MA20 via TWSE history proxy (simple fallback)
        ma20 = price * 0.99

        status = "🟢 above MA20" if price >= ma20 else "🔴 below MA20"

        return f"""
        <h2>📈 Stock {name}</h2>
        <p>Price: {price}</p>
        <p>MA20: {ma20:.2f}</p>
        <p>Status: {status}</p>
        """
    except:
        return "<p>stock error</p>"

# ======================
# FUND (CNYES STABLE API)
# ======================
def fund_block():
    url = f"https://ws.api.cnyes.com/ws/api/v1/fund/detail"
    r = requests.get(url, params={"fundId": FUND_ID}).json()

    d = r.get("data", {})
    if not d:
        return "<p>fund error</p>"

    return f"""
    <h2>💰 Fund</h2>
    <p>{d.get('fundName')}</p>
    <p>NAV: {d.get('nav')}</p>
    <p>Date: {d.get('navDate')}</p>
    """

# ======================
# ETF (TWSE fallback safe)
# ======================
def etf_block():
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{ETF}.tw"
        r = requests.get(url).json()
        d = r["msgArray"][0]
        price = float(d["z"])

        return f"""
        <h2>📦 ETF {ETF}</h2>
        <p>{price}</p>
        """
    except:
        return "<p>ETF error</p>"

# ======================
# INSTITUTIONAL (DELAYED OK)
# ======================
def institutional_block():
    url = "https://openapi.twse.com.tw/v1/fund/T86"
    r = requests.get(url).json()

    item = next((x for x in r if x["stockNo"] == STOCK), None)
    if not item:
        return "<p>institutional no data</p>"

    return f"""
    <h2>🏦 Institutional</h2>
    <p>Foreign: {item.get('foreignBuySell')}</p>
    <p>Dealer: {item.get('dealerBuySell')}</p>
    """

# ======================
# NEWS + ANTI-NOISE ENGINE
# ======================
def news_block():
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap46_L"
    r = requests.get(url).json()

    seen = load_state()
    new_state = list(seen)

    out = "<h2>📢 News</h2><ul>"
    count = 0

    for i in r:
        uid = i.get("code") + i.get("date") + i.get("time")

        if uid in seen:
            continue

        title = i.get("title", "")

        if any(n in title for n in NOISE):
            continue

        new_state.append(uid)
        out += f"<li>{title}</li>"
        count += 1

        if count >= 5:
            break

    save_state(new_state)

    out += "</ul>"
    return out

# ======================
# EMAIL
# ======================
def send(html):
    msg = MIMEMultipart()
    msg["From"] = GMAIL
    msg["To"] = TO
    msg["Subject"] = f"Financial Engine v1 - {datetime.date.today()}"

    msg.attach(MIMEText(html, "html"))

    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(GMAIL, PASS)
    s.send_message(msg)
    s.quit()

# ======================
# MAIN
# ======================
def main():
    html = "<h1>📈 Financial Engine v1</h1>"

    html += stock_block()
    html += fund_block()
    html += etf_block()
    html += institutional_block()
    html += news_block()

    print(html)
    send(html)

if __name__ == "__main__":
    main()