import requests
import json
import os
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ========================
# 配置区（你只需要看这里）
# ========================

URLS = {
    "water": "https://www.wap.cnyiot.com/nat/pay.aspx?mid=50400466780",
    "electric": "https://www.wap.cnyiot.com/nat/pay.aspx?mid=19105155238",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GitHub Actions)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.wap.cnyiot.com/",
}

DATA_FILE = "data.json"

# ========================
# 你只需要实现这个函数
# ========================

def fetch_balance(url: str) -> float:
    session = requests.Session()
    session.headers.update(HEADERS)

    # 先访问首页，建立 cookie
    session.get("https://www.wap.cnyiot.com/", timeout=15)

    resp = session.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    span = soup.find("span", string="剩余金额:")
    if not span:
        raise RuntimeError("未找到 '剩余金额:'")

    parent = span.find_parent("div")
    if not parent:
        raise RuntimeError("未找到父级 div")

    label = parent.find("label")
    if not label:
        raise RuntimeError("未找到余额 label")

    text = label.get_text(strip=True)

    match = re.search(r"([\d.]+)", text)
    if not match:
        raise RuntimeError(f"无法解析余额: {text}")

    return float(match.group(1))

# ========================
# 下面是通用逻辑，不要改
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

def main():
    try:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "water": fetch_balance(URLS["water"]),
            "electric": fetch_balance(URLS["electric"]),
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
