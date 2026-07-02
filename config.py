# config.py

STOCKS = ["2330", "2317", "2454"]  # 多股票
WATCHLIST = set(STOCKS)

BLACKLIST = [
    "代子公司",
    "澄清媒體",
    "取得理財",
    "說明事項",
    "子公司公告",
    "代重要子公司",
    "主管"
]

ALLOW_KEYWORDS = [
    "財務",
    "營收",
    "董事會",
    "盈餘",
    "法說",
    "公告"
]

BLOCK_KEYWORDS = [
    "子公司",
    "澄清",
    "異動說明",
    "代重要子公司"
]
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}