import requests
import base64
import re

# لیست منابع بروز شده شما
urls = [
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub2.txt',
    'https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/base64/trojan',
    'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_base64_Sub.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/All_Configs_base64_Sub.txt',
    'https://raw.githubusercontent.com/frank-vpl/servers/refs/heads/main/irbox',
    'https://www.v2nodes.com/subscriptions/country/all/?key=E8FF7329C918147'
]

def get_flag(code):
    if not code or code == "??": return "🏳️"
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def decode_if_base64(content):
    try:
        return base64.b64decode(content).decode('utf-8')
    except:
        return content

def main():
    print("شروع فرآیند استخراج...")
    unique_configs = {} # استفاده از دیکشنری برای حذف تکراری بر اساس IP
    
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 3000:
                content = decode_if_base64(resp.text.strip())
                for line in content.splitlines():
                    if line.startswith(('vless://', 'vmess://', 'trojan://', 'ss://')):
                        # استخراج IP و پورت برای شناسایی تکراری‌ها
                        match = re.search(r'@([^:/]+):(\d+)', line)
                        if match:
                            ip_port = f"{match.group(1)}:{match.group(2)}"
                            if ip_port not in unique_configs:
                                # ذخیره لینک خام بدون نام قدیمی
                                clean_link = line.split('#')[0]
                                unique_configs[ip_port] = clean_link
        except: pass

    # برای اینکه کد گیر نکند، در این مرحله فقط ۱۰۰ سرور اول را برای تعیین کشور می‌فرستیم
    # (چون تشخیص کشور هزاران سرور گیت‌هاب را از کار می‌اندازد)
    processed_list = []
    
    # دریافت لیست کشورها به صورت دسته‌جمعی (Batch) برای سرعت
    ips = list(unique_configs.keys())[:3000] # محدود به ۲۰۰ مورد برتر برای پایداری
    
    print(f"در حال تعیین کشور برای {len(ips)} سرور یکتا...")
    
    for ip_port in ips:
        addr = ip_port.split(':')[0]
        try:
            # فقط برای آی‌پی‌های عددی لوکیشن می‌گیریم (سریع‌تر)
            resp = requests.get(f'http://ip-api.com/json/{addr}', timeout=1).json()
            c_code = resp.get('countryCode', '??')
            flag = get_flag(c_code)
        except:
            c_code, flag = '??', '🏳️'
            
        processed_list.append({
            'link': unique_configs[ip_port],
            'country': c_code,
            'flag': flag
        })

    # مرتب‌سازی بر اساس نام کشور
    processed_list.sort(key=lambda x: x['country'])

    # ساخت خروجی نهایی
    output = []
    for i, item in enumerate(processed_list, 1):
        name = f"{item['flag']} redline-crypto - {i}"
        output.append(f"{item['link']}#{name}")

    final_text = "\n".join(output)
    encoded_final = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    
    with open('sub_converted.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_final)
    print("پایان عملیات.")

if __name__ == "__main__":
    main()
