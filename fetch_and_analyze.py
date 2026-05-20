import requests
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# --- تنظیمات ---
API_BASE_URL = "https://api.bitbarg.com/api/v1/docs/prices"
HISTORY_FILE = "price_history.json"
README_FILE = "README.md"
TOP_N = 5  # تعداد ارزهای برتر

# --- توابع کمکی ---

def fetch_all_prices():
    """
    دریافت قیمت تمام ارزها با مدیریت صفحه‌بندی
    """
    all_items = []
    page = 1
    while True:
        try:
            response = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"}, # دریافت قیمت بر اساس تتر
                headers={"Accept": "application/json"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                print(f"خطا از API: {data.get('message')}")
                break

            items = data["result"]["items"]
            all_items.extend(items)

            # بررسی پایان صفحه‌بندی
            meta = data["result"]["meta"]["paginateHelper"]
            if meta["currentPage"] >= meta["lastPage"]:
                break
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"خطا در دریافت داده‌ها: {e}")
            break

    return all_items

def load_history():
    """خواندن داده‌های تاریخی از فایل"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    """ذخیره‌سازی داده‌های تاریخی"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def calculate_changes(current_prices, previous_prices):
    """محاسبه درصد تغییرات"""
    changes = {}
    prev_dict = {item["slug"]: item["price"] for item in previous_prices}

    for item in current_prices:
        slug = item["slug"]
        current_price = item["price"]
        previous_price = prev_dict.get(slug)

        if previous_price and previous_price > 0:
            change_percent = ((current_price - previous_price) / previous_price) * 100
            changes[slug] = {
                "name": slug,
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": round(change_percent, 4)
            }
        else:
            # برای ارزهایی که سابقه ندارند
            changes[slug] = {
                "name": slug,
                "current_price": current_price,
                "previous_price": None,
                "change_percent": 0.0
            }
    return changes

def generate_readme(top_gainers, top_losers, all_changes, timestamp):
    """تولید فایل README.md جذاب"""
    # مرتب‌سازی کامل تغییرات
    sorted_changes = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)

    # ساخت ردیف‌های جدول برای ۲۰ ارز برتر
    table_rows = ""
    for i, coin in enumerate(sorted_changes[:20], 1):
        emoji = "📈" if coin["change_percent"] > 0 else "📉"
        table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |\n"

    # ساخت بخش برترین‌ها
    gainers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_gainers)])
    losers_list = "\n".join([f"{i+1}. {c['name']}: **%{c['change_percent']:+.2f}**" for i, c in enumerate(top_losers)])

    readme_content = f"""# 📊 Bitbarg Market Monitor (بات نتایج زنده)

**🕒 آخرین به‌روزرسانی:** `{timestamp}`

---

## 🔥 بیشترین رشدها
{gainers_list}

## ❄️ بیشترین افت‌ها
{losers_list}

---

## 📈 جدول برترین تغییرات
| رتبه | ارز | قیمت فعلی | تغییر ۲۴ ساعته |
|------|-----|-----------|----------------|
{table_rows}

---
*🤖 این گزارش به صورت خودکار توسط GitHub Actions تولید و به‌روزرسانی می‌شود.*
"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_content)

def generate_json_report(top_gainers, top_losers, all_changes, timestamp):
    """تولید گزارش JSON کامل"""
    report = {
        "timestamp": timestamp,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    with open("market_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

# --- اجرای اصلی ---
def main():
    print("شروع فرآیند واکشی و تحلیل داده‌ها...")

    # 1. واکشی قیمت‌های فعلی
    print("دریافت قیمت‌های فعلی...")
    current_prices = fetch_all_prices()
    if not current_prices:
        print("هیچ داده‌ای دریافت نشد. عملیات متوقف شد.")
        return
    print(f"تعداد {len(current_prices)} ارز دریافت شد.")

    # 2. بارگذاری تاریخچه
    history = load_history()
    previous_prices = history[-1]["items"] if history else [] # آخرین وضعیت ثبت شده

    # 3. محاسبه تغییرات
    print("محاسبه تغییرات...")
    all_changes = calculate_changes(current_prices, previous_prices)

    # 4. یافتن برترین‌ها
    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N] if sorted_items else []
    top_losers = sorted_items[-TOP_N:] if sorted_items else []
    top_losers.reverse()  # برای نمایش از بیشترین افت به کمترین

    # 5. به‌روزرسانی تاریخچه
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({
        "timestamp": timestamp,
        "items": current_prices
    })

    # محدود کردن تاریخچه به ۱۰۰ وضعیت آخر (برای جلوگیری از رشد حجم فایل)
    if len(history) > 100:
        history = history[-100:]

    save_history(history)

    # 6. تولید گزارش‌ها
    print("تولید گزارش‌ها...")
    generate_readme(top_gainers, top_losers, all_changes, timestamp)
    generate_json_report(top_gainers, top_losers, all_changes, timestamp)

    print("✅ عملیات با موفقیت به پایان رسید!")

if __name__ == "__main__":
    main()