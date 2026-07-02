from data_engine import *

BLACKLIST = ["代子公司", "更正", "公告說明"]

def get_news():
    r = requests.get(BASE + "/opendata/t187ap04_L", headers=HEADERS).json()

    state = load_state()
    new_state = set(state)

    result = []

    for x in r:
        code = x["公司代號"]

        if code not in WATCHLIST:
            continue

        uid = f"{code}_{x['發言日期']}_{x['發言時間']}"

        if uid in state:
            continue

        title = x.get("主旨 ", "")

        if any(b in title for b in BLACKLIST):
            continue

        result.append({
            "company": x["公司名稱"],
            "text": title
        })

        new_state.add(uid)

        if len(result) >= 5:
            break

    save_state(new_state)
    return result