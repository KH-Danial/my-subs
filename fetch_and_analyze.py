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

# --- توابع کمکی (با مدیریت خطای جامع) ---

def fetch_all_prices():
    """
    دریافت تمام قیمت‌ها با حلقه while و خروج امن در صورت خطا
    """
    all_items = []
    page = 1
    last_page = 1

    while True:
        try:
            print(f"📥 درخواست صفحه {page}...")
            resp = requests.get(
                API_BASE_URL,
                params={"pageSize": 100, "page": page, "base": "usdt"},
                headers={"Accept": "application/json"},
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()

            # لاگ کردن کلیدهای اصلی پاسخ برای دیباگ
            print(f"🔑 کلیدهای پاسخ: {list(data.keys())}")

            if not isinstance(data, dict) or not data.get("success"):
                print(f"⚠️ API خطا داد: {data.get('message', 'پاسخ نامعتبر')}")
                break

            result = data.get("result", {})
            items = result.get("items", [])
            if not items:
                print("📭 آیتمی در این صفحه نیست.")
                break

            all_items.extend(items)
            print(f"✅ {len(items)} آیتم از صفحه {page} دریافت شد (کل: {len(all_items)})")

            # به‌روزرسانی اطلاعات صفحه‌بندی
            meta = result.get("meta", {}).get("paginateHelper", {})
            current_page = meta.get("currentPage", page)
            last_page = meta.get("lastPage", 1)

            if current_page >= last_page:
                print(f"🏁 به صفحه آخر رسیدیم ({current_page}/{last_page})")
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"❌ خطای شبکه/درخواست: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"❌ پاسخ API یک JSON معتبر نبود: {e}")
            break
        except Exception as e:
            print(f"❌ خطای پیش‌بینی‌نشده: {e}")
            traceback.print_exc()
            break

    return all_items

def load_history():
    """بارگذاری امن تاریخچه"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ ناتوانی در خواندن تاریخچه: {e}")
        return []

def save_history(history):
    """ذخیره تاریخچه با مدیریت خطا"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"💾 تاریخچه ذخیره شد ({len(history)} وضعیت)")
    except Exception as e:
        print(f"❌ خطا در ذخیره تاریخچه: {e}")

def calculate_changes(current, previous):
    """محاسبه درصد تغییرات با کلیدهای امن"""
    changes = {}
    if not current:
        return changes

    prev_dict = {}
    if previous:
        prev_dict = {item.get("slug"): item.get("price") for item in previous if item.get("slug")}

    for item in current:
        slug = item.get("slug")
        price = item.get("price")
        if not slug or price is None:
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
    return changes

def generate_files(top_gainers, top_losers, all_changes, timestamp):
    """تولید همزمان README و JSON با تضمین نوشتن فایل"""

    # --- ساخت README حداقلی حتی در صورت نبود داده ---
    if not all_changes:
        readme_body = f"""# 📊 Bitbarg Market Monitor

**🕒 آخرین به‌روزرسانی:** `{timestamp}`
**⚠️ خطا: هیچ داده قیمتی برای تحلیل دریافت نشد.**
"""
    else:
        sorted_all = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
        gainers_str = "\n".join([f"{i+1}. {c['name']}: **{c['change_percent']:+.2f}%**" for i, c in enumerate(top_gainers)])
        losers_str = "\n".join([f"{i+1}. {c['name']}: **{c['change_percent']:+.2f}%**" for i, c in enumerate(top_losers)])

        table_rows = ""
        for i, coin in enumerate(sorted_all[:20], 1):
            if coin["change_percent"] != 0:
                emoji = "📈" if coin["change_percent"] > 0 else "📉"
                table_rows += f"| {i} | {coin['name']} | {coin['current_price']:,.2f} | {coin['change_percent']:+.2f}% {emoji} |\n"

        readme_body = f"""# 📊 Bitbarg Market Monitor

**🕒 آخرین به‌روزرسانی:** `{timestamp}`

## 🔥 بیشترین رشدها
{gainers_str}

## ❄️ بیشترین افت‌ها
{losers_str}

## 📈 جدول برترین تغییرات
| رتبه | ارز | قیمت فعلی | تغییر ۲۴ ساعته |
|------|-----|-----------|----------------|
{table_rows if table_rows else '| - | - | - | - |'}

---
*🤖 گزارش خودکار توسط GitHub Actions*
"""

    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(readme_body)
        print(f"📄 {README_FILE} به‌روزرسانی شد.")
    except Exception as e:
        print(f"❌ نوشتن README ناموفق: {e}")

    # --- ساخت گزارش JSON ---
    report = {
        "timestamp": timestamp,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "all_changes": all_changes
    }
    try:
        with open("market_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("📄 market_report.json به‌روزرسانی شد.")
    except Exception as e:
        print(f"❌ نوشتن JSON ناموفق: {e}")

# --- خط اصلی اجرا ---
def main():
    print("🚀 شروع فرآیند واکشی...")
    current_prices = fetch_all_prices()

    if not current_prices:
        print("❌ قیمتی دریافت نشد. یک README خطا تولید می‌شود.")
        generate_files([], [], {}, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        sys.exit(1)  # خروج با خطا تا workflow متوجه شود

    print(f"✅ مجموع ارزهای دریافت‌شده: {len(current_prices)}")

    history = load_history()
    previous_prices = history[-1]["items"] if history else []

    all_changes = calculate_changes(current_prices, previous_prices)
    if not all_changes:
        print("❌ هیچ تغییری محاسبه نشد.")
        sys.exit(1)

    sorted_items = sorted(all_changes.values(), key=lambda x: x["change_percent"], reverse=True)
    top_gainers = sorted_items[:TOP_N]
    top_losers = sorted_items[-TOP_N:]
    top_losers.reverse()

    # به‌روزرسانی تاریخچه
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history.append({"timestamp": timestamp, "items": current_prices})
    if len(history) > 100:
        history = history[-100:]
    save_history(history)

    generate_files(top_gainers, top_losers, all_changes, timestamp)
    print("🎉 عملیات با موفقیت به پایان رسید.")

if __name__ == "__main__":
    main()