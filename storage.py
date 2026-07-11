import json
from pathlib import Path

try:
    current_dir = Path(__file__).resolve().parent
except NameError:
    current_dir = Path.cwd().resolve()

# STOCK_STATE_FILE = current_dir / "stock_state.json"
NEWS_STATE_FILE = current_dir / "news_state.json"

"""
def load_stock_state():
    if not STOCK_STATE_FILE.exists():
        return {}
    try:
        with open(STOCK_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def save_stock_state(state_dict):
    with open(STOCK_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, ensure_ascii=False, indent=4)
"""

# --- NEWS (透過檔案紀錄達到增量爬蟲) ---
def load_news_state():
    if not NEWS_STATE_FILE.exists():
        return set()

    try:
        with open(NEWS_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return set(data)

        return set()

    except Exception:
        return set()

def save_news_state(state):
    with open(NEWS_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(state)), f, ensure_ascii=False, indent=4)
