import requests
import json
import os
import sys
import traceback
from datetime import datetime, timezone

# --- تنظیمات ---
API_BASE_URL = "https://api.bitbarg.com/api/v1/docs/prices"
HISTORY_FILE = "price_history.json"
README_FILE = "README.md"
TOP_N = 5

def fetch_all_prices():
    all_items = []
    page = 1
    print(f"🔍 دریافت داده از {API_BASE_URL} (پارامتر base=toman)")

    while True:
        try:
            print(f"📥 صفحه {page}...")
            resp = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "toman"},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "GitHub-Action-Monitor/1.0"
                },
                timeout=30
            )
            print(f"📊 وضعیت: {resp.status_code}")
            resp.raise_for_status()

            # بررسی Content-Type
            ct = resp.headers.get('Content-Type', '')
            if 'application/json' not in ct:
                print(f"⚠️ نوع محتوا: {ct} | {resp.text[:200]}")
                break

            data = resp.json()
            print(f"🔑 کلیدها: {list(data.keys())} | success: {data.get('success')} | msg: {data.get('message')}")

            if not isinstance(data, dict) or not data.get("success"):
                print(f"❌ API خطا: {data.get('message', 'نامشخص')}")
                break

            result = data.get("result", {})
            items = result.get("items", [])
            if not items:
                print("📭 صفحه خالی")
                break

            all_items.extend(items)
            print(f"✅ {len(items)} آیتم (کل: {len(all_items)})")

            # صفحه‌بندی
            meta = result.get("meta", {}).get("paginateHelper", {})
            cur = meta.get("currentPage", page)
            last = meta.get("lastPage", 1)
            print(f"📖 صفحه {cur}/{last}")
            if cur >= last:
                print("🏁 آخرین صفحه")
                break
            page += 1

        except Exception as e:
            print(f"💥 خطا: {e}")
            traceback.print_exc()
            break

    print(f"📦 مجموع: {len(all_items)}")
    return all_items

def load_history():
    if not os.path.exists(HISTORY_FILE):
        print("📂 تاریخچه یافت نشد")
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            h = json.load(f)
        print(f"📚 {len(h)} وضعیت بارگذاری شد")
        return h
    except Exception as e:
        print(f"⚠️ خطای تاریخچه: {e}")
        return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"💾 تاریخچه ذخیره شد")
    except Exception as e:
        print(f"❌ ذخیره تاریخچه: {e}")

def calculate_changes(current, previous):
    changes = {}
    if not current:
        return changes

    # ساخت دیکشنری قیمت‌های قبلی
    prev_dict = {}
    if previous:
        for item in previous:
            slug = item.get("slug")
            # اولویت: quote (تومان)، سپس currency_price (دلار)
            price = item.get("quote") or item.get("currency_price")
            if slug and price is not None:
                prev_dict[slug] = price

    skipped = 0
    for item in current:
        slug = item.get("slug")
        price = item.get("quote") or item.get("currency_price")
        if not slug or price is None:
            skipped += 1
            continue

        prev_price = prev_dict.get(slug)
        if prev_price and prev_price > 0:
            change = ((price - prev_price) / prev_price) * 100
        else:
            change = 0.0

        changes[slug] = {
            "name": slug,
            "current_price": price,
            "previous_price": prev_price,
            "change_percent": round(change, 4)
        }

    if skipped:
        print(f"⚠️ {skipped} آیتم نادیده گرفته شد")
    print(f"✅ تغییرات {len(changes)} ارز محاسبه شد")
    return changes

def generate_files(top_gainers, top_losers, all_changes, timestamp):
    # --- README ---
    if not all_changes:
        readme_body = f"""# 📊 Bitbarg Market Monitor

**🕒 آخرین به‌روزرسانی:** `{timestamp}`

## ⚠️ خطا در دریافت داده
داده‌ای از API دریافت نشد. لطفاً لاگ‌ها را بررسی کنید.
"""
    else:
        sorted_all = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)

        gainers_str = "\n".join(
            f"{i+1}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.0f} تومان)"
            for i, c in enumerate(top_gainers)
        )
        losers_str = "\n".join(
            f"{i+1}. **{c['name']}**: {c['change_percent']:+.2f}% (قیمت: {c['current_price']:,.0f} تومان)"
            for i, c in enumerate(top_losers)
        )

        table_rows = ""
        for i, coin in enumerate(sorted_all[:20], 1):
            emoji = "🟢" if coin["change_percent"] > 0 else ("🔴" if coin["change_percent"] < 0 else "⚪")
            table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.0f} | {coin['change_percent']:+.2f}% {emoji} |\n"

        readme_body = f"""# 📊 Bitbarg Market Monitor (گزارش زنده)

**🕒 آخرین به‌روزرسانی:** `{timestamp}`
**📈 تعداد ارزهای ردیابی‌شده:** `{len(all_changes)}`

---

## 🔥 ۵ ارز با بیشترین رشد (۲۴ ساعته)
{gainers_str}

## ❄️ ۵ ارز با بیشترین افت (۲۴ ساعته)
{losers_str}

---

## 📋 ۲۰ ارز با بیشترین تغییرات
| رتبه | ارز | قیمت (تومان) | تغییر ۲۴ ساعته |
|------|-----|-------------|----------------|
{table_rows}

---
*🤖 این گزارش به‌صورت خودکار هر ۶ ساعت توسط GitHub Actions به‌روزرسانی می‌شود.*
*📡 داده‌ها از API رسمی [Bitbarg](https://bitbarg.com) دریافت می‌شود.*
"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_body)
    print("📄 README ذخیره شد")

    # --- JSON ---
    report = {
        "metadata": {"timestamp": timestamp, "source": "Bitbarg API", "total_coins": len(all_changes)},
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    with open("market_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("📄 JSON ذخیره شد")

def main():
    print("=" * 50)
    print("🚀 شروع تحلیل قیمت‌ها")
    print("=" * 50)

    current_prices = fetch_all_prices()
    if not current_prices:
        print("❌ قیمتی دریافت نشد")
        generate_files([], [], {}, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        sys.exit(1)

    history = load_history()
    previous_prices = history[-1]["items"] if history else []

    all_changes = calculate_changes(current_prices, previous_prices)
    if not all_changes:
        print("❌ تغییری محاسبه نشد")
        sys.exit(1)

    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()

    print("\n📊 نتایج:")
    print(f"🔥 رشدها: {', '.join(f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_gainers)}")
    print(f"❄️ افت‌ها: {', '.join(f'{c[\"name\"]}({c[\"change_percent\"]:+.2f}%)' for c in top_losers)}")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({"timestamp": timestamp, "items": current_prices})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

    generate_files(top_gainers, top_losers, all_changes, timestamp)
    print("\n✅ پایان موفق")

if __name__ == "__main__":
    main()