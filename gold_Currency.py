# gold_Currency.py
# ماژول تخصصی بازار طلا و ارز
# شامل ۲ سرویس BrsApi

from config import API_BASE_URL, SECRET_NAME

# ═══════════════════════════════════════════════════════════════
# ۱. تعریف سرویس‌های طلا و ارز
# ═══════════════════════════════════════════════════════════════

API_ENDPOINTS = {
    # ----- طلا و ارز (رایگان) -----
    "gold_currency": {
        "path": "/Market/Gold_Currency.php",
        "params": ["key"],
        "description": "قیمت لحظه‌ای طلا، سکه و ارزهای اصلی (رایگان)"
    },
    # ----- طلا و ارز (حرفه‌ای) -----
    "gold_currency_pro": {
        "path": "/Market/Gold_Currency_Pro.php",
        "params": ["key", "section"],    # section: gold, currency, cryptocurrency
        "description": "قیمت لحظه‌ای طلا و ارز (Pro) با فیلتر و تاریخچه"
    }
}

# ═══════════════════════════════════════════════════════════════
# ۲. نقشه ترجمه فیلدهای خروجی
# ═══════════════════════════════════════════════════════════════

FIELD_MAPS = {
    # --- طلا و ارز (رایگان) ---
    "gold_currency": {
        "name": "نام",
        "price": "قیمت",
        "change_value": "تغییر",
        "change_percent": "درصد تغییر",
        "unit": "واحد"
    },
    # --- طلا و ارز (Pro) ---
    "gold_currency_pro": {
        "name": "نام",
        "price": "قیمت",
        "change_value": "تغییر",
        "change_percent": "درصد تغییر",
        "unit": "واحد",
        "symbol": "نماد",
        "name_en": "نام انگلیسی"
    }
}
