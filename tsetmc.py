# tsetmc.py
# ماژول تخصصی بازار بورس و فرابورس ایران
# این فایل شامل تمامی endpointها، پارامترها و فیلدهای خروجی APIهای مرتبط با بورس تهران است.

API_BASE_URL = "https://Api.BrsApi.ir"

# --- ۱. تعریف سرویس‌ها، پارامترها و ساختار درخواست ---
API_ENDPOINTS = {
    "all_symbols": {
        "path": "/Tsetmc/AllSymbols.php",
        "params": ["key", "type"],
        "description": "اطلاعات لحظه‌ای کلیه نمادهای بورس و فرابورس"
    },
    "index": {
        "path": "/Tsetmc/Index.php",
        "params": ["key", "type"],
        "description": "اطلاعات لحظه‌ای شاخص‌های بورس و فرابورس"
    },
    "symbol_data": {
        "path": "/Tsetmc/Symbol.php",
        "params": ["key", "l18"],
        "description": "دیتای جامع یک نماد (قیمت، معاملات، مجامع)"
    },
    "etf_nav": {
        "path": "/Tsetmc/Nav.php",
        "params": ["key", "l18"],
        "description": "NAV لحظه‌ای صندوق‌های ETF"
    },
    "option_market": {
        "path": "/Tsetmc/Option.php",
        "params": ["key"],
        "description": "دیتای لحظه‌ای بازار اختیار معامله"
    },
    "transaction": {
        "path": "/Tsetmc/Transaction.php",
        "params": ["key", "l18", "date"],
        "description": "ریزمعاملات یک نماد در یک تاریخ خاص"
    },
    "history": {
        "path": "/Tsetmc/History.php",
        "params": ["key", "type", "l18"],
        "description": "دیتای تاریخی معاملات (قیمت، معاملات، حقیقی-حقوقی)"
    },
    "candlestick": {
        "path": "/Tsetmc/Candlestick.php",
        "params": ["key", "type", "l18"],
        "description": "داده‌های کندل‌استیک (شمعی) برای تحلیل تکنیکال"
    },
    "shareholders": {
        "path": "/Tsetmc/Shareholder.php",
        "params": ["key", "l18", "date"],
        "description": "اطلاعات سهامداران عمده یک نماد"
    },
    "codal": {
        "path": "/Codal/Announcement.php",
        "params": ["key", "l18", "category", "date_start", "date_end", "page"],
        "description": "اطلاعیه‌های لحظه‌ای کدال"
    }
}

# --- ۲. دیکشنری ترجمه فیلدهای خروجی (Field Maps) ---
# این بخش به مدل می‌گوید هر پارامتری که از API برمی‌گردد چه معنایی دارد.
FIELD_MAPS = {
    "all_symbols": {
        "l18": "نماد", "l30": "نام", "pl": "آخرین قیمت", "pc": "قیمت پایانی",
        "plc": "تغییر قیمت", "plp": "درصد تغییر", "tno": "تعداد معاملات",
        "tvol": "حجم معاملات", "tval": "ارزش معاملات", "pe": "P/E",
        "eps": "EPS", "mv": "ارزش بازار"
    },
    "index": {
        "name": "نام شاخص", "index": "مقدار", "index_change": "تغییر",
        "index_change_percent": "درصد تغییر", "tvol": "حجم معاملات", "tval": "ارزش معاملات"
    },
    "symbol_data": {
        "l18": "نماد", "l30": "نام", "pl": "آخرین قیمت", "plc": "تغییر قیمت",
        "plp": "درصد تغییر", "tvol": "حجم معاملات", "Buy_CountI": "تعداد خریدار حقیقی",
        "Sell_CountI": "تعداد فروشنده حقیقی", "pe": "P/E", "eps": "EPS", "mv": "ارزش بازار"
    },
    "transaction": {
        "time": "زمان", "volume": "حجم", "price": "قیمت", "canceled": "ابطال شده"
    },
    "candlestick": {
        "date": "تاریخ", "open": "قیمت باز شدن", "high": "بالاترین قیمت",
        "low": "پایین‌ترین قیمت", "close": "قیمت پایانی", "volume": "حجم معاملات"
    },
    "shareholders": {
        "name": "نام سهامدار", "volume": "تعداد سهام", "percent": "درصد مالکیت",
        "change": "تغییر تعداد سهام"
    }
}

# --- ۳. توضیحات تکمیلی پارامترها (اختیاری، برای خوانایی بیشتر) ---
PARAM_DESCRIPTIONS = {
    "key": "کلید API (اختصاصی برای هر سرویس)",
    "l18": "نماد معاملاتی (مثال: فملی، خودرو)",
    "type": "شناسه نوع دیتا (اعداد ۱ تا ۵ بسته به سرویس)",
    "date": "تاریخ به فرمت YYYY-MM-DD",
    "date_start": "تاریخ شروع بازه",
    "date_end": "تاریخ پایان بازه",
    "category": "دسته‌بندی اطلاعیه (۱=صورت مالی، ۲=شفاف‌سازی، ...)",
    "page": "شماره صفحه"
}
