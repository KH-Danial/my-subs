import requests
import base64
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor

# منابع استخراج سرور
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/base64/trojan',
    'https://raw.githubusercontent.com/frank-vpl/servers/refs/heads/main/irbox',
    'https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/v2ray/base64'
]

def get_flag(code):
    if not code or code == "??": return "🏳️"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_country_info(address):
    try:
        clean_addr = address.split(':')[0]
        resp = requests.get(f'http://ip-api.com/json/{clean_addr}', timeout=2).json()
        if resp.get('status') == 'success':
            return get_flag(resp.get('countryCode'))
    except: pass
    return "🏳️"

def tcp_ping(address, port):
    """تست زنده بودن و محاسبه پینگ (سقف ۲۰۰ میلی‌ثانیه)"""
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5) # زمان انتظار کوتاه برای فیلتر کردن سرورهای کند
        sock.connect((address, int(port)))
        sock.close()
        return int((time.time() - start_time) * 1000)
    except:
        return None

def process_config(config):
    try:
        # استخراج آدرس و پورت
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: return None
        
        address, port = match.group(1), match.group(2)
        
        # ۱. تست پینگ
        ping = tcp_ping(address, port)
        
        # ۲. فیلتر سخت‌گیرانه (فقط زیر ۲۰۰ میلی‌ثانیه)
        if ping is None or ping > 200:
            return None
            
        # ۳. دریافت پرچم
        flag = get_country_info(address)
        
        # ۴. حذف نام (Remark) قدیمی
        clean_config = config.split('#')[0]
        
        return {
            'config': clean_config,
            'ping': ping,
            'flag': flag
        }
    except:
        return None

def main():
    print("در حال استخراج سرورها...")
    raw_configs = set()
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            content = resp.text.strip()
            try:
                content = base64.b64decode(content).decode('utf-8')
            except: pass
            
            for line in content.splitlines():
                if line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                    raw_configs.add(line.strip())
        except: pass

    print(f"تعداد کل سرورهای خام: {len(raw_configs)}")

    # تست موازی سرورها (۳۰ پردازش همزمان برای سرعت بیشتر)
    final_results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        # بررسی ۲۰۰ سرور اول برای حفظ کیفیت و سرعت گیت‌هاب
        results = list(executor.map(process_config, list(raw_configs)[:200]))
        final_results = [r for r in results if r is not None]

    # ۵. مرتب‌سازی: سریع‌ترین‌ها در ابتدای لیست
    final_results.sort(key=lambda x: x['ping'])

    # ۶. ساخت فایل نهایی با فرمت درخواستی شما
    output_configs = []
    for i, item in enumerate(final_results, 1):
        new_name = f"{item['flag']} redline-crypto - {i}"
        output_configs.append(f"{item['config']}#{new_name}")

    final_text = "\n".join(output_configs)
    encoded_final = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    
    with open('sub_converted.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_final)
    print("عملیات با موفقیت تمام شد. فایل آپدیت شد.")

if __name__ == "__main__":
    main()
