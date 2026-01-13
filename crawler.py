import requests
import json
import os
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ========================
# 配置区
# ========================

URLS = {
    "water": "https://www.wap.cnyiot.com/nat/pay.aspx?mid=50400466780",
    "electric": "https://www.wap.cnyiot.com/nat/pay.aspx?mid=19105155238",
}

DATA_FILE = "data.json"

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.wap.cnyiot.com/",
}

TIMEOUT = 15

# ========================
# 抓取逻辑
# ========================

def init_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(BASE_HEADERS)

    # 种 cookie（关键）
    session.get("https://www.wap.cnyiot.com/", timeout=TIMEOUT)
    session.get("https://www.wap.cnyiot.com/nat/", timeout=TIMEOUT)

    return session


def fetch_balance(session: requests.Session, url: str) -> float:
    resp = session.get(url, timeout=TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    span = soup.find("span", string="剩余金额:")
    if not span:
        raise RuntimeError("未找到 '剩余金额:'")

    label = span.find_parent("div").find("label")
    text = label.get_text(strip=True)

    match = re.search(r"([\d.]+)", text)
    if not match:
        raise RuntimeError(f"无法解析余额: {text}")

    return float(match.group(1))


# ========================
# 数据读写（保持不变）
# ========================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def same_hour(t1, t2):
    return t1[:13] == t2[:13]  # YYYY-MM-DDTHH


# ========================
# 主流程
# ========================

def main():
    try:
        session = init_session()

        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "water": fetch_balance(session, URLS["water"]),
            "electric": fetch_balance(session, URLS["electric"]),
        }

        data = load_data()
        if data and same_hour(data[-1]["time"], record["time"]):
            data[-1] = record
        else:
            data.append(record)

        save_data(data)
        print("✅ New record added:", record)

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
